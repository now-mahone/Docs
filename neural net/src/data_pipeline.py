# Created: 2026-02-19
"""
Kerne Data Pipeline - Feature Engineering and Data Management
==============================================================

Handles data fetching, feature engineering, and preparation for
the neural net models. Integrates with yield-server database
and external data sources.
"""

import os
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
import json

import numpy as np
import pandas as pd

from .utils import load_config, setup_logging


@dataclass
class FeatureSet:
    """Container for prepared features."""
    pool_id: str
    ts_features: np.ndarray  # Time series features (seq_len, n_features)
    static_features: np.ndarray  # Static features
    market_features: np.ndarray  # Market features
    timestamps: np.ndarray  # Timestamps for each observation
    target: Optional[np.ndarray] = None  # Target values for training


class DataPipeline:
    """
    Data pipeline for neural net models.
    
    Handles:
    - Database connections
    - Feature engineering
    - Data normalization
    - Caching
    """
    
    def __init__(
        self,
        config: Optional[Dict] = None,
        cache_enabled: bool = True
    ):
        """
        Initialize the data pipeline.
        
        Args:
            config: Configuration dictionary
            cache_enabled: Whether to use Redis caching
        """
        self.config = config or load_config()
        self.logger = setup_logging("DataPipeline")
        
        # Database connection
        self._db_conn = None
        self._redis_client = None
        self.cache_enabled = cache_enabled
        
        # Feature configuration
        self.pipeline_config = self.config.get("data_pipeline", {})
        self.feature_windows = self.pipeline_config.get("feature_windows", {})
        self.quality_config = self.pipeline_config.get("quality", {})
        
        # Normalization parameters
        self._normalization_params = {}
    
    def _get_db_connection(self):
        """Get database connection (lazy)."""
        if self._db_conn is not None:
            return self._db_conn
        
        try:
            import psycopg2
            from psycopg2.extras import RealDictCursor
            
            db_config = self.pipeline_config.get("database", {})
            
            self._db_conn = psycopg2.connect(
                host=db_config.get("host", "localhost"),
                port=db_config.get("port", 5432),
                database=db_config.get("name", "kerne"),
                user=db_config.get("user", "postgres"),
                password=db_config.get("password", ""),
                cursor_factory=RealDictCursor
            )
            
            self.logger.info("Database connection established")
            return self._db_conn
            
        except ImportError:
            self.logger.warning("psycopg2 not available. Database features disabled.")
            return None
        except Exception as e:
            self.logger.error(f"Database connection failed: {e}")
            return None
    
    def _get_redis_client(self):
        """Get Redis client (lazy)."""
        if self._redis_client is not None:
            return self._redis_client
        
        if not self.cache_enabled:
            return None
        
        try:
            import redis
            
            redis_config = self.pipeline_config.get("redis", {})
            
            self._redis_client = redis.Redis(
                host=redis_config.get("host", "localhost"),
                port=redis_config.get("port", 6379),
                db=redis_config.get("db", 0),
                decode_responses=True
            )
            
            # Test connection
            self._redis_client.ping()
            self.logger.info("Redis connection established")
            return self._redis_client
            
        except ImportError:
            self.logger.warning("redis not available. Caching disabled.")
            return None
        except Exception as e:
            self.logger.warning(f"Redis connection failed: {e}")
            return None
    
    def fetch_yield_history(
        self,
        pool_id: str,
        lookback_days: int = 90,
        interval: str = "1h"
    ) -> pd.DataFrame:
        """
        Fetch historical yield data for a pool.
        
        Args:
            pool_id: Pool identifier (configID)
            lookback_days: Number of days to look back
            interval: Data interval ("1h", "24h")
            
        Returns:
            DataFrame with yield history
        """
        cache_key = f"yield_history:{pool_id}:{lookback_days}:{interval}"
        
        # Check cache
        redis = self._get_redis_client()
        if redis:
            cached = redis.get(cache_key)
            if cached:
                self.logger.debug(f"Cache hit for {cache_key}")
                return pd.read_json(cached)
        
        # Fetch from database
        db = self._get_db_connection()
        if db is None:
            return self._generate_synthetic_data(pool_id, lookback_days)
        
        try:
            query = """
                SELECT 
                    timestamp,
                    "tvlUsd" as tvl_usd,
                    apy,
                    "apyBase" as apy_base,
                    "apyReward" as apy_reward,
                    "il7d",
                    "apyBase7d" as apy_base_7d,
                    "volumeUsd1d" as volume_usd_1d
                FROM yield
                WHERE "configID" = %s
                AND timestamp >= NOW() - INTERVAL '%s days'
                ORDER BY timestamp ASC
            """
            
            df = pd.read_sql(query, db, params=(pool_id, lookback_days))
            
            # Cache result
            if redis and not df.empty:
                redis.setex(cache_key, 3600, df.to_json())  # 1 hour TTL
            
            return df
            
        except Exception as e:
            self.logger.error(f"Database query failed: {e}")
            return self._generate_synthetic_data(pool_id, lookback_days)
    
    def _generate_synthetic_data(
        self,
        pool_id: str,
        lookback_days: int
    ) -> pd.DataFrame:
        """Generate synthetic data for testing/fallback."""
        self.logger.warning(f"Generating synthetic data for {pool_id}")
        
        # Generate timestamps
        hours = lookback_days * 24
        timestamps = pd.date_range(
            end=datetime.utcnow(),
            periods=hours,
            freq="H"
        )
        
        # Generate synthetic yield data
        np.random.seed(hash(pool_id) % 2**32)
        
        base_apy = np.random.uniform(0.03, 0.15)
        trend = np.linspace(0, np.random.uniform(-0.02, 0.02), hours)
        noise = np.random.normal(0, 0.005, hours)
        apy = base_apy + trend + noise
        apy = np.maximum(apy, 0.001)  # Ensure positive
        
        base_tvl = np.random.uniform(1e6, 1e9)
        tvl_trend = np.linspace(0, np.random.uniform(-0.2, 0.5), hours)
        tvl = base_tvl * (1 + tvl_trend)
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "tvl_usd": tvl,
            "apy": apy,
            "apy_base": apy * np.random.uniform(0.5, 0.8),
            "apy_reward": apy * np.random.uniform(0.2, 0.5),
            "il7d": np.random.uniform(0, 0.01, hours),
            "apy_base_7d": apy * np.random.uniform(0.4, 0.7),
            "volume_usd_1d": tvl * np.random.uniform(0.01, 0.1, hours)
        })
    
    def fetch_market_data(
        self,
        lookback_days: int = 90
    ) -> pd.DataFrame:
        """
        Fetch market data (ETH price, gas, etc.).
        
        Args:
            lookback_days: Number of days to look back
            
        Returns:
            DataFrame with market data
        """
        cache_key = f"market_data:{lookback_days}"
        
        # Check cache
        redis = self._get_redis_client()
        if redis:
            cached = redis.get(cache_key)
            if cached:
                return pd.read_json(cached)
        
        # Try to fetch from external APIs
        try:
            # Fetch ETH price from CoinGecko
            days = min(lookback_days, 90)  # CoinGecko free API limit
            
            import requests
            
            response = requests.get(
                "https://api.coingecko.com/api/v3/coins/ethereum/market_chart",
                params={"vs_currency": "usd", "days": days, "interval": "hourly"},
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                prices = data.get("prices", [])
                
                df = pd.DataFrame(prices, columns=["timestamp_ms", "eth_price"])
                df["timestamp"] = pd.to_datetime(df["timestamp_ms"], unit="ms")
                df = df.drop("timestamp_ms", axis=1)
                
                # Calculate volatility
                df["eth_return"] = df["eth_price"].pct_change()
                df["eth_volatility_24h"] = df["eth_return"].rolling(24).std() * np.sqrt(365)
                
                # Add placeholder for funding rate
                df["funding_rate"] = 0.0001  # Placeholder
                
                # Add placeholder for gas
                df["gas_price"] = 30  # Gwei placeholder
                
                # Cache
                if redis:
                    redis.setex(cache_key, 300, df.to_json())  # 5 min TTL
                
                return df
            
        except Exception as e:
            self.logger.warning(f"Market data fetch failed: {e}")
        
        # Generate synthetic market data
        return self._generate_synthetic_market_data(lookback_days)
    
    def _generate_synthetic_market_data(self, lookback_days: int) -> pd.DataFrame:
        """Generate synthetic market data for testing."""
        hours = lookback_days * 24
        timestamps = pd.date_range(
            end=datetime.utcnow(),
            periods=hours,
            freq="H"
        )
        
        # Generate ETH price with random walk
        np.random.seed(42)
        returns = np.random.normal(0.0001, 0.02, hours)
        price = 2500 * np.exp(np.cumsum(returns))
        
        return pd.DataFrame({
            "timestamp": timestamps,
            "eth_price": price,
            "eth_volatility_24h": np.abs(np.random.normal(0.5, 0.2, hours)),
            "funding_rate": np.random.normal(0.0001, 0.0002, hours),
            "gas_price": np.random.uniform(10, 100, hours)
        })
    
    def compute_derived_features(
        self,
        df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Compute derived features from raw data.
        
        Args:
            df: DataFrame with raw yield data
            
        Returns:
            DataFrame with additional derived features
        """
        df = df.copy()
        
        # Moving averages
        df["apy_ma_7d"] = df["apy"].rolling(7 * 24, min_periods=1).mean()
        df["apy_ma_30d"] = df["apy"].rolling(30 * 24, min_periods=1).mean()
        
        # Volatility
        df["apy_volatility"] = df["apy"].rolling(7 * 24, min_periods=1).std()
        
        # TVL changes
        df["tvl_change_24h"] = df["tvl_usd"].pct_change(24)
        df["tvl_change_7d"] = df["tvl_usd"].pct_change(7 * 24)
        
        # Yield trend (linear regression slope over 7 days)
        window = 7 * 24
        if len(df) >= window:
            x = np.arange(window)
            df["yield_trend"] = df["apy"].rolling(window).apply(
                lambda y: np.polyfit(x, y, 1)[0] if len(y) == window else 0,
                raw=False
            )
        else:
            df["yield_trend"] = 0
        
        # Fill NaN values
        df = df.fillna(method="bfill").fillna(method="ffill").fillna(0)
        
        return df
    
    def prepare_features(
        self,
        pool_id: str,
        lookback_days: Optional[int] = None,
        include_target: bool = False,
        target_horizon: int = 24  # Hours ahead for target
    ) -> FeatureSet:
        """
        Prepare complete feature set for a pool.
        
        Args:
            pool_id: Pool identifier
            lookback_days: Number of days to look back
            include_target: Whether to include target values
            target_horizon: Hours ahead for target prediction
            
        Returns:
            FeatureSet with all features prepared
        """
        lookback_days = lookback_days or self.feature_windows.get("lookback_days", 90)
        
        # Fetch data
        yield_df = self.fetch_yield_history(pool_id, lookback_days)
        market_df = self.fetch_market_data(lookback_days)
        
        # Compute derived features
        yield_df = self.compute_derived_features(yield_df)
        
        # Merge with market data
        yield_df["timestamp"] = pd.to_datetime(yield_df["timestamp"])
        market_df["timestamp"] = pd.to_datetime(market_df["timestamp"])
        
        df = pd.merge_asof(
            yield_df.sort_values("timestamp"),
            market_df.sort_values("timestamp"),
            on="timestamp",
            direction="nearest"
        )
        
        # Extract features
        features_config = self.config.get("yield_predictor", {}).get("features", {})
        
        # Time series features
        ts_feature_names = features_config.get("ts_features", [])
        derived_feature_names = features_config.get("derived_features", [])
        
        all_ts_features = ts_feature_names + derived_feature_names
        ts_features = df[all_ts_features].values
        
        # Static features (would come from protocol metadata)
        static_feature_names = features_config.get("static_features", [])
        static_features = np.zeros(len(static_feature_names))  # Placeholder
        
        # Market features
        market_feature_names = features_config.get("market_features", [])
        market_features = df[market_feature_names].values[-1] if not df.empty else np.zeros(len(market_feature_names))
        
        # Timestamps
        timestamps = df["timestamp"].values
        
        # Target (for training)
        target = None
        if include_target:
            # Target is APY at horizon hours ahead
            target = df["apy"].shift(-target_horizon).values
        
        return FeatureSet(
            pool_id=pool_id,
            ts_features=ts_features,
            static_features=static_features,
            market_features=market_features,
            timestamps=timestamps,
            target=target
        )
    
    def prepare_training_data(
        self,
        pool_ids: List[str],
        seq_length: int = 168,  # 7 days of hourly data
        horizon: int = 24,
        lookback_days: int = 90
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare training data for multiple pools.
        
        Args:
            pool_ids: List of pool identifiers
            seq_length: Sequence length for input
            horizon: Prediction horizon
            lookback_days: Days of history to use
            
        Returns:
            Tuple of (X, y) arrays
        """
        X_list = []
        y_list = []
        
        for pool_id in pool_ids:
            try:
                features = self.prepare_features(
                    pool_id,
                    lookback_days=lookback_days,
                    include_target=True,
                    target_horizon=horizon
                )
                
                # Create sequences
                ts = features.ts_features
                target = features.target
                
                for i in range(len(ts) - seq_length - horizon):
                    X_list.append(ts[i:i + seq_length])
                    y_list.append(target[i + seq_length])
                    
            except Exception as e:
                self.logger.error(f"Failed to prepare data for {pool_id}: {e}")
        
        if not X_list:
            raise ValueError("No training data could be prepared")
        
        X = np.array(X_list)
        y = np.array(y_list)
        
        # Normalize
        X, params = self._normalize_features(X)
        self._normalization_params = params
        
        return X, y
    
    def _normalize_features(
        self,
        X: np.ndarray
    ) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """
        Normalize features.
        
        Args:
            X: Feature array of shape (n_samples, seq_len, n_features)
            
        Returns:
            Tuple of (normalized_X, params)
        """
        # Compute statistics across all samples and timesteps
        X_flat = X.reshape(-1, X.shape[-1])
        
        mean = np.mean(X_flat, axis=0)
        std = np.std(X_flat, axis=0) + 1e-8
        
        # Normalize
        X_normalized = (X - mean) / std
        
        params = {
            "mean": mean,
            "std": std
        }
        
        return X_normalized, params
    
    def get_protocol_metadata(
        self,
        protocol: str,
        chain: str
    ) -> Dict[str, Any]:
        """
        Get protocol metadata for risk scoring.
        
        Args:
            protocol: Protocol name
            chain: Chain name
            
        Returns:
            Dictionary of protocol metadata
        """
        cache_key = f"protocol_metadata:{protocol}:{chain}"
        
        # Check cache
        redis = self._get_redis_client()
        if redis:
            cached = redis.get(cache_key)
            if cached:
                return json.loads(cached)
        
        # Default metadata (would be fetched from database or API)
        metadata = {
            "protocol": protocol,
            "chain": chain,
            "audit_count": 1,
            "audit_quality_score": 70,
            "days_since_audit": 180,
            "bug_bounty_size": 50000,
            "code_complexity_score": 50,
            "upgradeable": True,
            "admin_key_timelock": 24,
            "team_doxxed": True,
            "team_reputation_score": 70,
            "multisig_threshold": 3,
            "governance_decentralization": 60,
            "tvl_usd": 100000000,
            "tvl_stability": 0.1,
            "liquidity_depth": 80,
            "slippage_1m": 0.005,
            "withdrawal_time": 3600,
            "yield_volatility": 0.15,
            "yield_sustainability": 70,
            "correlation_eth": 0.5,
            "correlation_btc": 0.3,
            "bridge_dependency": False,
            "oracle_dependency": 1,
            "protocol_interconnections": 5,
            "tvl_concentration": 0.3,
            "whale_percentage": 0.2,
            "protocol_tvl_share": 0.01
        }
        
        # Cache
        if redis:
            redis.setex(cache_key, 3600, json.dumps(metadata))
        
        return metadata
    
    def close(self):
        """Close database and Redis connections."""
        if self._db_conn:
            self._db_conn.close()
            self._db_conn = None
        
        if self._redis_client:
            self._redis_client.close()
            self._redis_client = None