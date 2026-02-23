# Created: 2026-02-19
"""
Kerne Neural Net GPU Trainer
============================
Local GPU training with real-time usage display and dynamic throttling.
Keeps GPU utilization below a configurable ceiling (default 75%) so
other processes can share the GPU without starvation.
"""

import os
import sys
import time
import threading
from pathlib import Path
from datetime import datetime, timedelta

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

import numpy as np
import pandas as pd
import requests
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from tqdm import tqdm

from src.yield_predictor import YieldTransformer, YieldLoss

# Suppress pandas warnings
pd.set_option('future.no_silent_downcasting', True)

HORIZONS = ["1h", "24h", "7d", "30d"]


def _get_gpu_utilization() -> float:
    """Query current GPU utilization % via nvidia-smi. Returns -1 on failure."""
    try:
        import subprocess
        result = subprocess.run(
            ['nvidia-smi', '--query-gpu=utilization.gpu', '--format=csv,noheader,nounits'],
            capture_output=True, text=True, timeout=2
        )
        if result.returncode == 0:
            return float(result.stdout.strip())
    except Exception:
        pass
    return -1.0


class GPUThrottler:
    """
    Dynamically adjusts sleep delay between training batches to keep
    GPU utilization below `max_util_pct`.

    Algorithm:
      - If current_util > max_util:      increase sleep by STEP_UP   ms (slow down)
      - If current_util < max_util - 10: decrease sleep by STEP_DOWN ms (speed up)
      - Sleep is clamped between MIN_SLEEP and MAX_SLEEP seconds
    """
    MIN_SLEEP   = 0.0    # seconds
    MAX_SLEEP   = 2.0    # seconds
    STEP_UP     = 0.04   # +40 ms when over limit
    STEP_DOWN   = 0.01   # -10 ms when well under limit

    def __init__(self, max_util_pct: float = 75.0):
        self.max_util_pct = max_util_pct
        self._sleep = 0.0            # current inter-batch sleep
        self._last_util = 0.0       # last sampled utilization

    def update(self, current_util: float):
        """Update the throttler with the latest GPU utilization reading."""
        if current_util < 0:         # nvidia-smi failed – do nothing
            return
        self._last_util = current_util
        if current_util > self.max_util_pct:
            self._sleep = min(self._sleep + self.STEP_UP, self.MAX_SLEEP)
        elif current_util < self.max_util_pct - 10:
            self._sleep = max(self._sleep - self.STEP_DOWN, self.MIN_SLEEP)

    def wait(self):
        """Sleep for the current throttle duration."""
        if self._sleep > 0:
            time.sleep(self._sleep)

    @property
    def sleep_ms(self) -> float:
        return self._sleep * 1000


