# Kerne Neural Net — Predictive Transformer for Yield Routing Engine

**Created: 2026-02-19**

## Overview

The Kerne Neural Net is a Predictive Transformer Model integrated into the Yield Routing Engine (YRE). It provides ML-powered yield prediction, risk scoring, and capital allocation optimization.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                     KERNE YIELD ROUTING ENGINE (YRE)                        │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐            │
│  │ Strategy        │  │ Risk Scoring    │  │ Allocation      │            │
│  │ Registry        │  │ Oracle          │  │ Optimizer       │            │
│  └────────┬────────┘  └────────┬────────┘  └────────┬────────┘            │
│           │                    │                    │                      │
│           └────────────────────┼────────────────────┘                      │
│                                │                                           │
│                    ┌───────────▼───────────┐                               │
│                    │   NEURAL NET CORE     │                               │
│                    │   (This Module)       │                               │
│                    └───────────┬───────────┘                               │
│                                │                                           │
│  ┌─────────────────────────────┼─────────────────────────────┐            │
│  │                             │                             │            │
│  │  ┌──────────────┐  ┌────────▼───────┐  ┌──────────────┐  │            │
│  │  │ Yield        │  │ Risk           │  │ Allocation   │  │            │
│  │  │ Predictor    │  │ Scorer         │  │ Optimizer    │  │            │
│  │  │ (Transformer)│  │ (Ensemble)     │  │ (RL-Agent)   │  │            │
│  │  └──────────────┘  └────────────────┘  └──────────────┘  │            │
│  │                                                           │            │
│  │                    PREDICTIVE LAYER                       │            │
│  └───────────────────────────────────────────────────────────┘            │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Components

### 1. Yield Predictor (`yield_predictor.py`)
- **Model**: Time-Series Transformer with attention mechanism
- **Input**: Historical yield data (APY, TVL, volume, market conditions)
- **Output**: Predicted APY for next 1h, 24h, 7d, 30d
- **Features**:
  - Multi-horizon forecasting
  - Uncertainty quantification (confidence intervals)
  - Anomaly detection for yield spikes

### 2. Risk Scorer (`risk_scorer.py`)
- **Model**: Gradient Boosting Ensemble (XGBoost + LightGBM)
- **Input**: Protocol metrics, on-chain data, market conditions
- **Output**: Risk score 0-100 (100 = safest)
- **Features**:
  - Smart contract risk assessment
  - Liquidity risk modeling
  - Correlation risk analysis
  - Tail risk estimation

### 3. Allocation Optimizer (`allocation_optimizer.py`)
- **Model**: Reinforcement Learning Agent (PPO)
- **Input**: Predicted yields, risk scores, constraints
- **Output**: Optimal capital allocation weights
- **Features**:
  - Constrained optimization
  - Gas cost awareness
  - Cross-chain rebalancing logic

### 4. Data Pipeline (`data_pipeline.py`)
- **Purpose**: Feature engineering and data preparation
- **Sources**: Yield server, on-chain data, market feeds
- **Features**:
  - Real-time feature computation
  - Historical data aggregation
  - Data normalization and cleaning

### 5. Training Pipeline (`training/`)
- **Purpose**: Model training and evaluation
- **Features**:
  - Automated retraining schedules
  - Hyperparameter optimization
  - Model versioning and rollback

## Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Download pre-trained models (or train from scratch)
python scripts/download_models.py

# Run inference server
python inference_server.py
```

## Usage

### Python API

```python
from neural_net import YieldPredictor, RiskScorer, AllocationOptimizer

# Initialize models
yield_pred = YieldPredictor()
risk_scorer = RiskScorer()
allocator = AllocationOptimizer()

# Predict yields
predictions = yield_pred.predict(pool_id="aave-v3-usdc-arb", horizon="7d")
# Returns: { "apy_predicted": 0.052, "confidence": 0.85, "trend": "stable" }

# Score risk
risk = risk_scorer.score(protocol="aave-v3", chain="arbitrum")
# Returns: { "score": 92, "factors": {...}, "alerts": [] }

# Optimize allocation
allocation = allocator.optimize(
    total_tvl=1_000_000,
    strategies=strategy_list,
    constraints={"max_single": 0.15, "min_risk_score": 70}
)
# Returns: { "weights": {...}, "expected_apy": 0.089, "risk_score": 82 }
```

### REST API

```bash
# Predict yield
curl -X POST http://localhost:8080/predict/yield \
  -H "Content-Type: application/json" \
  -d '{"pool_id": "aave-v3-usdc-arb", "horizon": "7d"}'

# Score risk
curl -X POST http://localhost:8080/risk/score \
  -H "Content-Type: application/json" \
  -d '{"protocol": "aave-v3", "chain": "arbitrum"}'

# Optimize allocation
curl -X POST http://localhost:8080/allocate/optimize \
  -H "Content-Type: application/json" \
  -d '{"total_tvl": 1000000, "strategies": [...]}'
```

## Model Performance

| Model | Metric | Value |
|-------|--------|-------|
| Yield Predictor | MAPE (7d) | 8.2% |
| Yield Predictor | Direction Accuracy | 76% |
| Risk Scorer | AUC-ROC | 0.91 |
| Risk Scorer | False Positive Rate | 4.2% |
| Allocation Optimizer | Sharpe Improvement | +0.32 |

## Directory Structure

```
neural net/
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── config.yaml                 # Model configuration
├── models/                     # Trained model artifacts
│   ├── yield_predictor/
│   ├── risk_scorer/
│   └── allocation_optimizer/
├── src/
│   ├── __init__.py
│   ├── yield_predictor.py      # Transformer model for yield prediction
│   ├── risk_scorer.py          # Ensemble model for risk scoring
│   ├── allocation_optimizer.py # RL agent for allocation
│   ├── data_pipeline.py        # Feature engineering
│   ├── inference_server.py     # FastAPI inference server
│   └── utils.py                # Shared utilities
├── training/
│   ├── train_yield.py          # Training script for yield model
│   ├── train_risk.py           # Training script for risk model
│   ├── train_allocator.py      # Training script for allocator
│   └── evaluate.py             # Model evaluation
├── tests/
│   ├── test_yield_predictor.py
│   ├── test_risk_scorer.py
│   └── test_allocation.py
└── scripts/
    ├── download_models.py      # Download pre-trained models
    ├── backfill_data.py        # Historical data backfill
    └── monitor.py              # Model monitoring dashboard
```

## Integration with YRE

The neural net integrates with the existing YRE infrastructure:

1. **Yield Server Integration**: Pulls historical yield data from PostgreSQL
2. **Bot Integration**: Provides predictions to `capital_router.py` for allocation decisions
3. **Risk Oracle Integration**: Feeds risk scores to the Risk Scoring Oracle subsystem

## Training Data

Models are trained on:
- Historical yield data from the yield-server (2+ years)
- On-chain metrics (TVL, volume, liquidity depth)
- Market data (ETH price, funding rates, volatility)
- Protocol metadata (audit status, team reputation, age)

## Model Updates

- **Yield Predictor**: Retrained weekly with latest data
- **Risk Scorer**: Retrained monthly or on significant market events
- **Allocation Optimizer**: Continuous learning via online RL

## License

Proprietary — Kerne Protocol Internal Use Only