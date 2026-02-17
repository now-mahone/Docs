// Created: 2026-02-12

# Kerne OpenRouter Inference Provider Blueprint

## Executive Summary

**Objective:** Generate $20-$100+/day in profit by becoming an OpenRouter inference provider for open-source models.

**Strategy:** Deploy cost-effective GPU instances running high-demand open-source models, earning per-token fees from OpenRouter while maintaining healthy profit margins over infrastructure costs.

---

## 1. OpenRouter Provider Economics

### How OpenRouter Provider Payments Work

OpenRouter routes user requests to multiple providers. As a provider, you earn:

| Metric | Typical Rate |
|--------|-------------|
| **Prompt Tokens** | $0.10 - $0.60 per million tokens |
| **Completion Tokens** | $0.20 - $1.20 per million tokens |
| **OpenRouter Fee** | ~5-7% of transaction |

### Revenue Formula
```
Daily Revenue = (Prompt Tokens + Completion Tokens) × Blended Rate
Daily Profit = Daily Revenue - GPU Rental Cost - Electricity/Overhead
```

### Target Metrics for $50/day Profit
| Target | Value |
|--------|-------|
| **Daily Revenue Target** | $70-80/day |
| **GPU Cost Budget** | $15-25/day |
| **Net Profit** | $50-55/day |
| **Monthly Profit** | $1,500-1,650/month |

---

## 2. Cloud GPU Provider Comparison

### Cost-Effective Options (Ranked by Value)

#### Tier 1: Best Value (Consumer GPUs)

| Provider | GPU | $/hr | $/day | VRAM | Best For |
|----------|-----|------|-------|------|----------|
| **RunPod** | RTX 4090 | $0.34 | $8.16 | 24GB | 7B-14B models |
| **Vast.ai** | RTX 4090 | $0.30-0.40 | $7.20-9.60 | 24GB | 7B-14B models |
| **RunPod** | RTX 3090 | $0.19 | $4.56 | 24GB | 7B models |
| **Vast.ai** | RTX 3090 | $0.15-0.25 | $3.60-6.00 | 24GB | 7B models |

#### Tier 2: Professional GPUs (Higher Throughput)

| Provider | GPU | $/hr | $/day | VRAM | Best For |
|----------|-----|------|-------|------|----------|
| **Lambda Labs** | A100 40GB | $0.50 | $12.00 | 40GB | 14B-30B models |
| **RunPod** | A100 40GB | $0.89 | $21.36 | 40GB | 14B-30B models |
| **Modal** | A10G | $0.35 | $8.40 | 24GB | Serverless scaling |

#### Tier 3: Enterprise (Reliability Premium)

| Provider | GPU | $/hr | $/day | VRAM | Best For |
|----------|-----|------|-------|------|----------|
| **AWS** | A10G | $1.10 | $26.40 | 24GB | Production critical |
| **GCP** | L4 | $0.80 | $19.20 | 24GB | Production critical |

#### Tier 4: DigitalOcean (Current Kerne Infrastructure)

| Provider | GPU | $/hr | $/day | VRAM | Best For |
|----------|-----|------|-------|------|----------|
| **DigitalOcean** | H100 | $2.69 | $64.56 | 80GB | Premium, reliable |
| **DigitalOcean** | A100 | $1.99 | $47.76 | 80GB | Premium, reliable |
| **DigitalOcean** | A10G | $1.10 | $26.40 | 24GB | Small models |

---

## 2.5. DigitalOcean vs. RunPod/Vast.ai Comparison

### Why DigitalOcean for Kerne?

**Advantages:**
- ✅ **Already in use** - Kerne hedging bot runs on DigitalOcean
- ✅ **Unified billing** - Single invoice for all infrastructure
- ✅ **Familiar tooling** - Same dashboard, CLI, and workflows
- ✅ **Reliability** - 99.99% uptime SLA
- ✅ **Support** - Enterprise support already available
- ✅ **Security** - Same VPC/firewall rules as hedging bot
- ✅ **Simple provisioning** - `doctl` CLI or web dashboard