class GPUTrainer:
    """GPU trainer with real-time usage display and adaptive throttling."""
    
    def __init__(self, max_gpu_util: float = 75.0):
        self.max_gpu_util = max_gpu_util
        self.device = self._check_gpu()
        self.model = None
        self.normalization_params = None
        self.training_stats = {
            "epochs": 0,
            "total_samples": 0,
            "best_val_loss": float("inf"),
            "current_epoch": 0,
            "epoch_loss": 0,
            "start_time": None,
            "gpu_memory_used": 0,
            "gpu_memory_total": 0,
            "gpu_utilization": 0,
            "throttle_sleep_ms": 0,
        }
        self.stop_flag = False
        self._throttler = GPUThrottler(max_util_pct=max_gpu_util)
        
    def _check_gpu(self) -> torch.device:
        """Check for GPU and return device."""
        print("\n" + "=" * 60)
        print("  KERNE NEURAL NET - GPU TRAINER")
        print("=" * 60)
        
        if torch.cuda.is_available():
            device = torch.device("cuda")
            gpu_name = torch.cuda.get_device_name(0)
            gpu_memory = torch.cuda.get_device_properties(0).total_memory / 1e9
            print(f"\n  [OK] GPU Detected: {gpu_name}")
            print(f"  [OK] GPU Memory: {gpu_memory:.1f} GB")
            print(f"  [OK] CUDA Version: {torch.version.cuda}")
            print(f"  [OK] GPU Utilization Cap: {self.max_gpu_util:.0f}%")
            return device
        else:
            print("\n  [WARNING] No GPU detected - using CPU (slower)")
            return torch.device("cpu")
    
    def _update_gpu_stats(self):
        """Update GPU statistics + throttler in background thread (every 500 ms)."""
        while not self.stop_flag:
            if self.device.type == "cuda":
                try:
                    self.training_stats["gpu_memory_used"] = (
                        torch.cuda.memory_allocated(0) / 1e9
                    )
                    self.training_stats["gpu_memory_total"] = (
                        torch.cuda.get_device_properties(0).total_memory / 1e9
                    )
                    util = _get_gpu_utilization()
                    if util >= 0:
                        self.training_stats["gpu_utilization"] = util
                        # Feed the throttler with the latest reading
                        self._throttler.update(util)
                        self.training_stats["throttle_sleep_ms"] = self._throttler.sleep_ms
                except Exception:
                    pass
            time.sleep(0.5)
    
    def fetch_data(self) -> list:
        """Fetch training data from DeFiLlama."""
        print("\n" + "-" * 60)
        print("  FETCHING DATA FROM DEFILLAMA")
        print("-" * 60)
        
        # Fetch pools
        print("  [1/3] Fetching pool list...")
        url = "https://yields.llama.fi/pools"
        response = requests.get(url, timeout=30)
        data = response.json()
        pools = data.get("data", [])
        df = pd.DataFrame(pools)
        
        # Filter stablecoin pools
        stablecoin_pools = df[
            (df.get("stablecoin", False) == True) & 
            (df["tvlUsd"] > 1e6)
        ].nlargest(50, "tvlUsd")
        
        print(f"  [OK] Found {len(stablecoin_pools)} stablecoin pools")
        
        # Fetch historical data
        print("  [2/3] Fetching historical data (this may take a minute)...")
        pool_data = {}
        
        for idx, row in tqdm(stablecoin_pools.iterrows(), total=len(stablecoin_pools), desc="  Downloading"):
            pool_id = row.get("pool", "")
            try:
                url = f"https://yields.llama.fi/chart/{pool_id}"
                resp = requests.get(url, timeout=30)
                if resp.status_code == 200:
                    points = resp.json().get("data", [])
                    if points:
                        hist_df = pd.DataFrame(points)
                        hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"])
                        hist_df["pool_id"] = pool_id
                        pool_data[pool_id] = hist_df
                time.sleep(0.3)  # Rate limit
            except Exception as e:
                continue
        
        print(f"  [OK] Downloaded data for {len(pool_data)} pools")
        
        # Prepare sequences
        print("  [3/3] Preparing training sequences...")
        sequences = []
        
        for pool_id, df in pool_data.items():
            if df is None or len(df) < 200:
                continue
            
            # Create features
            df["apy_ma7"] = df["apy"].rolling(7, min_periods=1).mean()
            df["apy_ma30"] = df["apy"].rolling(30, min_periods=1).mean()
            df["apy_vol"] = df["apy"].rolling(7, min_periods=1).std()
            df["tvl_change"] = df["tvlUsd"].pct_change()
            df = df.infer_objects(copy=False).ffill().bfill().fillna(0)
            
            # Create sequences
            seq_length = 168
            feature_cols = ["apy", "apy_ma7", "apy_ma30", "apy_vol", "tvlUsd", "tvl_change"]
            
            for i in range(len(df) - seq_length - 720):
                seq = df[feature_cols].iloc[i:i+seq_length].values
                
                # Multi-horizon targets
                targets = []
                for h in [1, 24, 168, 720]:
                    if i + seq_length + h < len(df):
                        targets.append(df["apy"].iloc[i + seq_length + h])
                    else:
                        targets.append(df["apy"].iloc[-1])
                
                # Pad to 20 features
                if seq.shape[1] < 20:
                    pad = np.zeros((seq.shape[0], 20 - seq.shape[1]))
                    seq = np.concatenate([seq, pad], axis=1)
                
                sequences.append({
                    "features": seq.astype(np.float32),
                    "targets": np.array(targets, dtype=np.float32)
                })
        
        print(f"  [OK] Generated {len(sequences)} training sequences")
        self.training_stats["total_samples"] = len(sequences)
        
        return sequences
    
    def train(self, sequences: list, epochs: int = 50, batch_size: int = 64):
        """Train the model with GPU and adaptive throttling."""
        if not sequences:
            print("  [ERROR] No training data!")
            return
        
        print("\n" + "-" * 60)
        print("  TRAINING ON GPU  (throttle cap: {:.0f}%)".format(self.max_gpu_util))
        print("-" * 60)
        
        # Start GPU monitor thread
        gpu_monitor = threading.Thread(target=self._update_gpu_stats, daemon=True)
        gpu_monitor.start()
        
        # Prepare data
        X = np.array([s["features"] for s in sequences])
        y = np.array([s["targets"] for s in sequences])
        
        # Normalization
        X_mean = X.mean(axis=(0, 1), keepdims=True)
        X_std = X.std(axis=(0, 1), keepdims=True) + 1e-8
        self.normalization_params = {"mean": X_mean, "std": X_std}
        X_norm = (X - X_mean) / X_std
        
        # Split
        n_train = int(len(X) * 0.8)
        X_train, X_val = X_norm[:n_train], X_norm[n_train:]
        y_train, y_val = y[:n_train], y[n_train:]
        
        print(f"  Training samples: {len(X_train)}")
        print(f"  Validation samples: {len(X_val)}")
        print(f"  Epochs: {epochs}")
        print(f"  Batch size: {batch_size}")
        print(f"  Device: {self.device}")
        print(f"  GPU util cap: {self.max_gpu_util:.0f}%")
        
        # DataLoaders
        train_loader = DataLoader(
            TensorDataset(torch.tensor(X_train), torch.tensor(y_train)),
            batch_size=batch_size, shuffle=True, pin_memory=True
        )
        val_loader = DataLoader(
            TensorDataset(torch.tensor(X_val), torch.tensor(y_val)),
            batch_size=batch_size, pin_memory=True
        )
        
        # Initialize model
        self.model = YieldTransformer(
            n_features=20,
            d_model=128,
            n_heads=8,
            n_encoder_layers=4,
            n_decoder_layers=2,
            d_ff=512,
            n_horizons=4,
            dropout=0.1
        ).to(self.device)
        
        # Optimizer
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-4, weight_decay=0.01)
        scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, patience=5, factor=0.5)
        loss_fn = YieldLoss()
        
        # Training loop
        self.training_stats["start_time"] = datetime.now()
        best_val_loss = float("inf")
        
        for epoch in range(epochs):
            if self.stop_flag:
                break
            
            self.training_stats["current_epoch"] = epoch + 1
            
            # ---------- Train ----------
            self.model.train()
            train_loss = 0
            
            for X_batch, y_batch in train_loader:
                X_batch = X_batch.to(self.device, non_blocking=True)
                y_batch = y_batch.to(self.device, non_blocking=True)
                
                optimizer.zero_grad()
                output = self.model(X_batch, return_uncertainty=True)
                loss = loss_fn(
                    predictions=output["predictions"],
                    targets=y_batch,
                    uncertainties=output.get("uncertainties")
                )["total_loss"]
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                optimizer.step()
                train_loss += loss.item()

                # ---- Dynamic throttle ----
                # The background thread keeps _throttler updated; just wait.
                self._throttler.wait()
            
            train_loss /= len(train_loader)
            
            # ---------- Validate ----------
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch = X_batch.to(self.device, non_blocking=True)
                    y_batch = y_batch.to(self.device, non_blocking=True)
                    output = self.model(X_batch, return_uncertainty=True)
                    loss = loss_fn(
                        predictions=output["predictions"],
                        targets=y_batch,
                        uncertainties=output.get("uncertainties")
                    )["total_loss"]
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            scheduler.step(val_loss)
            
            self.training_stats["epoch_loss"] = val_loss
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                self.training_stats["best_val_loss"] = best_val_loss
                self._save_model()
            
            # Print progress with GPU stats
            elapsed = (datetime.now() - self.training_stats["start_time"]).total_seconds()
            eta = elapsed / (epoch + 1) * (epochs - epoch - 1)
            
            gpu_mem  = self.training_stats["gpu_memory_used"]
            gpu_util = self.training_stats["gpu_utilization"]
            throttle = self.training_stats["throttle_sleep_ms"]
            
            print(f"\r  Epoch {epoch+1:3d}/{epochs} | "
                  f"Train: {train_loss:.4f} | Val: {val_loss:.4f} | "
                  f"GPU: {gpu_util:3.0f}% (cap {self.max_gpu_util:.0f}%) | "
                  f"Mem: {gpu_mem:.2f}GB | "
                  f"Throttle: {throttle:4.0f}ms | "
                  f"ETA: {timedelta(seconds=int(eta))}", end="")
        
        print("\n")
        self.stop_flag = True
        print(f"  Training complete! Best val loss: {best_val_loss:.4f}")
    
    def _save_model(self):
        """Save model checkpoint."""
        model_dir = Path(__file__).parent.parent / "models" / "yield_predictor"
        model_dir.mkdir(parents=True, exist_ok=True)
        
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "normalization_params": self.normalization_params,
            "training_stats": self.training_stats,
            "timestamp": datetime.now().isoformat()
        }
        torch.save(checkpoint, model_dir / "best_model.pt")
    
    def run(self, epochs: int = 50):
        """Run the full training pipeline."""
        sequences = self.fetch_data()
        if sequences:
            self.train(sequences, epochs=epochs)
            print("\n" + "=" * 60)
            print("  TRAINING COMPLETE!")
            print(f"  Model saved to: models/yield_predictor/best_model.pt")
            print("=" * 60)


def main():
    """Main entry point."""
    import argparse
    parser = argparse.ArgumentParser(description="Kerne Neural Net GPU Trainer")
    parser.add_argument("--epochs", type=int, default=50,
                        help="Number of epochs (default: 50)")
    parser.add_argument("--max-gpu-util", type=float, default=75.0,
                        help="Maximum GPU utilization %% to allow (default: 75). "
                             "Set to 100 to disable throttling.")
    args = parser.parse_args()
    
    trainer = GPUTrainer(max_gpu_util=args.max_gpu_util)
    trainer.run(epochs=args.epochs)


if __name__ == "__main__":
    main()