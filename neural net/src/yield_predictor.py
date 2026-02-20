# Created: 2026-02-19
"""
Kerne Yield Predictor - Time-Series Transformer for APY Forecasting
====================================================================

Predictive Transformer model for forecasting yield (APY) across DeFi protocols.
Supports multi-horizon prediction (1h, 24h, 7d, 30d) with uncertainty quantification.
"""

import math
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass
from datetime import datetime

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch import Tensor

from .utils import load_config, get_device, setup_logging


@dataclass
class YieldPrediction:
    """Container for yield prediction results."""
    pool_id: str
    predictions: Dict[str, float]  # horizon -> predicted APY
    confidence_intervals: Dict[str, Tuple[float, float]]  # horizon -> (lower, upper)
    trend: str  # "up", "down", "stable"
    anomaly_detected: bool
    timestamp: str
    model_version: str


class PositionalEncoding(nn.Module):
    """
    Sinusoidal positional encoding for transformer.
    
    Adds positional information to input embeddings using sine and cosine functions
    of different frequencies.
    """
    
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        super().__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        position = torch.arange(max_len).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2) * (-math.log(10000.0) / d_model))
        
        pe = torch.zeros(1, max_len, d_model)
        pe[0, :, 0::2] = torch.sin(position * div_term)
        pe[0, :, 1::2] = torch.cos(position * div_term)
        
        self.register_buffer('pe', pe)
    
    def forward(self, x: Tensor) -> Tensor:
        """
        Args:
            x: Tensor of shape (batch_size, seq_len, d_model)
        Returns:
            Tensor with positional encoding added
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TemporalFusionLayer(nn.Module):
    """
    Temporal Fusion Layer for capturing time-series patterns.
    
    Combines self-attention with temporal convolutions for better
    capture of local and global temporal patterns.
    """
    
    def __init__(
        self,
        d_model: int,
        n_heads: int,
        d_ff: int,
        dropout: float = 0.1,
        kernel_size: int = 3
    ):
        super().__init__()
        
        # Multi-head self-attention
        self.self_attn = nn.MultiheadAttention(
            d_model, n_heads, dropout=dropout, batch_first=True
        )
        
        # Temporal convolution for local patterns
        self.temporal_conv = nn.Conv1d(
            d_model, d_model, kernel_size, 
            padding=kernel_size // 2, groups=d_model
        )
        
        # Feed-forward network
        self.ffn = nn.Sequential(
            nn.Linear(d_model, d_ff),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_ff, d_model),
            nn.Dropout(dropout)
        )
        
        # Layer normalization
        self.norm1 = nn.LayerNorm(d_model)
        self.norm2 = nn.LayerNorm(d_model)
        self.norm3 = nn.LayerNorm(d_model)
        
        self.dropout = nn.Dropout(dropout)
    
    def forward(self, x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        """
        Args:
            x: Input tensor of shape (batch_size, seq_len, d_model)
            mask: Optional attention mask
        Returns:
            Output tensor of shape (batch_size, seq_len, d_model)
        """
        # Self-attention with residual
        attn_out, _ = self.self_attn(x, x, x, attn_mask=mask)
        x = self.norm1(x + self.dropout(attn_out))
        
        # Temporal convolution with residual
        # Transpose for conv1d: (batch, d_model, seq_len)
        x_t = x.transpose(1, 2)
        conv_out = self.temporal_conv(x_t).transpose(1, 2)
        x = self.norm2(x + self.dropout(conv_out))
        
        # Feed-forward with residual
        ffn_out = self.ffn(x)
        x = self.norm3(x + ffn_out)
        
        return x


class YieldTransformer(nn.Module):
    """
    Transformer model for yield prediction.
    
    Architecture:
    - Input embedding layer for time-series features
    - Positional encoding
    - Stack of temporal fusion layers
    - Multi-horizon prediction heads
    - Uncertainty estimation heads
    """
    
    def __init__(
        self,
        n_features: int,
        d_model: int = 128,
        n_heads: int = 8,
        n_encoder_layers: int = 4,
        n_decoder_layers: int = 2,
        d_ff: int = 512,
        n_horizons: int = 4,
        dropout: float = 0.1,
        max_seq_len: int = 168
    ):
        super().__init__()
        
        self.d_model = d_model
        self.n_horizons = n_horizons
        
        # Input projection
        self.input_projection = nn.Linear(n_features, d_model)
        
        # Positional encoding
        self.pos_encoding = PositionalEncoding(d_model, max_seq_len, dropout)
        
        # Encoder layers
        self.encoder_layers = nn.ModuleList([
            TemporalFusionLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_encoder_layers)
        ])
        
        # Decoder layers (for sequence-to-sequence prediction)
        self.decoder_layers = nn.ModuleList([
            TemporalFusionLayer(d_model, n_heads, d_ff, dropout)
            for _ in range(n_decoder_layers)
        ])
        
        # Prediction heads for each horizon
        self.prediction_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, d_model // 2),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_model // 2, 1)
            )
            for _ in range(n_horizons)
        ])
        
        # Uncertainty heads (predict log variance for each horizon)
        self.uncertainty_heads = nn.ModuleList([
            nn.Sequential(
                nn.Linear(d_model, d_model // 2),
                nn.GELU(),
                nn.Dropout(dropout),
                nn.Linear(d_model // 2, 1)
            )
            for _ in range(n_horizons)
        ])
        
        # Global pooling for final prediction
        self.global_pool = nn.AdaptiveAvgPool1d(1)
        
        # Trend classification head
        self.trend_head = nn.Sequential(
            nn.Linear(d_model, d_model // 2),
            nn.GELU(),
            nn.Dropout(dropout),
            nn.Linear(d_model // 2, 3)  # up, down, stable
        )
    
    def encode(self, x: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        """
        Encode input sequence.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, n_features)
            mask: Optional attention mask
            
        Returns:
            Encoded representation of shape (batch_size, seq_len, d_model)
        """
        # Project input to model dimension
        x = self.input_projection(x)
        
        # Add positional encoding
        x = self.pos_encoding(x)
        
        # Pass through encoder layers
        for layer in self.encoder_layers:
            x = layer(x, mask)
        
        return x
    
    def decode(self, encoded: Tensor, mask: Optional[Tensor] = None) -> Tensor:
        """
        Decode encoded representation.
        
        Args:
            encoded: Encoded tensor of shape (batch_size, seq_len, d_model)
            mask: Optional attention mask
            
        Returns:
            Decoded representation of shape (batch_size, seq_len, d_model)
        """
        for layer in self.decoder_layers:
            encoded = layer(encoded, mask)
        
        return encoded
    
    def forward(
        self, 
        x: Tensor, 
        mask: Optional[Tensor] = None,
        return_uncertainty: bool = True
    ) -> Dict[str, Tensor]:
        """
        Forward pass.
        
        Args:
            x: Input tensor of shape (batch_size, seq_len, n_features)
            mask: Optional attention mask
            return_uncertainty: Whether to return uncertainty estimates
            
        Returns:
            Dictionary containing:
                - predictions: (batch_size, n_horizons)
                - uncertainties: (batch_size, n_horizons) if return_uncertainty
                - trend_logits: (batch_size, 3)
                - encoded: (batch_size, seq_len, d_model)
        """
        # Encode
        encoded = self.encode(x, mask)
        
        # Decode
        decoded = self.decode(encoded, mask)
        
        # Global pooling
        pooled = self.global_pool(decoded.transpose(1, 2)).squeeze(-1)
        
        # Multi-horizon predictions
        predictions = []
        uncertainties = []
        
        for i, head in enumerate(self.prediction_heads):
            pred = head(pooled)
            predictions.append(pred)
            
            if return_uncertainty:
                log_var = self.uncertainty_heads[i](pooled)
                uncertainties.append(log_var)
        
        predictions = torch.cat(predictions, dim=-1)
        
        # Trend classification
        trend_logits = self.trend_head(pooled)
        
        output = {
            "predictions": predictions,
            "trend_logits": trend_logits,
            "encoded": encoded
        }
        
        if return_uncertainty:
            output["uncertainties"] = torch.cat(uncertainties, dim=-1)
        
        return output


class YieldPredictor:
    """
    Main interface for yield prediction.
    
    Handles model loading, inference, and result formatting.
    """
    
    HORIZONS = ["1h", "24h", "7d", "30d"]
    MODEL_VERSION = "1.0.0"
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict] = None,
        device: str = "auto"
    ):
        """
        Initialize the yield predictor.
        
        Args:
            model_path: Path to trained model weights
            config: Configuration dictionary (loads from file if not provided)
            device: Device to use for inference
        """
        self.config = config or load_config()
        self.logger = setup_logging("YieldPredictor")
        self.device = get_device(device)
        
        # Get model configuration
        model_config = self.config.get("yield_predictor", {}).get("model", {})
        
        # Number of input features
        features_config = self.config.get("yield_predictor", {}).get("features", {})
        n_features = (
            len(features_config.get("ts_features", [])) +
            len(features_config.get("static_features", [])) +
            len(features_config.get("market_features", [])) +
            len(features_config.get("derived_features", []))
        )
        
        # Initialize model
        self.model = YieldTransformer(
            n_features=n_features,
            d_model=model_config.get("d_model", 128),
            n_heads=model_config.get("n_heads", 8),
            n_encoder_layers=model_config.get("n_encoder_layers", 4),
            n_decoder_layers=model_config.get("n_decoder_layers", 2),
            d_ff=model_config.get("d_ff", 512),
            n_horizons=len(self.HORIZONS),
            dropout=model_config.get("dropout", 0.1),
            max_seq_len=model_config.get("max_seq_len", 168)
        )
        
        # Load weights if provided
        if model_path:
            self.load(model_path)
        else:
            self.logger.warning("No model weights provided. Using random initialization.")
        
        self.model.to(self.device)
        self.model.eval()
        
        # Normalization parameters (loaded with model or computed from data)
        self.normalization_params = None
    
    def load(self, path: str):
        """Load model weights from file."""
        self.logger.info(f"Loading model weights from {path}")
        
        checkpoint = torch.load(path, map_location=self.device)
        
        if "model_state_dict" in checkpoint:
            self.model.load_state_dict(checkpoint["model_state_dict"])
            self.normalization_params = checkpoint.get("normalization_params")
        else:
            self.model.load_state_dict(checkpoint)
        
        self.logger.success("Model weights loaded successfully")
    
    def save(self, path: str):
        """Save model weights to file."""
        self.logger.info(f"Saving model weights to {path}")
        
        checkpoint = {
            "model_state_dict": self.model.state_dict(),
            "normalization_params": self.normalization_params,
            "config": self.config,
            "version": self.MODEL_VERSION
        }
        
        torch.save(checkpoint, path)
        self.logger.success("Model weights saved successfully")
    
    def preprocess(
        self, 
        data: Dict[str, Any],
        normalize: bool = True
    ) -> Tensor:
        """
        Preprocess input data for model inference.
        
        Args:
            data: Dictionary containing time-series data and metadata
            normalize: Whether to apply normalization
            
        Returns:
            Preprocessed tensor of shape (1, seq_len, n_features)
        """
        # Extract features in the correct order
        features_config = self.config.get("yield_predictor", {}).get("features", {})
        
        feature_list = []
        
        # Time series features
        for feat in features_config.get("ts_features", []):
            if feat in data:
                feature_list.append(np.array(data[feat]).reshape(-1, 1))
        
        # Static features (broadcast across sequence)
        static_features = []
        for feat in features_config.get("static_features", []):
            if feat in data:
                static_features.append(data[feat])
        
        # Market features (broadcast across sequence)
        market_features = []
        for feat in features_config.get("market_features", []):
            if feat in data:
                market_features.append(data[feat])
        
        # Derived features
        for feat in features_config.get("derived_features", []):
            if feat in data:
                feature_list.append(np.array(data[feat]).reshape(-1, 1))
        
        # Combine features
        if feature_list:
            features = np.concatenate(feature_list, axis=1)
        else:
            raise ValueError("No valid features found in input data")
        
        # Add static and market features
        if static_features or market_features:
            static_array = np.array(static_features + market_features)
            # Broadcast across sequence length
            static_tiled = np.tile(static_array, (features.shape[0], 1))
            features = np.concatenate([features, static_tiled], axis=1)
        
        # Normalize if parameters are available
        if normalize and self.normalization_params is not None:
            features = self._apply_normalization(features)
        
        # Convert to tensor
        tensor = torch.tensor(features, dtype=torch.float32)
        
        # Add batch dimension
        tensor = tensor.unsqueeze(0)
        
        return tensor.to(self.device)
    
    def _apply_normalization(self, features: np.ndarray) -> np.ndarray:
        """Apply normalization using stored parameters."""
        if self.normalization_params is None:
            return features
        
        mean = self.normalization_params.get("mean", 0)
        std = self.normalization_params.get("std", 1)
        
        return (features - mean) / (std + 1e-8)
    
    @torch.no_grad()
    def predict(
        self,
        pool_id: str,
        data: Optional[Dict[str, Any]] = None,
        preprocessed: Optional[Tensor] = None,
        return_confidence: bool = True
    ) -> YieldPrediction:
        """
        Make yield predictions for a pool.
        
        Args:
            pool_id: Identifier for the pool/strategy
            data: Raw input data (will be preprocessed)
            preprocessed: Pre-processed input tensor (skips preprocessing)
            return_confidence: Whether to compute confidence intervals
            
        Returns:
            YieldPrediction object with predictions and metadata
        """
        # Get input tensor
        if preprocessed is not None:
            x = preprocessed
        elif data is not None:
            x = self.preprocess(data)
        else:
            raise ValueError("Either 'data' or 'preprocessed' must be provided")
        
        # Run inference
        output = self.model(x, return_uncertainty=return_confidence)
        
        # Extract predictions
        predictions = output["predictions"].cpu().numpy().flatten()
        
        # Process uncertainties into confidence intervals
        confidence_intervals = {}
        if return_confidence and "uncertainties" in output:
            uncertainties = output["uncertainties"].cpu().numpy().flatten()
            for i, horizon in enumerate(self.HORIZONS):
                std = np.exp(0.5 * uncertainties[i])
                confidence_intervals[horizon] = (
                    float(predictions[i] - 1.96 * std),
                    float(predictions[i] + 1.96 * std)
                )
        
        # Determine trend
        trend_logits = output["trend_logits"].cpu().numpy().flatten()
        trend_idx = np.argmax(trend_logits)
        trend_map = {0: "up", 1: "stable", 2: "down"}
        trend = trend_map[trend_idx]
        
        # Check for anomalies
        anomaly_detected = False
        if data is not None and "apy" in data:
            current_apy = data["apy"][-1] if isinstance(data["apy"], (list, np.ndarray)) else data["apy"]
            # Anomaly if predicted change is > 3 standard deviations
            for i, horizon in enumerate(self.HORIZONS[:2]):  # Check short-term
                if horizon in confidence_intervals:
                    lower, upper = confidence_intervals[horizon]
                    if current_apy < lower or current_apy > upper:
                        anomaly_detected = True
                        break
        
        # Format predictions
        predictions_dict = {
            horizon: float(predictions[i]) 
            for i, horizon in enumerate(self.HORIZONS)
        }
        
        return YieldPrediction(
            pool_id=pool_id,
            predictions=predictions_dict,
            confidence_intervals=confidence_intervals,
            trend=trend,
            anomaly_detected=anomaly_detected,
            timestamp=datetime.utcnow().isoformat(),
            model_version=self.MODEL_VERSION
        )
    
    def predict_batch(
        self,
        pool_ids: List[str],
        data_list: List[Dict[str, Any]]
    ) -> List[YieldPrediction]:
        """
        Make predictions for multiple pools.
        
        Args:
            pool_ids: List of pool identifiers
            data_list: List of input data dictionaries
            
        Returns:
            List of YieldPrediction objects
        """
        results = []
        
        for pool_id, data in zip(pool_ids, data_list):
            try:
                pred = self.predict(pool_id, data=data)
                results.append(pred)
            except Exception as e:
                self.logger.error(f"Prediction failed for {pool_id}: {e}")
        
        return results
    
    def to_dict(self, prediction: YieldPrediction) -> Dict[str, Any]:
        """Convert prediction to dictionary for API response."""
        return {
            "pool_id": prediction.pool_id,
            "predictions": prediction.predictions,
            "confidence_intervals": prediction.confidence_intervals,
            "trend": prediction.trend,
            "anomaly_detected": prediction.anomaly_detected,
            "timestamp": prediction.timestamp,
            "model_version": prediction.model_version
        }


# =============================================================================
# Training Utilities
# =============================================================================

class YieldLoss(nn.Module):
    """
    Custom loss function for yield prediction.
    
    Combines:
    - MSE loss for point predictions
    - NLL loss for uncertainty estimation
    - Cross-entropy loss for trend classification
    """
    
    def __init__(
        self,
        prediction_weight: float = 1.0,
        uncertainty_weight: float = 0.5,
        trend_weight: float = 0.2
    ):
        super().__init__()
        self.prediction_weight = prediction_weight
        self.uncertainty_weight = uncertainty_weight
        self.trend_weight = trend_weight
        self.mse = nn.MSELoss()
        self.ce = nn.CrossEntropyLoss()
    
    def forward(
        self,
        predictions: Tensor,
        targets: Tensor,
        uncertainties: Optional[Tensor] = None,
        trend_logits: Optional[Tensor] = None,
        trend_targets: Optional[Tensor] = None
    ) -> Dict[str, Tensor]:
        """
        Compute loss.
        
        Args:
            predictions: Predicted values (batch_size, n_horizons)
            targets: Target values (batch_size, n_horizons)
            uncertainties: Log variance predictions (batch_size, n_horizons)
            trend_logits: Trend classification logits (batch_size, 3)
            trend_targets: Trend targets (batch_size,)
            
        Returns:
            Dictionary with total loss and individual components
        """
        # Prediction loss
        pred_loss = self.mse(predictions, targets)
        
        total_loss = self.prediction_weight * pred_loss
        losses = {"prediction_loss": pred_loss}
        
        # Uncertainty loss (negative log-likelihood)
        if uncertainties is not None:
            # NLL: 0.5 * (log_var + (target - pred)^2 / var)
            nll = 0.5 * (
                uncertainties + 
                (targets - predictions) ** 2 / (torch.exp(uncertainties) + 1e-8)
            )
            unc_loss = nll.mean()
            total_loss = total_loss + self.uncertainty_weight * unc_loss
            losses["uncertainty_loss"] = unc_loss
        
        # Trend classification loss
        if trend_logits is not None and trend_targets is not None:
            trend_loss = self.ce(trend_logits, trend_targets)
            total_loss = total_loss + self.trend_weight * trend_loss
            losses["trend_loss"] = trend_loss
        
        losses["total_loss"] = total_loss
        
        return losses