**Disadvantages:**
- ❌ **Higher cost** - 2-8x more expensive than RunPod/Vast.ai
- ❌ **Limited GPU selection** - Only H100, A100, A10G
- ❌ **No consumer GPUs** - No RTX 4090/3090 options

### Cost Comparison: DigitalOcean vs RunPod

| Configuration | DigitalOcean | RunPod | Difference |
|---------------|--------------|--------|------------|
| **7B Model (24GB VRAM)** | | | |
| A10G 24GB | $26.40/day | N/A | - |
| RTX 4090 equivalent | N/A | $8.16/day | **+$18.24/day more on DO** |
| **14B Model (40GB VRAM)** | | | |
| A100 80GB | $47.76/day | $21.36/day | **+$26.40/day more on DO** |
| **70B Model (80GB VRAM)** | | | |
| H100 80GB | $64.56/day | $32.00/day | **+$32.56/day more on DO** |

### Profitability Impact

**Scenario: Llama 3.1 8B at 50% Utilization ($70/day revenue)**

| Provider | Daily Cost | Daily Profit | Profit Margin |
|----------|------------|--------------|---------------|
| RunPod RTX 4090 | $8.16 | $61.84 | 88% |
| DigitalOcean A10G | $26.40 | $43.60 | 62% |
| **Difference** | +$18.24 | -$18.24 | -26% |

**Scenario: GLM-5 750B at 60% Utilization ($432/day revenue)**

| Provider | Daily Cost | Daily Profit | Profit Margin |
|----------|------------|--------------|---------------|
| RunPod 8× H100 | $240.00 | $192.00 | 44% |
| DigitalOcean 8× H100 | $516.48 | -$84.48 | -20% (LOSS) |
| **Difference** | +$276.48 | -$276.48 | -64% |

### Recommendation Matrix

| Use Case | Recommended Provider | Reasoning |
|----------|---------------------|-----------|
| **Llama 8B / Qwen 7B** | RunPod/Vast.ai | 3x cheaper, higher profit margin |
| **Testing/Development** | DigitalOcean A10G | Already have account, easy setup |
| **GLM-5 (750B)** | RunPod ONLY | DigitalOcean would be unprofitable |
| **Production Stability** | DigitalOcean | If reliability > profit margin |
| **Unified Infrastructure** | DigitalOcean | If simplifying operations matters |

### DigitalOcean Deployment

If using DigitalOcean for inference:

```bash
# Install doctl CLI
snap install doctl

# Create GPU droplet
doctl compute droplet create kerne-inference \
  --region nyc1 \
  --size gpu-h100-80gb-1 \
  --image ubuntu-22-04-x64 \
  --ssh-keys <your-ssh-key-id>

# Or via web: https://cloud.digitalocean.com/droplets/new
# Select: GPU Droplet → H100 80GB → $2.69/hr
```

### Hybrid Strategy (Recommended for Kerne)

**Best of both worlds:**
1. **DigitalOcean** - Run hedging bot (current setup)
2. **RunPod/Vast.ai** - Run inference (cost-optimized)
3. **Use DigitalOcean for:**
   - Development/testing
   - Monitoring dashboard
   - Failover backup

**Why this works:**
- Keep proven hedging infrastructure on DO
- Maximize inference profits with cheaper GPUs
- Low risk: separate infrastructure = isolated failures
- Can monitor both from DigitalOcean monitoring tools

### Final Verdict

| Factor | DigitalOcean | RunPod/Vast.ai |
|--------|--------------|----------------|
| Cost Efficiency | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Profit Margin | ⭐⭐ | ⭐⭐⭐⭐⭐ |
| Reliability | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Convenience (for Kerne) | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| GLM-5 Viability | ❌ | ✅ |

**Bottom Line:** For maximizing profit ($20-100+/day target), RunPod/Vast.ai is the clear choice. DigitalOcean would reduce margins by 25-65%, making GLM-5 unprofitable and small models marginally profitable.


**Why:**
- Best price-to-performance ratio
- 24GB VRAM fits 7B-14B models comfortably
- Mature infrastructure
- Hourly billing (no commitment)

