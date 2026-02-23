# Created: 2026-02-19
"""
Continuous Learning System for Yield Predictor
================================================

Runs continuously on DigitalOcean, fetching new data, training, and serving predictions.
Implements online learning with periodic retraining.
"""

import os
import sys
import time
import json
import signal
from pathlib import Path
from datetime import datetime, timedelta
from threading import Thread, Event
import queue

import numpy as np
import pandas as pd
import requests
import torch
from torch.utils.data import DataLoader, TensorDataset

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.yield_predictor import YieldTransformer, YieldLoss
from src.utils import setup_logging


class ContinuousLearner:
    """
    Continuous learning system that:
    1. Fetches new data every hour
    2. Retrains model periodically
    3. Serves predictions via in-memory cache
    4. Logs all activity
    """
    
    def __init__(self, config: dict = None):
        self.config = config or {}
        self.logger = setup_logging("ContinuousLearner")
        
        # Training config
        self.retrain_interval = self.config.get("retrain_interval_hours", 6)
        self.data_fetch_interval = self.config.get("data_fetch_interval_minutes", 60)
        self.min_new_samples = self.config.get("min_new_samples", 100)
        self.epochs_per_retrain = self.config.get("epochs_per_retrain", 5)
        
        # Model paths
        self.model_dir = Path(__file__).parent.parent / "models" / "yield_predictor"
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.model_path = self.model_dir / "best_model.pt"
        
        # Device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        
        # Model state
        self.model = None
        self.normalization_params = None
        self.training_data_buffer = []
        self.last_retrain = None
        self.last_data_fetch = None
        
        # Prediction cache
        self.prediction_cache = {}
        self.cache_timestamp = None
        
        # Control
        self.running = False
        self.stop_event = Event()
        
        # Metrics
        self.metrics = {
            "total_retrains": 0,
            "total_predictions": 0,
            "data_fetches": 0,
            "start_time": None,
            "last_loss": None
        }
        
        # Initialize model
        self._init_model()
    
    def _init_model(self):
        """Initialize or load model."""
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
        
        if self.model_path.exists():
            try:
                checkpoint = torch.load(self.model_path, map_location=self.device, weights_only=False)
                self.model.load_state_dict(checkpoint["model_state_dict"])
                self.normalization_params = checkpoint.get("normalization_params", {})
                self.logger.info(f"Loaded existing model from {self.model_path}")
            except Exception as e:
                self.logger.warning(f"Failed to load model: {e}. Starting fresh.")
        else:
            self.logger.info("No existing model found. Starting with fresh model.")
    
    def fetch_latest_data(self) -> pd.DataFrame:
        """Fetch latest yield data from DeFiLlama."""
        self.logger.info("Fetching latest yield data...")
        
        try:
            # Get all pools
            url = "https://yields.llama.fi/pools"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                self.logger.error(f"DeFiLlama API returned {response.status_code}")
                return None
            
            data = response.json()
            pools = data.get("data", [])
            df = pd.DataFrame(pools)
            
            # Filter stablecoin pools with good TVL
            stablecoin_pools = df[
                (df.get("stablecoin", False) == True) & 
                (df["tvlUsd"] > 1e6)
            ].nlargest(50, "tvlUsd")
            
            self.metrics["data_fetches"] += 1
            self.logger.info(f"Fetched {len(stablecoin_pools)} stablecoin pools")
            
            return stablecoin_pools
            
        except Exception as e:
            self.logger.error(f"Data fetch failed: {e}")
            return None
    
    def fetch_historical_for_pool(self, pool_id: str) -> pd.DataFrame:
        """Fetch historical data for a specific pool."""
        try:
            url = f"https://yields.llama.fi/chart/{pool_id}"
            response = requests.get(url, timeout=30)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            points = data.get("data", [])
            
            if not points:
                return None
            
            df = pd.DataFrame(points)
            df["timestamp"] = pd.to_datetime(df["timestamp"])
            df["pool_id"] = pool_id
            
            return df
            
        except Exception as e:
            return None
    
    def prepare_sequences(self, pool_data: dict) -> list:
        """Prepare training sequences from pool data."""
        sequences = []
        
        for pool_id, df in pool_data.items():
            if df is None or len(df) < 200:
                continue
            
            # Create features
            df["apy_ma7"] = df["apy"].rolling(7, min_periods=1).mean()
            df["apy_ma30"] = df["apy"].rolling(30, min_periods=1).mean()
            df["apy_vol"] = df["apy"].rolling(7, min_periods=1).std()
            df["tvl_change"] = df["tvlUsd"].pct_change()
            
            df = df.ffill().bfill().fillna(0)
            
            # Create sequences
            seq_length = 168
            feature_cols = ["apy", "apy_ma7", "apy_ma30", "apy_vol", "tvlUsd", "tvl_change"]
            
            for i in range(len(df) - seq_length - 720):  # Need 30 days ahead for targets
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
                    "targets": np.array(targets, dtype=np.float32),
                    "pool_id": pool_id,
                    "timestamp": df["timestamp"].iloc[i + seq_length]
                })
        
        return sequences
    
    def train_step(self, new_sequences: list):
        """Perform incremental training with new data."""
        if not new_sequences:
            self.logger.warning("No new sequences to train on")
            return
        
        self.logger.info(f"Training on {len(new_sequences)} new sequences...")
        
        # Prepare data
        X = np.array([s["features"] for s in new_sequences])
        y = np.array([s["targets"] for s in new_sequences])
        
        # Update normalization params incrementally
        if self.normalization_params is None:
            X_mean = X.mean(axis=(0, 1), keepdims=True)
            X_std = X.std(axis=(0, 1), keepdims=True) + 1e-8
            self.normalization_params = {"mean": X_mean, "std": X_std}
        else:
            # Incremental mean/std update (exponential moving average)
            alpha = 0.1  # Learning rate for normalization update
            new_mean = X.mean(axis=(0, 1), keepdims=True)
            new_std = X.std(axis=(0, 1), keepdims=True) + 1e-8
            
            old_mean = self.normalization_params["mean"]
            old_std = self.normalization_params["std"]
            
            self.normalization_params["mean"] = (1 - alpha) * old_mean + alpha * new_mean
            self.normalization_params["std"] = (1 - alpha) * old_std + alpha * new_std
        
        # Normalize
        X_norm = (X - self.normalization_params["mean"]) / self.normalization_params["std"]
        
        # Split
        n_train = int(len(X) * 0.8)
        X_train, X_val = X_norm[:n_train], X_norm[n_train:]
        y_train, y_val = y[:n_train], y[n_train:]
        
        # DataLoaders
        train_loader = DataLoader(
            TensorDataset(torch.tensor(X_train), torch.tensor(y_train)),
            batch_size=32, shuffle=True
        )
        val_loader = DataLoader(
            TensorDataset(torch.tensor(X_val), torch.tensor(y_val)),
            batch_size=32
        )
        
        # Training
        self.model.train()
        optimizer = torch.optim.AdamW(self.model.parameters(), lr=1e-5, weight_decay=0.01)
        loss_fn = YieldLoss()
        
        best_val_loss = float("inf")
        
        for epoch in range(self.epochs_per_retrain):
            # Train
            train_loss = 0
            for X_batch, y_batch in train_loader:
                X_batch = X_batch.to(self.device)
                y_batch = y_batch.to(self.device)
                
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
            
            # Validate
            self.model.eval()
            val_loss = 0
            with torch.no_grad():
                for X_batch, y_batch in val_loader:
                    X_batch = X_batch.to(self.device)
                    y_batch = y_batch.to(self.device)
                    
                    output = self.model(X_batch, return_uncertainty=True)
                    loss = loss_fn(
                        predictions=output["predictions"],
                        targets=y_batch,
                        uncertainties=output.get("uncertainties")
                    )["total_loss"]
                    
                    val_loss += loss.item()
            
            train_loss /= len(train_loader)
            val_loss /= len(val_loader)
            
            self.logger.info(f"Epoch {epoch+1}/{self.epochs_per_retrain} - Train: {train_loss:.4f}, Val: {val_loss:.4f}")
            
            if val_loss < best_val_loss:
                best_val_loss = val_loss
        
        self.metrics["total_retrains"] += 1
        self.metrics["last_loss"] = best_val_loss
        self.last_retrain = datetime.utcnow()
        
        # Save model
        self._save_model()
        
        self.logger.info(f"Training complete. Best val loss: {best_val_loss:.4f}")
    
    def _save_model(self):
        """Save model checkpoint."""
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "normalization_params": self.normalization_params,
            "last_retrain": self.last_retrain.isoformat() if self.last_retrain else None,
            "metrics": self.metrics
        }
        torch.save(checkpoint, self.model_path)
        self.logger.info(f"Model saved to {self.model_path}")
    
    def predict(self, features: np.ndarray) -> dict:
        """Make prediction for given features."""
        self.model.eval()
        
        # Normalize
        if self.normalization_params:
            features = (features - self.normalization_params["mean"].squeeze()) / (
                self.normalization_params["std"].squeeze() + 1e-8
            )
        
        # Prepare tensor
        x = torch.tensor(features, dtype=torch.float32).unsqueeze(0).to(self.device)
        
        with torch.no_grad():
            output = self.model(x, return_uncertainty=True)
        
        predictions = output["predictions"].cpu().numpy().flatten()
        uncertainties = output["uncertainties"].cpu().numpy().flatten()
        trend_logits = output["trend_logits"].cpu().numpy().flatten()
        
        self.metrics["total_predictions"] += 1
        
        return {
            "predictions": {
                "1h": float(predictions[0]),
                "24h": float(predictions[1]),
                "7d": float(predictions[2]),
                "30d": float(predictions[3])
            },
            "uncertainties": {
                "1h": float(uncertainties[0]),
                "24h": float(uncertainties[1]),
                "7d": float(uncertainties[2]),
                "30d": float(uncertainties[3])
            },
            "trend": ["up", "stable", "down"][int(np.argmax(trend_logits))],
            "trend_logits": trend_logits.tolist(),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def update_predictions_cache(self):
        """Update prediction cache for top pools."""
        self.logger.info("Updating prediction cache...")
        
        pools_df = self.fetch_latest_data()
        if pools_df is None:
            return
        
        for idx, row in pools_df.head(20).iterrows():
            pool_id = row.get("pool", "")
            pool_name = row.get("symbol", pool_id)
            
            # Create feature vector from current state
            features = np.zeros((168, 20), dtype=np.float32)
            features[:, 0] = row.get("apy", 0.05)  # Current APY
            features[:, 1] = row.get("apy", 0.05)  # MA7 (approx)
            features[:, 2] = row.get("apy", 0.05)  # MA30 (approx)
            features[:, 3] = 0.01  # Volatility estimate
            features[:, 4] = np.log10(max(row.get("tvlUsd", 1e6), 1))  # log TVL
            features[:, 5] = 0.0  # TVL change
            
            try:
                prediction = self.predict(features)
                prediction["pool_name"] = pool_name
                prediction["current_apy"] = row.get("apy", 0)
                prediction["tvl_usd"] = row.get("tvlUsd", 0)
                self.prediction_cache[pool_id] = prediction
            except Exception as e:
                self.logger.error(f"Prediction failed for {pool_id}: {e}")
        
        self.cache_timestamp = datetime.utcnow()
        self.logger.info(f"Cached predictions for {len(self.prediction_cache)} pools")
    
    def run_data_collection(self):
        """Background thread for data collection."""
        while not self.stop_event.is_set():
            try:
                self.logger.info("Starting data collection cycle...")
                
                # Fetch latest pools
                pools_df = self.fetch_latest_data()
                if pools_df is not None:
                    # Fetch historical for top pools
                    pool_data = {}
                    for idx, row in pools_df.head(30).iterrows():
                        pool_id = row.get("pool", "")
                        hist_df = self.fetch_historical_for_pool(pool_id)
                        if hist_df is not None:
                            pool_data[pool_id] = hist_df
                        time.sleep(0.3)  # Rate limit
                    
                    # Prepare sequences
                    new_sequences = self.prepare_sequences(pool_data)
                    self.training_data_buffer.extend(new_sequences)
                    
                    self.logger.info(f"Buffer now has {len(self.training_data_buffer)} sequences")
                
                # Update predictions
                self.update_predictions_cache()
                
                self.last_data_fetch = datetime.utcnow()
                
            except Exception as e:
                self.logger.error(f"Data collection error: {e}")
            
            # Wait for next cycle
            self.stop_event.wait(self.data_fetch_interval * 60)
    
    def run_training(self):
        """Background thread for periodic training."""
        while not self.stop_event.is_set():
            try:
                # Check if we have enough new data
                if len(self.training_data_buffer) >= self.min_new_samples:
                    self.logger.info(f"Starting retraining with {len(self.training_data_buffer)} samples...")
                    
                    # Train on buffer
                    self.train_step(self.training_data_buffer)
                    
                    # Clear buffer after training (keep some for continuity)
                    self.training_data_buffer = self.training_data_buffer[-500:]
                
                elif self.last_retrain is None:
                    # First run - train on whatever we have
                    if len(self.training_data_buffer) > 0:
                        self.train_step(self.training_data_buffer)
                
            except Exception as e:
                self.logger.error(f"Training error: {e}")
            
            # Wait for next training cycle
            self.stop_event.wait(self.retrain_interval * 3600)
    
    def start(self):
        """Start continuous learning."""
        self.logger.info("=" * 60)
        self.logger.info("Starting Continuous Learning System")
        self.logger.info("=" * 60)
        
        self.running = True
        self.metrics["start_time"] = datetime.utcnow().isoformat()
        
        # Start background threads
        self.data_thread = Thread(target=self.run_data_collection, daemon=True)
        self.training_thread = Thread(target=self.run_training, daemon=True)
        
        self.data_thread.start()
        self.training_thread.start()
        
        self.logger.info("Background threads started")
        
        # Keep main thread alive
        try:
            while self.running:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop()
    
    def stop(self):
        """Stop continuous learning."""
        self.logger.info("Stopping Continuous Learning System...")
        self.running = False
        self.stop_event.set()
        self._save_model()
        self.logger.info("Stopped")
    
    def get_status(self) -> dict:
        """Get current system status."""
        return {
            "running": self.running,
            "device": str(self.device),
            "last_retrain": self.last_retrain.isoformat() if self.last_retrain else None,
            "last_data_fetch": self.last_data_fetch.isoformat() if self.last_data_fetch else None,
            "buffer_size": len(self.training_data_buffer),
            "cache_size": len(self.prediction_cache),
            "cache_timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            "metrics": self.metrics
        }
    
    def get_predictions(self) -> dict:
        """Get all cached predictions."""
        return {
            "timestamp": self.cache_timestamp.isoformat() if self.cache_timestamp else None,
            "predictions": self.prediction_cache
        }


def main():
    """Main entry point."""
    learner = ContinuousLearner(
        config={
            "retrain_interval_hours": 6,
            "data_fetch_interval_minutes": 60,
            "min_new_samples": 100,
            "epochs_per_retrain": 5
        }
    )
    
    # Handle shutdown signals
    def handle_shutdown(signum, frame):
        learner.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, handle_shutdown)
    signal.signal(signal.SIGTERM, handle_shutdown)
    
    # Start
    learner.start()


if __name__ == "__main__":
    main()