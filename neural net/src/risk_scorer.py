# Created: 2026-02-19
"""
Kerne Risk Scorer - Ensemble Model for Protocol Risk Assessment
================================================================

Gradient Boosting Ensemble model for scoring risk of DeFi protocols.
Outputs a risk score 0-100 (100 = safest) with factor breakdowns.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import json

import numpy as np

from .utils import load_config, setup_logging


@dataclass
class RiskScore:
    """Container for risk score results."""
    protocol: str
    chain: str
    score: int  # 0-100, 100 = safest
    category: str  # excellent, good, moderate, acceptable, poor, critical
    factors: Dict[str, float]  # Individual factor scores
    alerts: List[str]  # Risk alerts
    allocation_cap: float  # Maximum recommended allocation
    timestamp: str
    model_version: str


@dataclass
class RiskFactor:
    """Definition of a risk factor."""
    name: str
    weight: float
    features: List[str]
    description: str = ""


class RiskScorer:
    """
    Ensemble-based risk scoring for DeFi protocols.
    
    Uses XGBoost, LightGBM, and CatBoost in an ensemble configuration
    to produce robust risk scores.
    """
    
    MODEL_VERSION = "1.0.0"
    
    # Risk categories and thresholds
    CATEGORIES = {
        "excellent": (90, 100),
        "good": (80, 89),
        "moderate": (70, 79),
        "acceptable": (50, 69),
        "poor": (30, 49),
        "critical": (0, 29)
    }
    
    # Allocation caps by category
    ALLOCATION_CAPS = {
        "excellent": 0.15,
        "good": 0.10,
        "moderate": 0.05,
        "acceptable": 0.02,
        "poor": 0.01,
        "critical": 0.0
    }
    
    def __init__(
        self,
        model_path: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        """
        Initialize the risk scorer.
        
        Args:
            model_path: Path to saved model directory
            config: Configuration dictionary
        """
        self.config = config or load_config()
        self.logger = setup_logging("RiskScorer")
        
        # Load risk factor definitions
        self.risk_factors = self._load_risk_factors()
        
        # Initialize models (lazy loading)
        self._models = None
        self._model_path = model_path
        self._feature_names = self._build_feature_names()
        
        # Feature statistics for normalization
        self._feature_stats = None
    
    def _load_risk_factors(self) -> Dict[str, RiskFactor]:
        """Load risk factor definitions from config."""
        factors_config = self.config.get("risk_scorer", {}).get("risk_factors", {})
        
        factors = {}
        for factor_name, factor_data in factors_config.items():
            factors[factor_name] = RiskFactor(
                name=factor_name,
                weight=factor_data.get("weight", 0.1),
                features=factor_data.get("features", []),
                description=factor_data.get("description", "")
            )
        
        return factors
    
    def _build_feature_names(self) -> List[str]:
        """Build ordered list of all feature names."""
        features = []
        for factor in self.risk_factors.values():
            features.extend(factor.features)
        return features
    
    def _load_models(self):
        """Lazy load the ensemble models."""
        if self._models is not None:
            return
        
        self._models = {}
        
        try:
            import xgboost as xgb
            import lightgbm as lgb
            
            # Try to load pre-trained models
            if self._model_path:
                import os
                from pathlib import Path
                
                model_dir = Path(self._model_path)
                
                # Load XGBoost
                xgb_path = model_dir / "xgboost_model.json"
                if xgb_path.exists():
                    self._models["xgboost"] = xgb.Booster()
                    self._models["xgboost"].load_model(str(xgb_path))
                    self.logger.info("Loaded XGBoost model")
                
                # Load LightGBM
                lgb_path = model_dir / "lightgbm_model.txt"
                if lgb_path.exists():
                    self._models["lightgbm"] = lgb.Booster(model_file=str(lgb_path))
                    self.logger.info("Loaded LightGBM model")
                
                # Load feature statistics
                stats_path = model_dir / "feature_stats.json"
                if stats_path.exists():
                    with open(stats_path, "r") as f:
                        self._feature_stats = json.load(f)
            
            # If no models loaded, create default models
            if not self._models:
                self.logger.warning("No pre-trained models found. Using rule-based scoring.")
                self._models = None
            
        except ImportError as e:
            self.logger.warning(f"ML libraries not available: {e}. Using rule-based scoring.")
            self._models = None
    
    def _preprocess_features(
        self, 
        data: Dict[str, Any]
    ) -> Tuple[np.ndarray, Dict[str, float]]:
        """
        Preprocess input data into feature vector.
        
        Args:
            data: Dictionary containing protocol metrics
            
        Returns:
            Tuple of (feature_vector, factor_scores)
        """
        # Extract features in order
        features = []
        missing_features = []
        
        for feat in self._feature_names:
            if feat in data:
                val = data[feat]
                if isinstance(val, bool):
                    val = 1.0 if val else 0.0
                elif val is None:
                    val = 0.0
                features.append(float(val))
            else:
                features.append(0.0)
                missing_features.append(feat)
        
        if missing_features:
            self.logger.debug(f"Missing features (set to 0): {missing_features[:5]}...")
        
        feature_vector = np.array(features).reshape(1, -1)
        
        # Normalize if statistics available
        if self._feature_stats is not None:
            mean = np.array(self._feature_stats.get("mean", [0] * len(features)))
            std = np.array(self._feature_stats.get("std", [1] * len(features)))
            feature_vector = (feature_vector - mean) / (std + 1e-8)
        
        # Compute factor scores
        factor_scores = self._compute_factor_scores(data)
        
        return feature_vector, factor_scores
    
    def _compute_factor_scores(self, data: Dict[str, Any]) -> Dict[str, float]:
        """
        Compute individual factor scores.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Dictionary mapping factor name to score (0-100)
        """
        factor_scores = {}
        
        for factor_name, factor in self.risk_factors.items():
            score = self._score_factor(factor, data)
            factor_scores[factor_name] = score
        
        return factor_scores
    
    def _score_factor(self, factor: RiskFactor, data: Dict[str, Any]) -> float:
        """
        Score a single risk factor.
        
        Args:
            factor: Risk factor definition
            data: Input data
            
        Returns:
            Factor score (0-100)
        """
        scores = []
        
        for feature in factor.features:
            if feature not in data:
                continue
            
            val = data[feature]
            if val is None:
                continue
            
            # Feature-specific scoring logic
            score = self._score_feature(feature, val)
            if score is not None:
                scores.append(score)
        
        if not scores:
            return 50.0  # Default neutral score
        
        return np.mean(scores)
    
    def _score_feature(self, feature: str, value: Any) -> Optional[float]:
        """
        Score an individual feature.
        
        Args:
            feature: Feature name
            value: Feature value
            
        Returns:
            Feature score (0-100) or None if not scorable
        """
        # Smart contract risk features
        if feature == "audit_count":
            if value >= 3:
                return 100.0
            elif value == 2:
                return 85.0
            elif value == 1:
                return 70.0
            else:
                return 30.0
        
        if feature == "audit_quality_score":
            # Assume value is already 0-100
            return float(value)
        
        if feature == "days_since_audit":
            if value <= 90:
                return 100.0
            elif value <= 180:
                return 85.0
            elif value <= 365:
                return 70.0
            else:
                return 50.0
        
        if feature == "bug_bounty_size":
            # Value in USD
            if value >= 1000000:
                return 100.0
            elif value >= 500000:
                return 90.0
            elif value >= 100000:
                return 80.0
            elif value >= 50000:
                return 70.0
            elif value > 0:
                return 60.0
            else:
                return 40.0
        
        if feature == "upgradeable":
            return 40.0 if value else 80.0
        
        if feature == "admin_key_timelock":
            if value >= 48:  # hours
                return 90.0
            elif value >= 24:
                return 75.0
            elif value > 0:
                return 50.0
            else:
                return 30.0
        
        # Counterparty risk features
        if feature == "team_doxxed":
            return 80.0 if value else 40.0
        
        if feature == "team_reputation_score":
            return float(value) if 0 <= value <= 100 else 50.0
        
        if feature == "multisig_threshold":
            if value >= 4:
                return 100.0
            elif value >= 3:
                return 85.0
            elif value >= 2:
                return 70.0
            else:
                return 40.0
        
        if feature == "governance_decentralization":
            # 0-100 score
            return float(value)
        
        # Liquidity risk features
        if feature == "tvl_usd":
            if value >= 1000000000:  # $1B+
                return 100.0
            elif value >= 500000000:
                return 95.0
            elif value >= 100000000:
                return 90.0
            elif value >= 50000000:
                return 85.0
            elif value >= 10000000:
                return 75.0
            elif value >= 1000000:
                return 60.0
            else:
                return 40.0
        
        if feature == "tvl_stability":
            # Lower is better (volatility)
            if value <= 0.05:
                return 100.0
            elif value <= 0.1:
                return 90.0
            elif value <= 0.2:
                return 80.0
            elif value <= 0.3:
                return 70.0
            else:
                return 50.0
        
        if feature == "liquidity_depth":
            return float(value) if 0 <= value <= 100 else 50.0
        
        if feature == "slippage_1m":
            # Slippage for $1M trade (lower is better)
            if value <= 0.001:  # 0.1%
                return 100.0
            elif value <= 0.005:  # 0.5%
                return 90.0
            elif value <= 0.01:  # 1%
                return 80.0
            elif value <= 0.02:  # 2%
                return 70.0
            else:
                return 50.0
        
        if feature == "withdrawal_time":
            # In seconds
            if value <= 60:  # 1 minute
                return 100.0
            elif value <= 300:  # 5 minutes
                return 90.0
            elif value <= 3600:  # 1 hour
                return 80.0
            elif value <= 86400:  # 1 day
                return 70.0
            else:
                return 50.0
        
        # Market risk features
        if feature == "yield_volatility":
            # Lower is better
            if value <= 0.05:
                return 100.0
            elif value <= 0.1:
                return 85.0
            elif value <= 0.2:
                return 70.0
            elif value <= 0.5:
                return 50.0
            else:
                return 30.0
        
        if feature == "yield_sustainability":
            return float(value) if 0 <= value <= 100 else 50.0
        
        if feature in ("correlation_eth", "correlation_btc"):
            # Moderate correlation is good
            if 0.3 <= value <= 0.7:
                return 80.0
            elif 0.1 <= value <= 0.9:
                return 70.0
            else:
                return 50.0
        
        # Systemic risk features
        if feature == "bridge_dependency":
            return 60.0 if value else 90.0
        
        if feature == "oracle_dependency":
            if value == 0:
                return 90.0
            elif value == 1:
                return 80.0
            elif value == 2:
                return 70.0
            else:
                return 50.0
        
        if feature == "protocol_interconnections":
            # Number of interconnected protocols
            if value <= 3:
                return 90.0
            elif value <= 5:
                return 80.0
            elif value <= 10:
                return 70.0
            else:
                return 50.0
        
        # Concentration risk features
        if feature == "tvl_concentration":
            # Percentage held by top wallets
            if value <= 0.2:
                return 100.0
            elif value <= 0.3:
                return 85.0
            elif value <= 0.5:
                return 70.0
            else:
                return 50.0
        
        if feature == "whale_percentage":
            if value <= 0.1:
                return 100.0
            elif value <= 0.2:
                return 85.0
            elif value <= 0.3:
                return 70.0
            else:
                return 50.0
        
        if feature == "protocol_tvl_share":
            # Our share of protocol TVL (lower is better)
            if value <= 0.01:
                return 100.0
            elif value <= 0.05:
                return 90.0
            elif value <= 0.1:
                return 80.0
            elif value <= 0.2:
                return 70.0
            else:
                return 50.0
        
        # Default: return value as-is if numeric
        if isinstance(value, (int, float)) and 0 <= value <= 100:
            return float(value)
        
        return None
    
    def _get_category(self, score: int) -> str:
        """Get risk category from score."""
        for category, (low, high) in self.CATEGORIES.items():
            if low <= score <= high:
                return category
        return "acceptable"
    
    def _generate_alerts(
        self, 
        factor_scores: Dict[str, float],
        data: Dict[str, Any]
    ) -> List[str]:
        """
        Generate risk alerts based on factor scores.
        
        Args:
            factor_scores: Individual factor scores
            data: Original input data
            
        Returns:
            List of alert strings
        """
        alerts = []
        
        # Check for critical factors
        for factor_name, score in factor_scores.items():
            if score < 30:
                alerts.append(f"CRITICAL: {factor_name} risk is very high (score: {score:.0f})")
            elif score < 50:
                alerts.append(f"WARNING: {factor_name} risk is elevated (score: {score:.0f})")
        
        # Check specific conditions
        if data.get("upgradeable", False) and data.get("admin_key_timelock", 0) < 24:
            alerts.append("WARNING: Upgradeable contracts with short/no timelock")
        
        if data.get("audit_count", 0) == 0:
            alerts.append("WARNING: No audits performed")
        
        if data.get("tvl_usd", 0) < 1000000:
            alerts.append("INFO: Low TVL (<$1M) - higher liquidity risk")
        
        if data.get("yield_volatility", 0) > 0.5:
            alerts.append("WARNING: High yield volatility - may be unsustainable")
        
        return alerts
    
    def score(
        self,
        protocol: str,
        chain: str,
        data: Optional[Dict[str, Any]] = None,
        feature_vector: Optional[np.ndarray] = None
    ) -> RiskScore:
        """
        Compute risk score for a protocol.
        
        Args:
            protocol: Protocol name (e.g., "aave-v3")
            chain: Chain name (e.g., "arbitrum")
            data: Dictionary of protocol metrics
            feature_vector: Pre-computed feature vector (skips preprocessing)
            
        Returns:
            RiskScore object with score and breakdown
        """
        # Load models if not already loaded
        self._load_models()
        
        # Get feature vector and factor scores
        if feature_vector is not None:
            features = feature_vector.reshape(1, -1)
            factor_scores = self._compute_factor_scores(data or {})
        elif data is not None:
            features, factor_scores = self._preprocess_features(data)
        else:
            raise ValueError("Either 'data' or 'feature_vector' must be provided")
        
        # Compute ensemble score
        if self._models:
            # Use ML models
            predictions = []
            
            try:
                import xgboost as xgb
                if "xgboost" in self._models:
                    dmatrix = xgb.DMatrix(features)
                    pred = self._models["xgboost"].predict(dmatrix)
                    predictions.append(pred[0])
            except Exception as e:
                self.logger.debug(f"XGBoost prediction failed: {e}")
            
            try:
                import lightgbm as lgb
                if "lightgbm" in self._models:
                    pred = self._models["lightgbm"].predict(features)
                    predictions.append(pred[0])
            except Exception as e:
                self.logger.debug(f"LightGBM prediction failed: {e}")
            
            if predictions:
                # Average ensemble predictions
                raw_score = np.mean(predictions)
                # Scale to 0-100
                score = int(np.clip(raw_score * 100, 0, 100))
            else:
                # Fallback to rule-based
                score = self._rule_based_score(factor_scores)
        else:
            # Rule-based scoring
            score = self._rule_based_score(factor_scores)
        
        # Get category and allocation cap
        category = self._get_category(score)
        allocation_cap = self.ALLOCATION_CAPS[category]
        
        # Generate alerts
        alerts = self._generate_alerts(factor_scores, data or {})
        
        return RiskScore(
            protocol=protocol,
            chain=chain,
            score=score,
            category=category,
            factors=factor_scores,
            alerts=alerts,
            allocation_cap=allocation_cap,
            timestamp=datetime.utcnow().isoformat(),
            model_version=self.MODEL_VERSION
        )
    
    def _rule_based_score(self, factor_scores: Dict[str, float]) -> int:
        """
        Compute rule-based score from factor scores.
        
        Args:
            factor_scores: Dictionary of factor scores
            
        Returns:
            Overall risk score (0-100)
        """
        weighted_sum = 0.0
        total_weight = 0.0
        
        for factor_name, score in factor_scores.items():
            weight = self.risk_factors.get(factor_name, RiskFactor("", 0.1, [])).weight
            weighted_sum += score * weight
            total_weight += weight
        
        if total_weight > 0:
            return int(weighted_sum / total_weight)
        else:
            return 50  # Neutral default
    
    def score_batch(
        self,
        protocols: List[Dict[str, Any]]
    ) -> List[RiskScore]:
        """
        Score multiple protocols.
        
        Args:
            protocols: List of dicts with 'protocol', 'chain', and 'data' keys
            
        Returns:
            List of RiskScore objects
        """
        results = []
        
        for item in protocols:
            try:
                score = self.score(
                    protocol=item["protocol"],
                    chain=item["chain"],
                    data=item.get("data")
                )
                results.append(score)
            except Exception as e:
                self.logger.error(f"Scoring failed for {item.get('protocol', 'unknown')}: {e}")
        
        return results
    
    def to_dict(self, score: RiskScore) -> Dict[str, Any]:
        """Convert risk score to dictionary for API response."""
        return {
            "protocol": score.protocol,
            "chain": score.chain,
            "score": score.score,
            "category": score.category,
            "factors": score.factors,
            "alerts": score.alerts,
            "allocation_cap": score.allocation_cap,
            "timestamp": score.timestamp,
            "model_version": score.model_version
        }
    
    def get_allocation_recommendation(
        self,
        scores: List[RiskScore],
        total_tvl: float,
        constraints: Optional[Dict[str, Any]] = None
    ) -> Dict[str, float]:
        """
        Get allocation recommendations based on risk scores.
        
        Args:
            scores: List of RiskScore objects
            total_tvl: Total TVL to allocate
            constraints: Optional constraints (max_single, min_score, etc.)
            
        Returns:
            Dictionary mapping protocol to recommended allocation
        """
        constraints = constraints or {}
        max_single = constraints.get("max_single", 0.15)
        min_score = constraints.get("min_score", 50)
        
        # Filter by minimum score
        eligible = [s for s in scores if s.score >= min_score]
        
        if not eligible:
            return {}
        
        # Compute weights based on scores
        total_score = sum(s.score for s in eligible)
        
        allocations = {}
        for score in eligible:
            # Weight proportional to score
            weight = score.score / total_score
            
            # Apply allocation cap
            weight = min(weight, max_single, score.allocation_cap)
            
            allocations[f"{score.protocol}_{score.chain}"] = weight * total_tvl
        
        return allocations