---

## 3. Model Selection Strategy

### Recommended Models (3 Models)

#### Model 1: Llama 3.1 8B Instruct ⭐ TOP PICK
| Metric | Value |
|--------|-------|
| **Parameters** | 8B |
| **VRAM Required** | ~6GB (FP16), ~4GB (FP8/INT8) |
| **Throughput** | 80-120 tokens/sec (RTX 4090) |
| **OpenRouter Demand** | Very High |
| **Competition** | High (but volume compensates) |
| **Why** | Highest demand on OpenRouter, efficient, reliable |

#### Model 2: Qwen 2.5 7B Instruct ⭐ HIGH DEMAND
| Metric | Value |
|--------|-------|
| **Parameters** | 7B |
| **VRAM Required** | ~5GB (FP16) |
| **Throughput** | 90-130 tokens/sec (RTX 4090) |
| **OpenRouter Demand** | High |
| **Competition** | Medium |
| **Why** | Growing popularity, excellent reasoning |

#### Model 3: Mistral 7B Instruct v0.3 ⭐ EFFICIENT
| Metric | Value |
|--------|-------|
| **Parameters** | 7B |
| **VRAM Required** | ~5GB (FP16) |
| **Throughput** | 100-140 tokens/sec (RTX 4090) |
| **OpenRouter Demand** | High |
| **Competition** | Medium |
| **Why** | Efficient, well-established, consistent demand |

### Alternative Models to Consider

| Model | VRAM | Notes |
|-------|------|-------|
| DeepSeek R1 Distill Qwen 1.5B | ~2GB | Very fast, trending |
| Phi-4 | ~6GB | Microsoft's new efficient model |
| Gemma 2 9B | ~7GB | Google model, good demand |
| Qwen 2.5 14B | ~10GB | Larger, more capable |

---

## 3.5. GLM-5 (750B Parameters) - Enterprise Tier Model

### Model Overview
**GLM-5** from ZAI Org is a 750 billion parameter model - one of the largest open-source models available.

| Metric | Value |
|--------|-------|
| **Parameters** | 750B |
| **HuggingFace** | https://huggingface.co/zai-org/GLM-5 |
| **Context Length** | Varies by configuration |
| **OpenRouter Demand** | Growing (new model) |
| **Competition** | Low (few providers can run it) |

### Hardware Requirements

**CRITICAL: This model requires enterprise-grade infrastructure.**

| Configuration | VRAM Required | GPU Setup | Est. Cost/Hour |
|---------------|---------------|-----------|----------------|
| **Minimum (FP8)** | ~800GB | 8× A100 80GB | $12-16/hr |
| **Recommended (FP8)** | ~1TB | 8× H100 80GB | $20-30/hr |
| **Optimal (BF16)** | ~1.5TB | 16× A100 80GB | $24-32/hr |

### Infrastructure Options for GLM-5

#### Option A: RunPod Secure Cloud
```bash
# 8× A100 80GB Instance
# Cost: ~$12-15/hr
# Select "Secure Cloud" → "Multi-GPU" → 8× A100 80GB
```

#### Option B: Lambda Labs
```bash
# GH200 Grace Hopper (96GB unified memory per GPU)
# Cost: ~$2.50/hr per GH200
# Need: 8-10× GH200 for GLM-5
```

#### Option C: AWS/GCP Enterprise
```bash
# AWS p5.48xlarge (8× H100 80GB)
# Cost: ~$98/hr (on-demand) or ~$30/hr (spot)
# Recommended: Use spot instances with checkpointing
```

#### Option D: Modal (Serverless)
```bash
# Pay per request - ideal for low/variable traffic
# Auto-scaling based on demand
# No idle costs
```

### GLM-5 Profitability Analysis

**Cost Structure (8× A100 80GB on RunPod):**
```
Hourly Cost: $12-15/hr
Daily Cost: $288-360/day
Monthly Cost: $8,640-10,800/month
```

