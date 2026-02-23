# Created: 2026-02-19
"""
Kerne Neural Net - Utility Functions
====================================
Shared utilities for configuration, logging, and common operations.
"""

import os
import yaml
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Union
from datetime import datetime, timedelta
import numpy as np
import torch


def load_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    Load configuration from YAML file.
    
    Args:
        config_path: Path to config file. Defaults to ../config.yaml
        
    Returns:
        Configuration dictionary
    """
    if config_path is None:
        config_path = Path(__file__).parent.parent / "config.yaml"
    else:
        config_path = Path(config_path)
    
    if not config_path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    
    # Expand environment variables
    config = _expand_env_vars(config)
    
    return config


def _expand_env_vars(config: Any) -> Any:
    """Recursively expand environment variables in config values."""
    if isinstance(config, dict):
        return {k: _expand_env_vars(v) for k, v in config.items()}
    elif isinstance(config, list):
        return [_expand_env_vars(item) for item in config]
    elif isinstance(config, str):
        # Handle ${VAR:default} syntax
        if config.startswith("${") and "}" in config:
            var_part = config[2:config.index("}")]
            if ":" in var_part:
                var_name, default = var_part.split(":", 1)
                return os.getenv(var_name, default)
            else:
                return os.getenv(var_part, config)
        return config
    else:
        return config


def setup_logging(
    name: str = "kerne_neural_net",
    level: str = "INFO",
    log_file: Optional[str] = None
) -> logging.Logger:
    """
    Setup logging for the neural net module.
    
    Args:
        name: Logger name
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for logging
        
    Returns:
        Configured logger instance
    """
    # Try to use loguru if available
    try:
        from loguru import logger
        logger.remove()
        logger.add(
            sink=lambda msg: print(msg, end=""),
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
        if log_file:
            logger.add(log_file, level=level, rotation="10 MB")
        return logger
    except ImportError:
        # Fallback to standard logging
        logger = logging.getLogger(name)
        logger.setLevel(getattr(logging, level.upper()))
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            handler.setLevel(getattr(logging, level.upper()))
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
            if log_file:
                file_handler = logging.FileHandler(log_file)
                file_handler.setLevel(getattr(logging, level.upper()))
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
        
        return logger


def get_device(device_config: str = "auto") -> torch.device:
    """
    Get the appropriate torch device.
    
    Args:
        device_config: Device configuration ("cuda", "cpu", "mps", "auto")
        
    Returns:
        torch.device instance
    """
    if device_config == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        else:
            return torch.device("cpu")
    else:
        return torch.device(device_config)


def normalize_data(
    data: np.ndarray,
    method: str = "minmax",
    axis: int = 0
) -> tuple:
    """
    Normalize data using specified method.
    
    Args:
        data: Input data array
        method: Normalization method ("minmax", "zscore", "robust")
        axis: Axis along which to normalize
        
    Returns:
        Tuple of (normalized_data, params) where params can be used to inverse transform
    """
    if method == "minmax":
        min_val = np.min(data, axis=axis, keepdims=True)
        max_val = np.max(data, axis=axis, keepdims=True)
        normalized = (data - min_val) / (max_val - min_val + 1e-8)
        params = {"min": min_val, "max": max_val}
    elif method == "zscore":
        mean = np.mean(data, axis=axis, keepdims=True)
        std = np.std(data, axis=axis, keepdims=True)
        normalized = (data - mean) / (std + 1e-8)
        params = {"mean": mean, "std": std}
    elif method == "robust":
        median = np.median(data, axis=axis, keepdims=True)
        q1 = np.percentile(data, 25, axis=axis, keepdims=True)
        q3 = np.percentile(data, 75, axis=axis, keepdims=True)
        iqr = q3 - q1
        normalized = (data - median) / (iqr + 1e-8)
        params = {"median": median, "iqr": iqr}
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized, params


def inverse_normalize(
    normalized_data: np.ndarray,
    params: Dict[str, np.ndarray],
    method: str = "minmax"
) -> np.ndarray:
    """
    Inverse normalize data using stored parameters.
    
    Args:
        normalized_data: Normalized data array
        params: Parameters from normalize_data
        method: Normalization method used
        
    Returns:
        Original scale data
    """
    if method == "minmax":
        return normalized_data * (params["max"] - params["min"]) + params["min"]
    elif method == "zscore":
        return normalized_data * params["std"] + params["mean"]
    elif method == "robust":
        return normalized_data * params["iqr"] + params["median"]
    else:
        raise ValueError(f"Unknown normalization method: {method}")


def compute_time_features(
    timestamps: np.ndarray,
    features: list = ["hour", "day_of_week", "day_of_month", "month"]
) -> np.ndarray:
    """
    Compute time-based features from timestamps.
    
    Args:
        timestamps: Array of Unix timestamps
        features: List of time features to compute
        
    Returns:
        Array of time features with shape (len(timestamps), len(features))
    """
    dt_objects = [datetime.fromtimestamp(ts) for ts in timestamps]
    
    feature_values = []
    for dt in dt_objects:
        row = []
        for feat in features:
            if feat == "hour":
                row.append(dt.hour / 23.0)  # Normalize to [0, 1]
            elif feat == "day_of_week":
                row.append(dt.weekday() / 6.0)
            elif feat == "day_of_month":
                row.append((dt.day - 1) / 30.0)
            elif feat == "month":
                row.append((dt.month - 1) / 11.0)
            elif feat == "is_weekend":
                row.append(1.0 if dt.weekday() >= 5 else 0.0)
        feature_values.append(row)
    
    return np.array(feature_values)


def create_sequences(
    data: np.ndarray,
    seq_length: int,
    horizon: int = 1,
    stride: int = 1
) -> tuple:
    """
    Create sequences for time series prediction.
    
    Args:
        data: Input data with shape (n_samples, n_features)
        seq_length: Length of input sequences
        horizon: Prediction horizon
        stride: Stride between sequences
        
    Returns:
        Tuple of (X, y) where X has shape (n_sequences, seq_length, n_features)
        and y has shape (n_sequences, horizon, n_features) or (n_sequences, horizon)
    """
    n_samples = len(data)
    X, y = [], []
    
    for i in range(0, n_samples - seq_length - horizon + 1, stride):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length:i + seq_length + horizon])
    
    return np.array(X), np.array(y)


def compute_metrics(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    metrics: list = ["mae", "mse", "mape", "r2"]
) -> Dict[str, float]:
    """
    Compute regression metrics.
    
    Args:
        y_true: Ground truth values
        y_pred: Predicted values
        metrics: List of metrics to compute
        
    Returns:
        Dictionary of metric values
    """
    results = {}
    
    y_true = np.array(y_true).flatten()
    y_pred = np.array(y_pred).flatten()
    
    if "mae" in metrics:
        results["mae"] = np.mean(np.abs(y_true - y_pred))
    
    if "mse" in metrics:
        results["mse"] = np.mean((y_true - y_pred) ** 2)
    
    if "rmse" in metrics:
        results["rmse"] = np.sqrt(np.mean((y_true - y_pred) ** 2))
    
    if "mape" in metrics:
        # Avoid division by zero
        mask = y_true != 0
        if mask.any():
            results["mape"] = np.mean(np.abs((y_true[mask] - y_pred[mask]) / y_true[mask])) * 100
        else:
            results["mape"] = float("inf")
    
    if "r2" in metrics:
        ss_res = np.sum((y_true - y_pred) ** 2)
        ss_tot = np.sum((y_true - np.mean(y_true)) ** 2)
        results["r2"] = 1 - (ss_res / (ss_tot + 1e-8))
    
    if "direction_accuracy" in metrics:
        # For time series: how often we predict the right direction
        true_direction = np.diff(y_true) > 0
        pred_direction = np.diff(y_pred) > 0
        results["direction_accuracy"] = np.mean(true_direction == pred_direction)
    
    return results


def detect_anomalies(
    data: np.ndarray,
    method: str = "zscore",
    threshold: float = 3.0
) -> np.ndarray:
    """
    Detect anomalies in data.
    
    Args:
        data: Input data array
        method: Detection method ("zscore", "iqr", "isolation_forest")
        threshold: Threshold for anomaly detection
        
    Returns:
        Boolean array where True indicates anomaly
    """
    if method == "zscore":
        mean = np.mean(data)
        std = np.std(data)
        z_scores = np.abs((data - mean) / (std + 1e-8))
        return z_scores > threshold
    
    elif method == "iqr":
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        return (data < lower_bound) | (data > upper_bound)
    
    elif method == "isolation_forest":
        try:
            from sklearn.ensemble import IsolationForest
            iso = IsolationForest(contamination=0.05, random_state=42)
            predictions = iso.fit_predict(data.reshape(-1, 1))
            return predictions == -1
        except ImportError:
            # Fallback to zscore
            return detect_anomalies(data, method="zscore", threshold=threshold)
    
    else:
        raise ValueError(f"Unknown anomaly detection method: {method}")


def format_prediction_output(
    predictions: np.ndarray,
    confidence_intervals: Optional[np.ndarray] = None,
    horizon_names: list = ["1h", "24h", "7d", "30d"]
) -> Dict[str, Any]:
    """
    Format prediction output for API response.
    
    Args:
        predictions: Predicted values
        confidence_intervals: Optional (lower, upper) bounds
        horizon_names: Names for each horizon
        
    Returns:
        Formatted dictionary
    """
    output = {
        "predictions": {},
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    for i, name in enumerate(horizon_names[:len(predictions)]):
        output["predictions"][name] = {
            "value": float(predictions[i]),
        }
        if confidence_intervals is not None:
            output["predictions"][name]["lower"] = float(confidence_intervals[0][i])
            output["predictions"][name]["upper"] = float(confidence_intervals[1][i])
    
    return output


class EarlyStopping:
    """Early stopping callback for training."""
    
    def __init__(
        self,
        patience: int = 10,
        min_delta: float = 0.0,
        mode: str = "min"
    ):
        """
        Initialize early stopping.
        
        Args:
            patience: Number of epochs to wait before stopping
            min_delta: Minimum change to qualify as improvement
            mode: "min" for loss, "max" for metrics
        """
        self.patience = patience
        self.min_delta = min_delta
        self.mode = mode
        self.counter = 0
        self.best_value = None
        self.should_stop = False
        
    def __call__(self, value: float) -> bool:
        """
        Check if training should stop.
        
        Args:
            value: Current metric value
            
        Returns:
            True if training should stop
        """
        if self.best_value is None:
            self.best_value = value
            return False
        
        if self.mode == "min":
            improved = value < self.best_value - self.min_delta
        else:
            improved = value > self.best_value + self.min_delta
        
        if improved:
            self.best_value = value
            self.counter = 0
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.should_stop = True
        
        return self.should_stop
    
    def reset(self):
        """Reset early stopping state."""
        self.counter = 0
        self.best_value = None
        self.should_stop = False