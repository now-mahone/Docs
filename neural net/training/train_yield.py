# Created: 2026-02-19
"""
Training script for Yield Predictor model.
"""

import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.optim import AdamW
from torch.optim.lr_scheduler import OneCycleLR
from tqdm import tqdm

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.yield_predictor import YieldTransformer, YieldLoss
from src.data_pipeline import DataPipeline
from src.utils import load_config, setup_logging, EarlyStopping, compute_metrics


def parse_args():
    parser = argparse.ArgumentParser(description="Train Yield Predictor")
    parser.add_argument("--epochs", type=int, default=100, help="Number of epochs")
    parser.add_argument("--batch-size", type=int, default=64, help="Batch size")
    parser.add_argument("--lr", type=float, default=0.0001, help="Learning rate")
    parser.add_argument("--seq-length", type=int, default=168, help="Sequence length")
    parser.add_argument("--horizon", type=int, default=24, help="Prediction horizon")
    parser.add_argument("--device", type=str, default="auto", help="Device (cuda/cpu/auto)")
    parser.add_argument("--output-dir", type=str, default="models/yield_predictor", help="Output directory")
    parser.add_argument("--pool-ids", type=str, nargs="+", help="Pool IDs for training")
    parser.add_argument("--synthetic", action="store_true", help="Use synthetic data")
    return parser.parse_args()