**Revenue Requirements:**
```
Break-even at: $15/hr revenue
Required tokens/day: ~200M+ tokens
Required utilization: ~60%+
```

**Pricing Strategy for GLM-5:**
| Token Type | Suggested Rate | Market Rate |
|------------|----------------|-------------|
| Prompt | $0.80-1.20/M | $1.00-1.50/M |
| Completion | $1.50-2.50/M | $2.00-3.00/M |

**Profit Scenarios:**
| Utilization | Daily Revenue | Daily Profit |
|-------------|---------------|--------------|
| 30% | $216 | -$72 to -$144 (loss) |
| 50% | $360 | $0 to $72 |
| 70% | $504 | $144-216 |
| 90% | $648 | $288-360 |

### GLM-5 Deployment Strategy

#### Recommended Approach: Start Small, Scale Up

1. **Phase 1**: Deploy 7B-8B models on single RTX 4090
   - Build reputation on OpenRouter
   - Generate initial profit ($20-50/day)
   - Learn infrastructure management

2. **Phase 2**: Add GLM-5 during high-demand periods
   - Use spot instances (60-80% cheaper)
   - Scale up during peak hours
   - Scale down during low demand

3. **Phase 3**: Dedicated GLM-5 instance (if demand proven)
   - Requires sustained 60%+ utilization
   - Target: $200-500/day profit

### GLM-5 Deployment Commands

```bash
# For multi-GPU setup with vLLM
python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 8 \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching

# Alternative: Use DeepSpeed for memory optimization
deepspeed --num_gpus 8 \
    -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --tensor-parallel-size 8
```

### GLM-5 Risk Assessment

| Risk | Level | Mitigation |
|------|-------|------------|
| High infrastructure cost | **CRITICAL** | Use spot instances, scale dynamically |
| Low utilization | **HIGH** | Start with smaller models, prove demand |
| Model loading time | **MEDIUM** | Keep model loaded, use model caching |
| Competition | **LOW** | Few providers can run 750B models |

---

## 4. Profitability Analysis

### Scenario: Single RTX 4090 Instance

**Costs:**
```
RTX 4090 Rental: $0.34/hr × 24hr = $8.16/day
Buffer (10%): $0.82/day
Total Cost: ~$9.00/day
```

**Revenue Projections:**

| Utilization | Tokens/Day | Revenue/Day | Profit/Day |
|-------------|------------|-------------|------------|
| 10% | 20M tokens | $15-20 | $6-11 |
| 25% | 50M tokens | $35-45 | $26-36 |
| 50% | 100M tokens | $70-90 | $61-81 |
| 75% | 150M tokens | $105-135 | $96-126 |

### Break-Even Analysis
```
Break-even utilization: ~15-20% (generating ~$9-10/day revenue)
```

### Multi-GPU Scaling Strategy

| Configuration | Daily Cost | Daily Revenue (50% util) | Daily Profit |
|---------------|------------|--------------------------|--------------|
| 1× RTX 4090 | $9 | $80 | $71 |
| 2× RTX 4090 | $18 | $160 | $142 |
| 4× RTX 4090 | $36 | $320 | $284 |

---

## 5. Infrastructure Architecture

### Recommended Stack

