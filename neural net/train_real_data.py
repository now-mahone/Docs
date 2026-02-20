# Created: 2026-02-19
"""
Automated training with real historical data from free APIs.
Fetches yield data from DeFiLlama and market data from CoinGecko.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import time

import numpy as np
import pandas as pd
import requests
import torch
from torch.utils.data import DataLoader, TensorDataset

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent))

from src.yield_predictor import YieldTransformer, YieldLoss
from src.utils import setup_logging


# DeFiLlama yield pools to fetch
YIELD_POOLS = [
    ("aave-v3", "Arbitrum", "USDC"),  # Aave V3 USDC on Arbitrum
    ("aave-v3", "Arbitrum", "USDT"),  # Aave V3 USDT on Arbitrum
    ("aave-v3", "Base", "USDC"),      # Aave V3 USDC on Base
    ("compound-v3", "Arbitrum", "USDC"),  # Compound V3 USDC
    ("lido", "Ethereum", "stETH"),    # Lido stETH
]

# CoinGecko coin IDs
COINGECKO_IDS = {
    "ethereum": "ethereum",
    "bitcoin": "bitcoin",
}


def fetch_defillama_yields(logger) -> pd.DataFrame:
    """Fetch current yields from DeFiLlama API."""
    logger.info("Fetching DeFiLlama yields...")
    
    try:
        # DeFiLlama yields endpoint
        url = "https://yields.llama.fi/pools"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"DeFiLlama API returned {response.status_code}")
            return None
        
        data = response.json()
        pools = data.get("data", [])
        
        # Filter to relevant pools
        df = pd.DataFrame(pools)
        
        # Log what we got
        logger.info(f"Fetched {len(df)} pools from DeFiLlama")
        
        return df
        
    except Exception as e:
        logger.error(f"DeFiLlama fetch failed: {e}")
        return None


def fetch_defillama_historical(pool_id: str, logger) -> pd.DataFrame:
    """Fetch historical APY data for a specific pool."""
    logger.info(f"Fetching historical data for pool {pool_id}...")
    
    try:
        # DeFiLlama chart endpoint
        url = f"https://yields.llama.fi/chart/{pool_id}"
        response = requests.get(url, timeout=30)
        
        if response.status_code != 200:
            logger.warning(f"Historical data fetch returned {response.status_code}")
            return None
        
        data = response.json()
        points = data.get("data", [])
        
        if not points:
            return None
            
        df = pd.DataFrame(points)
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        
        logger.info(f"Fetched {len(df)} historical points for {pool_id}")
        return df
        
    except Exception as e:
        logger.error(f"Historical fetch failed for {pool_id}: {e}")
        return None


def fetch_coingecko_ohlc(days: int = 90, logger=None) -> pd.DataFrame:
    """Fetch ETH price OHLC data from CoinGecko."""
    if logger:
        logger.info("Fetching ETH price data from CoinGecko...")
    
    try:
        url = "https://api.coingecko.com/api/v3/coins/ethereum/ohlc"
        params = {"vs_currency": "usd", "days": min(days, 90)}
        
        response = requests.get(url, params=params, timeout=30)
        
        if response.status_code != 200:
            if logger:
                logger.warning(f"CoinGecko returned {response.status_code}")
            return None
        
        data = response.json()
        
        df = pd.DataFrame(data, columns=["timestamp_ms", "open", "high", "low", "close"])
        df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
        df = df.drop("timestamp_ms", axis=1)
        
        # Calculate returns and volatility
        df["return"] = df["close"].pct_change()
        df["volatility"] = df["return"].rolling(7).std() * np.sqrt(365)
        
        if logger:
            logger.info(f"Fetched {len(df)} ETH price points")
        
        return df
        
    except Exception as e:
        if logger:
            logger.error(f"CoinGecko fetch failed: {e}")
        return None


def generate_training_data_from_real(yields_df: pd.DataFrame, eth_df: pd.DataFrame, logger) -> tuple:
    """Generate training sequences from real data."""
    logger.info("Generating training sequences from real data...")
    
    # Get top stablecoin pools by TVL
    stablecoin_pools = yields_df[
        (yields_df["stablecoin"] == True) & 
        (yields_df["tvlUsd"] > 1e6)
    ].nlargest(20, "tvlUsd")
    
    logger.info(f"Found {len(stablecoin_pools)} stablecoin pools with TVL > $1M")
    
    all_sequences = []
    all_targets = []
    
    for idx, row in stablecoin_pools.iterrows():
        pool_id = row.get("pool", "")
        
        # Fetch historical data for this pool
        hist_df = fetch_defillama_historical(pool_id, logger)
        
        if hist_df is None or len(hist_df) < 200:
            continue
        
        # Merge with ETH price data
        hist_df["timestamp"] = pd.to_datetime(hist_df["timestamp"])
        
        # Create features
        hist_df["apy_ma7"] = hist_df["apy"].rolling(7).mean()
        hist_df["apy_ma30"] = hist_df["apy"].rolling(30).mean()
        hist_df["apy_vol"] = hist_df["apy"].rolling(7).std()
        hist_df["tvl_change"] = hist_df["tvlUsd"].pct_change()
        
        # Fill NaN
        hist_df = hist_df.fillna(method="bfill").fillna(method="ffill").fillna(0)
        
        # Create sequences
        seq_length = 168  # 7 days
        horizon = 24  # predict 24h ahead
        
        feature_cols = ["apy", "apy_ma7", "apy_ma30", "apy_vol", "tvlUsd", "tvl_change"]
        
        for i in range(len(hist_df) - seq_length - horizon):
            seq = hist_df[feature_cols].iloc[i:i+seq_length].values
            
            # Target: APY at horizon hours ahead (multi-horizon)
            targets = []
            for h in [1, 24, 168, 720]:  # 1h, 24h, 7d, 30d
                if i + seq_length + h < len(hist_df):
                    targets.append(hist_df["apy"].iloc[i + seq_length + h])
                else:
                    targets.append(hist_df["apy"].iloc[-1])
            
            # Pad to 20 features if needed
            if seq.shape[1] < 20:
                pad = np.zeros((seq.shape[0], 20 - seq.shape[1]))
                seq = np.concatenate([seq, pad], axis=1)
            
            all_sequences.append(seq)
            all_targets.append(targets)
        
        # Rate limiting
        time.sleep(0.5)
    
    if not all_sequences:
        logger.warning("No sequences generated from real data, using synthetic")
        return None, None
    
    X = np.array(all_sequences, dtype=np.float32)
    y = np.array(all_targets, dtype=np.float32)
    
    logger.info(f"Generated {len(X)} training sequences with shape {X.shape}")
    
    return X, y


def train_model(X: np.ndarray, y: np.ndarray, epochs: int, logger) -> YieldTransformer:
    """Train the yield predictor model."""
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    logger.info(f"Training on {device}")
    
    # Normalize
    X_mean = X.mean(axis=(0, 1), keepdims=True)
    X_std = X.std(axis=(0, 1), keepdims=True) + 1e-8
    X_norm = (X - X_mean) / X_std
    
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
    
    # Model
    model = YieldTransformer(
        n_features=20,
        d_model=128,
        n_heads=8,
        n_encoder_layers=4,
        n_decoder_layers=2,
        d_ff=512,
        n_horizons=4,
        dropout=0.1
    ).to(device)
    
    logger.info(f"Model has {sum(p.numel() for p in model.parameters()):,} parameters")
    
    # Training setup
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=0.01)
    scheduler = torch.optim.lr_scheduler.OneCycleLR(
        optimizer, max_lr=1e-4, epochs=epochs, steps_per_epoch=len(train_loader)
    )
    loss_fn = YieldLoss()
    
    best_val_loss = float("inf")
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0
        for X_batch, y_batch in train_loader:
            X_batch = X_batch.to(device)
            y_batch = y_batch.to(device)
            
            optimizer.zero_grad()
            output = model(X_batch, return_uncertainty=True)
            
            loss = loss_fn(
                predictions=output["predictions"],
                targets=y_batch,
                uncertainties=output.get("uncertainties")
            )["total_loss"]
            
            loss.backward()
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            optimizer.step()
            scheduler.step()
            
            train_loss += loss.item()
        
        # Validate
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for X_batch, y_batch in val_loader:
                X_batch = X_batch.to(device)
                y_batch = y_batch.to(device)
                
                output = model(X_batch, return_uncertainty=True)
                loss = loss_fn(
                    predictions=output["predictions"],
                    targets=y_batch,
                    uncertainties=output.get("uncertainties")
                )["total_loss"]
                
                val_loss += loss.item()
        
        train_loss /= len(train_loader)
        val_loss /= len(val_loader)
        
        logger.info(f"Epoch {epoch+1}/{epochs} - Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")
        
        # Save best
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            save_dir = Path(__file__).parent.parent / "models" / "yield_predictor"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            torch.save({
                "model_state_dict": model.state_dict(),
                "normalization_params": {"mean": X_mean, "std": X_std},
                "epoch": epoch,
                "val_loss": val_loss
            }, save_dir / "best_model.pt")
            
            logger.info(f"Saved best model (val_loss={val_loss:.4f})")
    
    return model


def main():
    logger = setup_logging("TrainRealData")
    logger.info("=" * 60)
    logger.info("Training Yield Predictor with Real Data")
    logger.info("=" * 60)
    
    # Fetch real data
    yields_df = fetch_defillama_yields(logger)
    eth_df = fetch_coingecko_ohlc(days=90, logger=logger)
    
    X, y = None, None
    
    # Try to generate from real data
    if yields_df is not None:
        X, y = generate_training_data_from_real(yields_df, eth_df, logger)
    
    # Fallback to enhanced synthetic if real data fails
    if X is None:
        logger.info("Using enhanced synthetic data with realistic patterns...")
        
        # Generate more realistic synthetic data
        n_samples = 2000
        seq_length = 168
        n_features = 20
        
        X = np.zeros((n_samples, seq_length, n_features), dtype=np.float32)
        y = np.zeros((n_samples, 4), dtype=np.float32)
        
        for i in range(n_samples):
            # Base APY with realistic drift
            base_apy = np.random.uniform(0.02, 0.15)
            trend = np.random.uniform(-0.02, 0.02)
            noise = np.random.randn(seq_length) * 0.005
            
            apy = base_apy + np.linspace(0, trend, seq_length) + np.cumsum(noise) * 0.1
            apy = np.maximum(apy, 0.001)
            
            # TVL
            base_tvl = np.random.uniform(1e6, 1e9)
            tvl = base_tvl * (1 + np.cumsum(np.random.randn(seq_length) * 0.01))
            
            # Features
            X[i, :, 0] = apy
            X[i, :, 1] = pd.Series(apy).rolling(7, min_periods=1).mean().values
            X[i, :, 2] = pd.Series(apy).rolling(30, min_periods=1).mean().values
            X[i, :, 3] = pd.Series(apy).rolling(7, min_periods=1).std().fillna(0).values
            X[i, :, 4] = np.log10(tvl)
            X[i, :, 5] = np.gradient(tvl)
            
            # Add more synthetic features
            for f in range(6, 20):
                X[i, :, f] = np.random.randn(seq_length) * 0.1
            
            # Targets (multi-horizon)
            y[i, 0] = apy[-1] + np.random.randn() * 0.005  # 1h
            y[i, 1] = apy[-1] + trend * 0.04 + np.random.randn() * 0.01  # 24h
            y[i, 2] = apy[-1] + trend * 0.28 + np.random.randn() * 0.02  # 7d
            y[i, 3] = apy[-1] + trend * 1.2 + np.random.randn() * 0.03  # 30d
        
        logger.info(f"Generated {n_samples} synthetic samples")
    
    # Train
    model = train_model(X, y, epochs=20, logger=logger)
    
    logger.info("=" * 60)
    logger.info("Training complete!")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()