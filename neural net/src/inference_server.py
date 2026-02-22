# Created: 2026-02-19
"""
Kerne Neural Net Inference Server
=================================

FastAPI-based inference server for the neural net models.
Provides REST API endpoints for yield prediction, risk scoring,
and allocation optimization.
"""

import os
import sys
from typing import Dict, List, Optional, Any
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .utils import load_config, setup_logging
from .yield_predictor import YieldPredictor
from .risk_scorer import RiskScorer
from .allocation_optimizer import AllocationOptimizer, Strategy
from .data_pipeline import DataPipeline


# =============================================================================
# Configuration
# =============================================================================

config = load_config()
logger = setup_logging("InferenceServer")

# Global model instances
_models: Dict[str, Any] = {}


def get_yield_predictor() -> YieldPredictor:
    """Get or create yield predictor instance."""
    if "yield_predictor" not in _models:
        model_path = config.get("model_registry", {}).get("artifacts", {}).get("yield_predictor")
        _models["yield_predictor"] = YieldPredictor(model_path=model_path, config=config)
    return _models["yield_predictor"]


def get_risk_scorer() -> RiskScorer:
    """Get or create risk scorer instance."""
    if "risk_scorer" not in _models:
        model_path = config.get("model_registry", {}).get("artifacts", {}).get("risk_scorer")
        _models["risk_scorer"] = RiskScorer(model_path=model_path, config=config)
    return _models["risk_scorer"]


def get_allocation_optimizer() -> AllocationOptimizer:
    """Get or create allocation optimizer instance."""
    if "allocation_optimizer" not in _models:
        model_path = config.get("model_registry", {}).get("artifacts", {}).get("allocation_optimizer")
        _models["allocation_optimizer"] = AllocationOptimizer(model_path=model_path, config=config)
    return _models["allocation_optimizer"]


def get_data_pipeline() -> DataPipeline:
    """Get or create data pipeline instance."""
    if "data_pipeline" not in _models:
        _models["data_pipeline"] = DataPipeline(config=config)
    return _models["data_pipeline"]