```
┌─────────────────────────────────────────────────────────────┐
│                    OPENROUTER CLOUD                         │
│                  (Request Routing Layer)                    │
└─────────────────────┬───────────────────────────────────────┘
                      │ API Requests
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                  YOUR GPU INSTANCE                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │                 vLLM Server                          │   │
│  │         (OpenAI-Compatible API Server)               │   │
│  └─────────────────────────────────────────────────────┘   │
│                          │                                  │
│  ┌───────────┬───────────┼───────────┬───────────┐        │
│  │ Model 1   │ Model 2   │ Model 3   │           │        │
│  │ Llama 8B  │ Qwen 7B   │ Mistral   │           │        │
│  └───────────┴───────────┴───────────┴───────────┘        │
│                                                             │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              Monitoring & Logging                    │   │
│  │         (Prometheus/Grafana or custom)              │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Software Stack

| Component | Tool | Purpose |
|-----------|------|---------|
| **Inference Engine** | vLLM | Fast, efficient, OpenAI-compatible |
| **API Framework** | FastAPI | REST API server |
| **Monitoring** | Prometheus + Grafana | Performance metrics |
| **Logging** | Loguru | Structured logging |
| **Process Manager** | systemd / Docker | Service management |

### vLLM Advantages
- OpenAI-compatible API (required by OpenRouter)
- PagedAttention for efficient memory
- Continuous batching
- Supports FP8/INT8 quantization
- Active development & community

---

## 6. Implementation Steps

### Phase 1: Setup (Day 1-2)

#### Step 1: Create OpenRouter Provider Account
1. Visit https://openrouter.ai/docs/provider-guide
2. Sign up as a provider
3. Complete KYC if required
4. Get API credentials

#### Step 2: Provision GPU Instance
**RunPod Setup:**
```bash
# 1. Create RunPod account: https://runpod.io
# 2. Select "GPU Cloud" → RTX 4090
# 3. Choose template: "vLLM" or "PyTorch"
# 4. Deploy instance
```

**Vast.ai Setup:**
```bash
# 1. Create Vast.ai account: https://vast.ai
# 2. Search for RTX 4090 instances
# 3. Filter by: reliability > 95%, bandwidth > 500Mbps
# 4. Select instance with PyTorch template
```

#### Step 3: Install vLLM
```bash
# SSH into GPU instance
ssh root@<instance-ip>

# Install vLLM
pip install vllm

# Verify installation
python -c "import vllm; print(vllm.__version__)"
```

### Phase 2: Model Deployment (Day 2-3)

#### Step 4: Download and Configure Models
```bash
# Create model directory
mkdir -p /models

# Download models (HuggingFace)
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir /models/llama-3.1-8b

huggingface-cli download Qwen/Qwen2.5-7B-Instruct --local-dir /models/qwen-2.5-7b

huggingface-cli download mistralai/Mistral-7B-Instruct-v0.3 --local-dir /models/mistral-7b
```

#### Step 5: Launch vLLM Server
```bash
# Single model server (Llama 3.1 8B)
python -m vllm.entrypoints.openai.api_server \
    --model /models/llama-3.1-8b \
    --host 0.0.0.0 \
    --port 8000 \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.9

# For multiple models, run separate instances on different ports
# Port 8000: Llama 3.1 8B
# Port 8001: Qwen 2.5 7B
# Port 8002: Mistral 7B
```

#### Step 6: Test Inference
```bash
# Test the API
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "/models/llama-3.1-8b",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### Phase 3: OpenRouter Integration (Day 3-4)

#### Step 7: Configure OpenRouter Provider
1. In OpenRouter provider dashboard, add your endpoint:
   - URL: `http://<your-public-ip>:8000/v1`
   - Models: List your available models
   - Pricing: Set competitive rates

#### Step 8: Implement Health Checks
```python
# health_check.py
from fastapi import FastAPI
import requests

app = FastAPI()

@app.get("/health")
async def health():
    return {"status": "healthy", "gpu": "rtx4090"}

@app.get("/v1/models")
async def list_models():
    return {
        "data": [
            {"id": "llama-3.1-8b", "object": "model"},
            {"id": "qwen-2.5-7b", "object": "model"},
            {"id": "mistral-7b", "object": "model"}
        ]
    }
```

### Phase 4: Monitoring & Optimization (Day 4-7)

#### Step 9: Set Up Monitoring
```python
# monitor.py
import time
import requests
from datetime import datetime
import json

class InferenceMonitor:
    def __init__(self):
        self.metrics = {
            "requests": 0,
            "tokens_generated": 0,
            "errors": 0,
            "uptime_start": datetime.now()
        }
    
    def log_request(self, tokens):
        self.metrics["requests"] += 1
        self.metrics["tokens_generated"] += tokens
        self.save_metrics()
    
    def calculate_revenue(self, rate_per_million=0.50):
        return (self.metrics["tokens_generated"] / 1_000_000) * rate_per_million

monitor = InferenceMonitor()
```

