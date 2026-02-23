// Created: 2026-02-12

# Kerne Inference Profit Engine

**Autonomous GPU-based inference system that maximizes profit from OpenRouter.**

## Quick Start

```bash
# 1. Set your HuggingFace token
export HF_TOKEN=your_token_here

# 2. Run simulation to estimate profit
python start_engine.py --mode simulate --duration 30

# 3. Quick deploy (production)
python start_engine.py --quick-deploy
```

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    KERNE INFERENCE PROFIT ENGINE                        │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │  OpenRouter │───▶│   Demand    │───▶│    Auto     │                 │
│  │   Traffic   │    │   Monitor   │    │   Scaler    │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                                      │                        │
│         ▼                                      ▼                        │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                 │
│  │   Pricing   │◀───│   Profit    │◀───│    GPU      │                 │
│  │   Engine    │    │   Tracker   │    │   Manager   │                 │
│  └─────────────┘    └─────────────┘    └─────────────┘                 │
│         │                                      │                        │
│         └──────────────────────────────────────┘                        │
│                          │                                              │
│                          ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                     MODEL FLEET                                  │   │
│  │  ┌───────────┐  ┌───────────┐  ┌───────────┐  ┌───────────┐    │   │
│  │  │ Llama 8B  │  │ Qwen 7B   │  │ Mistral   │  │  GLM-5    │    │   │
│  │  │ RTX 4090  │  │ RTX 4090  │  │ RTX 4090  │  │ 8× A100   │    │   │
│  │  │ $0.34/hr  │  │ $0.34/hr  │  │ $0.34/hr  │  │ $12/hr    │    │   │
│  │  └───────────┘  └───────────┘  └───────────┘  └───────────┘    │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

## How It Works

### 1. **Model Registry**
- 8 models pre-configured (8B to 750B parameters)
- Ranked by profitability (profit per GPU hour)
- Automatic GPU allocation based on model requirements

### 2. **GPU Manager**
- Multi-provider support (RunPod, Vast.ai, Lambda Labs)
- Automatic cheapest-GPU selection
- Dynamic provisioning/deprovisioning

### 3. **Dynamic Pricing**
- Adjusts prices based on:
  - Current utilization
  - Time of day (peak hours)
  - Market rate ranges
- Goal: Maximize revenue while staying competitive

### 4. **Auto-Scaling**
- Monitors demand in real-time
- Scales up when utilization >80%
- Scales down when utilization <30%
- Cooldown prevents thrashing

### 5. **Profit Tracking**
- Real-time revenue/cost calculation
- Per-model profitability analysis
- Daily profit projections

## Model Fleet

| Tier | Model | Parameters | GPU | Cost/Hour | Priority |
|------|-------|------------|-----|-----------|----------|
| **1** | Llama 3.1 8B | 8B | RTX 4090 | $0.34 | ⭐⭐⭐⭐⭐ |
| **1** | Qwen 2.5 7B | 7B | RTX 4090 | $0.34 | ⭐⭐⭐⭐ |
| **1** | Mistral 7B | 7B | RTX 4090 | $0.34 | ⭐⭐⭐ |
| **2** | Qwen 2.5 72B | 72B | 2× A100 | $1.78 | ⭐⭐ |
| **2** | Llama 3.1 70B | 70B | 2× A100 | $1.78 | ⭐⭐ |
| **3** | GLM-5 | 750B | 8× A100 | $12.00 | ⭐ |
| **3** | Llama 3.1 405B | 405B | 8× A100 | $12.00 | ⭐ |

## Files

| File | Purpose |
|------|---------|
| `profit_engine.py` | Core engine (600+ lines) |
| `start_engine.py` | Startup script |
| `config.json` | Configuration |
| `monitor.py` | Simple profit monitor |
| `deploy.sh` | Single-model deploy script |
| `deploy_glm5.sh` | GLM-5 deployment script |
| `BLUEPRINT.md` | Full strategy document |
| `GLM5_STRATEGY.md` | GLM-5 specific strategy |
| `4HOUR_SPRINT.md` | 4-hour setup timeline |

## Usage Modes

### Simulation Mode
Test profitability before spending money:
```bash
python start_engine.py --mode simulate --duration 60
```

### Local Mode
Test with simulated GPU locally:
```bash
python start_engine.py --mode local
```

### Production Mode
Deploy with real GPU instances:
```bash
python start_engine.py --mode production
```

### Quick Deploy
One-command setup wizard:
```bash
python start_engine.py --quick-deploy
```

## Expected Profits

| Configuration | Daily Cost | Daily Revenue | Daily Profit |
|---------------|------------|---------------|--------------|
| 1× RTX 4090 (Llama 8B) | $8 | $50-80 | **$42-72** |
| 2× RTX 4090 (2 models) | $16 | $100-160 | **$84-144** |
| 1× RTX 4090 + GLM-5 spot | $50-100 | $150-300 | **$50-250** |
| Full fleet (optimal) | $100-200 | $300-600 | **$100-400** |

## Configuration

Edit `config.json` to customize:

```json
{
  "general": {
    "profit_target_daily": 100,
    "auto_scale_enabled": true,
    "dynamic_pricing_enabled": true
  },
  "scaling": {
    "target_utilization": 0.60,
    "scale_up_threshold": 0.80,
    "scale_down_threshold": 0.30
  }
}
```

## Requirements

```bash
pip install vllm transformers huggingface_hub
```

## Environment Variables

| Variable | Required | Purpose |
|----------|----------|---------|
| `HF_TOKEN` | ✅ Yes | HuggingFace authentication |
| `RUNPOD_API_KEY` | Optional | RunPod provisioning |
| `VAST_API_KEY` | Optional | Vast.ai provisioning |
| `LAMBDA_API_KEY` | Optional | Lambda Labs provisioning |
| `OPENROUTER_API_KEY` | Optional | OpenRouter integration |

## Architecture Details

See individual documentation:
- **BLUEPRINT.md** - Complete economic analysis
- **GLM5_STRATEGY.md** - 750B model strategy
- **4HOUR_SPRINT.md** - Fast setup timeline

## License

Proprietary - Kerne Protocol Team

---

*Created: 2026-02-12*