# =============================================================================
# Lifespan Management
# =============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan."""
    # Startup
    logger.info("Starting Kerne Neural Net Inference Server...")
    
    # Pre-load models
    try:
        get_yield_predictor()
        get_risk_scorer()
        get_allocation_optimizer()
        logger.info("All models loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
    
    yield
    
    # Shutdown
    logger.info("Shutting down inference server...")
    
    # Close connections
    if "data_pipeline" in _models:
        _models["data_pipeline"].close()
    
    _models.clear()


# =============================================================================
# FastAPI App
# =============================================================================

app = FastAPI(
    title="Kerne Neural Net API",
    description="ML-powered predictions for the Yield Routing Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Request/Response Models
# =============================================================================

class YieldPredictRequest(BaseModel):
    """Request for yield prediction."""
    pool_id: str = Field(..., description="Pool identifier (configID)")
    horizon: str = Field("7d", description="Prediction horizon: 1h, 24h, 7d, 30d")
    include_confidence: bool = Field(True, description="Include confidence intervals")


class YieldPredictResponse(BaseModel):
    """Response for yield prediction."""
    pool_id: str
    predictions: Dict[str, float]
    confidence_intervals: Optional[Dict[str, List[float]]] = None
    trend: str
    anomaly_detected: bool
    timestamp: str
    model_version: str


class RiskScoreRequest(BaseModel):
    """Request for risk scoring."""
    protocol: str = Field(..., description="Protocol name (e.g., aave-v3)")
    chain: str = Field(..., description="Chain name (e.g., arbitrum)")
    data: Optional[Dict[str, Any]] = Field(None, description="Protocol metrics")


class RiskScoreResponse(BaseModel):
    """Response for risk scoring."""
    protocol: str
    chain: str
    score: int
    category: str
    factors: Dict[str, float]
    alerts: List[str]
    allocation_cap: float
    timestamp: str
    model_version: str


class StrategyInput(BaseModel):
    """Input for a strategy."""
    id: str
    protocol: str
    chain: str
    asset: str
    current_apy: float
    predicted_apy: float
    risk_score: int
    tvl: float
    max_capacity: float
    current_allocation: float = 0.0


class AllocationRequest(BaseModel):
    """Request for allocation optimization."""
    strategies: List[StrategyInput]
    total_tvl: float
    current_allocations: Optional[Dict[str, float]] = None
    constraints: Optional[Dict[str, Any]] = None


class AllocationResponse(BaseModel):
    """Response for allocation optimization."""
    weights: Dict[str, float]
    expected_apy: float
    expected_risk_score: float
    rebalance_trades: List[Dict[str, Any]]
    gas_estimate: float
    confidence: float
    timestamp: str
    model_version: str


class HealthResponse(BaseModel):
    """Health check response."""
    status: str
    models_loaded: List[str]
    timestamp: str


# =============================================================================
# API Endpoints
# =============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy",
        models_loaded=list(_models.keys()),
        timestamp=datetime.utcnow().isoformat()
    )


@app.post("/predict/yield", response_model=YieldPredictResponse)
async def predict_yield(
    request: YieldPredictRequest,
    predictor: YieldPredictor = Depends(get_yield_predictor),
    pipeline: DataPipeline = Depends(get_data_pipeline)
):
    """
    Predict yield for a pool.
    
    Returns predicted APY for multiple horizons with optional confidence intervals.
    """
    try:
        # Prepare features
        features = pipeline.prepare_features(request.pool_id)
        
        # Make prediction
        prediction = predictor.predict(
            pool_id=request.pool_id,
            data={
                "apy": features.ts_features[:, 0].tolist() if len(features.ts_features) > 0 else [],
                "apy_base": features.ts_features[:, 1].tolist() if features.ts_features.shape[1] > 1 else [],
                "apy_reward": features.ts_features[:, 2].tolist() if features.ts_features.shape[1] > 2 else [],
                "tvl_usd": features.ts_features[:, 3].tolist() if features.ts_features.shape[1] > 3 else [],
                "eth_price": features.market_features[0] if len(features.market_features) > 0 else 2500,
                "eth_volatility_24h": features.market_features[1] if len(features.market_features) > 1 else 0.5,
            },
            return_confidence=request.include_confidence
        )
        
        return YieldPredictResponse(
            pool_id=prediction.pool_id,
            predictions=prediction.predictions,
            confidence_intervals=prediction.confidence_intervals if request.include_confidence else None,
            trend=prediction.trend,
            anomaly_detected=prediction.anomaly_detected,
            timestamp=prediction.timestamp,
            model_version=prediction.model_version
        )
        
    except Exception as e:
        logger.error(f"Yield prediction failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/risk/score", response_model=RiskScoreResponse)
async def score_risk(
    request: RiskScoreRequest,
    scorer: RiskScorer = Depends(get_risk_scorer),
    pipeline: DataPipeline = Depends(get_data_pipeline)
):
    """
    Score risk for a protocol.
    
    Returns risk score (0-100) with factor breakdown and alerts.
    """
    try:
        # Get protocol data if not provided
        data = request.data
        if data is None:
            data = pipeline.get_protocol_metadata(request.protocol, request.chain)
        
        # Score risk
        score = scorer.score(
            protocol=request.protocol,
            chain=request.chain,
            data=data
        )
        
        return RiskScoreResponse(
            protocol=score.protocol,
            chain=score.chain,
            score=score.score,
            category=score.category,
            factors=score.factors,
            alerts=score.alerts,
            allocation_cap=score.allocation_cap,
            timestamp=score.timestamp,
            model_version=score.model_version
        )
        
    except Exception as e:
        logger.error(f"Risk scoring failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/allocate/optimize", response_model=AllocationResponse)
async def optimize_allocation(
    request: AllocationRequest,
    optimizer: AllocationOptimizer = Depends(get_allocation_optimizer)
):
    """
    Optimize capital allocation across strategies.
    
    Returns optimal weights and rebalancing trades.
    """
    try:
        # Convert input to Strategy objects
        strategies = [
            Strategy(
                id=s.id,
                protocol=s.protocol,
                chain=s.chain,
                asset=s.asset,
                current_apy=s.current_apy,
                predicted_apy=s.predicted_apy,
                risk_score=s.risk_score,
                tvl=s.tvl,
                max_capacity=s.max_capacity,
                current_allocation=s.current_allocation
            )
            for s in request.strategies
        ]
        
        # Optimize
        decision = optimizer.optimize(
            strategies=strategies,
            total_tvl=request.total_tvl,
            current_allocations=request.current_allocations,
            constraints=request.constraints
        )
        
        return AllocationResponse(
            weights=decision.weights,
            expected_apy=decision.expected_apy,
            expected_risk_score=decision.expected_risk_score,
            rebalance_trades=decision.rebalance_trades,
            gas_estimate=decision.gas_estimate,
            confidence=decision.confidence,
            timestamp=decision.timestamp,
            model_version=decision.model_version
        )
        
    except Exception as e:
        logger.error(f"Allocation optimization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/batch/predict")
async def batch_predict(
    pool_ids: List[str],
    predictor: YieldPredictor = Depends(get_yield_predictor),
    pipeline: DataPipeline = Depends(get_data_pipeline)
):
    """
    Batch yield prediction for multiple pools.
    """
    results = []
    
    for pool_id in pool_ids:
        try:
            features = pipeline.prepare_features(pool_id)
            prediction = predictor.predict(
                pool_id=pool_id,
                data={
                    "apy": features.ts_features[:, 0].tolist() if len(features.ts_features) > 0 else [],
                }
            )
            results.append(predictor.to_dict(prediction))
        except Exception as e:
            results.append({
                "pool_id": pool_id,
                "error": str(e)
            })
    
    return {"results": results}


@app.post("/batch/risk")
async def batch_risk(
    protocols: List[Dict[str, str]],
    scorer: RiskScorer = Depends(get_risk_scorer),
    pipeline: DataPipeline = Depends(get_data_pipeline)
):
    """
    Batch risk scoring for multiple protocols.
    """
    results = []
    
    for item in protocols:
        try:
            data = pipeline.get_protocol_metadata(
                item.get("protocol", ""),
                item.get("chain", "")
            )
            score = scorer.score(
                protocol=item.get("protocol", ""),
                chain=item.get("chain", ""),
                data=data
            )
            results.append(scorer.to_dict(score))
        except Exception as e:
            results.append({
                "protocol": item.get("protocol", ""),
                "chain": item.get("chain", ""),
                "error": str(e)
            })
    
    return {"results": results}


# =============================================================================
# Main Entry Point
# =============================================================================

def run_server():
    """Run the inference server."""
    import uvicorn
    
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = server_config.get("port", 8080)
    workers = server_config.get("workers", 1)
    
    uvicorn.run(
        "neural_net.src.inference_server:app",
        host=host,
        port=port,
        workers=workers,
        reload=False
    )

def run_server_with_learner(learner):
    """Run the inference server with a continuous learner."""
    import uvicorn
    import threading
    
    @app.get("/status")
    async def get_status():
        return learner.get_status()
        
    @app.get("/predictions")
    async def get_predictions():
        return learner.get_predictions()
        
    # Start learner in background
    threading.Thread(target=learner.start, daemon=True).start()
    
    server_config = config.get("server", {})
    host = server_config.get("host", "0.0.0.0")
    port = 8000  # Dockerfile exposes 8000
    
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )

if __name__ == "__main__":
    run_server()