def train_epoch(model, dataloader, optimizer, scheduler, loss_fn, device):
    """Train for one epoch."""
    model.train()
    total_loss = 0
    all_preds = []
    all_targets = []
    
    for batch in tqdm(dataloader, desc="Training"):
        X, y = batch
        X = X.to(device)
        y = y.to(device)
        
        optimizer.zero_grad()
        
        output = model(X, return_uncertainty=True)
        
        # Compute trend targets
        with torch.no_grad():
            trend_targets = torch.zeros(y.shape[0], dtype=torch.long, device=device)
            for i in range(y.shape[0]):
                if y[i, 0] > X[i, -1, 0] * 1.01:  # 1% increase
                    trend_targets[i] = 0  # up
                elif y[i, 0] < X[i, -1, 0] * 0.99:  # 1% decrease
                    trend_targets[i] = 2  # down
                else:
                    trend_targets[i] = 1  # stable
        
        losses = loss_fn(
            predictions=output["predictions"],
            targets=y,
            uncertainties=output.get("uncertainties"),
            trend_logits=output.get("trend_logits"),
            trend_targets=trend_targets
        )
        
        loss = losses["total_loss"]
        loss.backward()
        
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        optimizer.step()
        scheduler.step()
        
        total_loss += loss.item()
        all_preds.append(output["predictions"].detach().cpu().numpy())
        all_targets.append(y.detach().cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    preds = np.concatenate(all_preds)
    targets = np.concatenate(all_targets)
    
    metrics = compute_metrics(targets.flatten(), preds.flatten())
    
    return avg_loss, metrics


def validate(model, dataloader, loss_fn, device):
    """Validate the model."""
    model.eval()
    total_loss = 0
    all_preds = []
    all_targets = []
    
    with torch.no_grad():
        for batch in tqdm(dataloader, desc="Validation"):
            X, y = batch
            X = X.to(device)
            y = y.to(device)
            
            output = model(X, return_uncertainty=True)
            
            losses = loss_fn(
                predictions=output["predictions"],
                targets=y,
                uncertainties=output.get("uncertainties")
            )
            
            total_loss += losses["total_loss"].item()
            all_preds.append(output["predictions"].cpu().numpy())
            all_targets.append(y.cpu().numpy())
    
    avg_loss = total_loss / len(dataloader)
    preds = np.concatenate(all_preds)
    targets = np.concatenate(all_targets)
    
    metrics = compute_metrics(targets.flatten(), preds.flatten())
    
    return avg_loss, metrics


def main():
    args = parse_args()
    config = load_config()
    logger = setup_logging("TrainYieldPredictor")
    
    # Device
    if args.device == "auto":
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    else:
        device = torch.device(args.device)
    logger.info(f"Using device: {device}")
    
    # Data pipeline
    pipeline = DataPipeline(config=config)
    
    # Get pool IDs
    if args.pool_ids:
        pool_ids = args.pool_ids
    else:
        # Default pools for training
        pool_ids = [
            "aave-v3-usdc-arb",
            "aave-v3-usdt-arb",
            "compound-v3-usdc-base",
            "lido-steth-eth",
        ]
    
    logger.info(f"Training on pools: {pool_ids}")
    
    # Prepare data
    if args.synthetic:
        logger.info("Using synthetic data for training")
        # Generate synthetic training data
        n_samples = 1000
        seq_length = args.seq_length
        n_features = 20
        
        X = np.random.randn(n_samples, seq_length, n_features).astype(np.float32)
        y = np.random.randn(n_samples, 4).astype(np.float32) * 0.1 + 0.05
    else:
        logger.info("Preparing training data...")
        X, y = pipeline.prepare_training_data(
            pool_ids=pool_ids,
            seq_length=args.seq_length,
            horizon=args.horizon
        )
    
    logger.info(f"Training data shape: X={X.shape}, y={y.shape}")
    
    # Split data
    n_train = int(len(X) * 0.8)
    X_train, X_val = X[:n_train], X[n_train:]
    y_train, y_val = y[:n_train], y[n_train:]
    
    # Create dataloaders
    train_dataset = TensorDataset(
        torch.tensor(X_train, dtype=torch.float32),
        torch.tensor(y_train, dtype=torch.float32)
    )
    val_dataset = TensorDataset(
        torch.tensor(X_val, dtype=torch.float32),
        torch.tensor(y_val, dtype=torch.float32)
    )
    
    train_loader = DataLoader(train_dataset, batch_size=args.batch_size, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=args.batch_size)
    
    # Model
    model_config = config.get("yield_predictor", {}).get("model", {})
    model = YieldTransformer(
        n_features=X.shape[-1],
        d_model=model_config.get("d_model", 128),
        n_heads=model_config.get("n_heads", 8),
        n_encoder_layers=model_config.get("n_encoder_layers", 4),
        n_decoder_layers=model_config.get("n_decoder_layers", 2),
        d_ff=model_config.get("d_ff", 512),
        n_horizons=4,
        dropout=model_config.get("dropout", 0.1)
    ).to(device)
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Optimizer and scheduler
    optimizer = AdamW(model.parameters(), lr=args.lr, weight_decay=0.01)
    scheduler = OneCycleLR(
        optimizer,
        max_lr=args.lr,
        epochs=args.epochs,
        steps_per_epoch=len(train_loader)
    )
    
    # Loss function
    loss_fn = YieldLoss()
    
    # Early stopping
    early_stopping = EarlyStopping(patience=10, min_delta=0.001)
    
    # Training loop
    best_val_loss = float("inf")
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for epoch in range(args.epochs):
        logger.info(f"\nEpoch {epoch + 1}/{args.epochs}")
        
        # Train
        train_loss, train_metrics = train_epoch(
            model, train_loader, optimizer, scheduler, loss_fn, device
        )
        logger.info(f"Train Loss: {train_loss:.4f}, MAE: {train_metrics['mae']:.4f}")
        
        # Validate
        val_loss, val_metrics = validate(model, val_loader, loss_fn, device)
        logger.info(f"Val Loss: {val_loss:.4f}, MAE: {val_metrics['mae']:.4f}")
        
        # Save best model
        if val_loss < best_val_loss:
            best_val_loss = val_loss
            torch.save({
                "model_state_dict": model.state_dict(),
                "config": model_config,
                "normalization_params": pipeline._normalization_params,
                "epoch": epoch,
                "val_loss": val_loss
            }, output_dir / "best_model.pt")
            logger.info(f"Saved best model (val_loss={val_loss:.4f})")
        
        # Early stopping
        if early_stopping(val_loss):
            logger.info(f"Early stopping at epoch {epoch + 1}")
            break
    
    # Save final model
    torch.save({
        "model_state_dict": model.state_dict(),
        "config": model_config,
        "normalization_params": pipeline._normalization_params,
        "epoch": args.epochs,
        "val_loss": val_loss
    }, output_dir / "final_model.pt")
    
    logger.info(f"Training complete. Best val loss: {best_val_loss:.4f}")
    logger.info(f"Models saved to {output_dir}")


if __name__ == "__main__":
    main()