#### Step 10: Optimize for Cost
- Enable FP8 quantization for 2x throughput
- Tune max_model_len for your use case
- Implement request batching
- Monitor GPU utilization

---

## 7. Risk Mitigation

### Technical Risks

| Risk | Mitigation |
|------|------------|
| GPU instance failure | Use reliable providers (RunPod/Lambda), have backup ready |
| High latency | Choose data center close to OpenRouter, optimize model |
| Model crashes | Implement auto-restart scripts, health checks |
| Network issues | Use instances with high bandwidth |

### Financial Risks

| Risk | Mitigation |
|------|------------|
| Low utilization | Start small, monitor demand, scale gradually |
| Price competition | Focus on efficiency, use cheaper GPUs |
| Unexpected costs | Set billing alerts, use hourly billing |

### Operational Risks

| Risk | Mitigation |
|------|------------|
| OpenRouter policy changes | Stay updated on provider guidelines |
| Model deprecation | Keep models updated, monitor community |
| Security | Use API keys, secure endpoints |

---

## 8. Recommended Launch Configuration

### Week 1: Single GPU Test
```
GPU: 1× RTX 4090 (RunPod)
Cost: ~$8-9/day
Models: Llama 3.1 8B Instruct
Expected Profit: $20-40/day (at 30-50% utilization)
```

### Week 2-4: Optimize & Scale
```
GPU: 2× RTX 4090 (RunPod)
Cost: ~$16-18/day
Models: Llama 3.1 8B + Qwen 2.5 7B + Mistral 7B
Expected Profit: $40-80/day (at 40-60% utilization)
```

### Month 2+: Full Production
```
GPU: 4× RTX 4090 or 2× A100
Cost: ~$32-36/day (RTX) or $24-30/day (A100)
Models: Full model suite
Expected Profit: $100-200/day (at 50%+ utilization)
```

---

## 9. Quick Start Commands

### One-Line vLLM Launch
```bash
# Llama 3.1 8B (most recommended)
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --dtype auto --max-model-len 8192 \
    --gpu-memory-utilization 0.9 \
    --enable-prefix-caching
```

### Docker Deployment
```bash
# Using official vLLM Docker image
docker run --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -p 8000:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --dtype auto
```

---

## 10. Key Success Metrics

| Metric | Target | Monitor |
|--------|--------|---------|
| **GPU Utilization** | >60% | nvidia-smi |
| **Request Latency** | <500ms TTFT | vLLM logs |
| **Tokens/Second** | >80 TPS | Custom monitor |
| **Daily Revenue** | >$50 | OpenRouter dashboard |
| **Daily Profit** | >$30 | Revenue - Costs |
| **Uptime** | >99% | Health checks |

---

## 11. Next Steps Checklist

- [ ] Create OpenRouter provider account
- [ ] Provision RunPod RTX 4090 instance
- [ ] Install vLLM and download models
- [ ] Test local inference
- [ ] Configure OpenRouter endpoint
- [ ] Deploy to production
- [ ] Set up monitoring dashboard
- [ ] Optimize based on utilization data
- [ ] Scale to additional GPUs if profitable

---

## Appendix A: Model Pricing Reference

Current OpenRouter market rates (approximate):

| Model | Prompt $/M tokens | Completion $/M tokens |
|-------|-------------------|----------------------|
| Llama 3.1 8B | $0.10-0.20 | $0.20-0.40 |
| Qwen 2.5 7B | $0.08-0.15 | $0.15-0.30 |
| Mistral 7B | $0.08-0.15 | $0.15-0.30 |

*Note: Set your prices slightly below market average to attract traffic initially.*

---

## Appendix B: Useful Links

- OpenRouter Provider Docs: https://openrouter.ai/docs/provider-guide
- vLLM Documentation: https://vllm.readthedocs.io/
- RunPod: https://runpod.io
- Vast.ai: https://vast.ai
- HuggingFace Models: https://huggingface.co/models

---

*Document Version: 1.0*
*Created: 2026-02-12*
*Author: Kerne Protocol Team*