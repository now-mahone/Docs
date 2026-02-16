// Created: 2026-02-12

# GLM-5 (750B) - The Singular Best Deployment Strategy

## Executive Decision: Two-Tier Approach

**The Reality:** GLM-5 (750B parameters) requires enterprise infrastructure that fundamentally changes the profit equation. A single RTX 4090 cannot run this model.

**The Solution:** Deploy a **two-tier infrastructure**:

1. **Tier 1 (Profit Generator):** Small models on cheap GPUs → Generates profit
2. **Tier 2 (Differentiation):** GLM-5 on enterprise GPUs → Commands premium pricing

---

## 1. Hardware Requirements - Non-Negotiable

### GLM-5 Minimum Requirements

| Configuration | VRAM | GPUs Required | Hourly Cost |
|---------------|------|---------------|-------------|
| **Minimum (INT4/FP8)** | ~400GB | 5× A100 80GB | $7.50/hr |
| **Recommended (FP8)** | ~800GB | 8× A100 80GB | $12/hr |
| **Optimal (BF16)** | ~1500GB | 16× A100 80GB | $24/hr |

### Available Model Formats

The GLM-5 model may have compressed variants:
- **BF16 (full precision)**: ~1.5TB VRAM - 16× A100 required
- **FP8**: ~750GB VRAM - 8× A100 required  
- **INT4/GPTQ**: ~400GB VRAM - 5× A100 required (if available)

---

## 2. The Singular Best Approach: RunPod + Dynamic Scaling

### Why RunPod?

| Factor | RunPod | Lambda Labs | AWS | DigitalOcean |
|--------|--------|-------------|-----|--------------|
| 8× H100 hourly | $20-30 | $20-25 | $98 | N/A |
| 8× A100 hourly | $12-15 | $12-15 | $32 | N/A |
| Spot instances | ✅ 60-80% off | ✅ Available | ✅ Available | ❌ |
| Hourly billing | ✅ | ✅ | ✅ | ✅ |
| **GLM-5 viability** | ✅ BEST | ✅ Good | ❌ Too expensive | ❌ N/A |

### Recommended Configuration

```
Provider: RunPod Secure Cloud
GPU: 8× A100 80GB (or 8× H100 80GB for better throughput)
Hourly Cost: $12-15/hr (A100) or $20-30/hr (H100)
Daily Cost: $288-360 (A100) or $480-720 (H100)
```

---

## 3. Profitability Analysis - The Brutal Truth

### Cost Structure

```
RunPod 8× A100: $12/hr × 24hr = $288/day
RunPod 8× H100: $20/hr × 24hr = $480/day
```

### Required Revenue to Break Even

| Token Type | Rate | Daily Tokens Needed |
|------------|------|---------------------|
| Prompt ($1.00/M) | $1.00/M | 288M prompt tokens |
| Completion ($2.00/M) | $2.00/M | 144M completion tokens |
| **Blended** | $1.50/M | ~192M total tokens |

### Break-Even Utilization

```
At $288/day cost with $1.50/M blended rate:
Break-even = 192M tokens/day

RTX 4090 does ~100M tokens/day at 50% utilization
GLM-5 on 8× H100 does ~60-80M tokens/day at 50% utilization (slower due to model size)

Break-even utilization: ~80-100% (VERY DIFFICULT)
```

### The Profit Problem

**Problem:** GLM-5 is SLOWER per dollar than smaller models because:
1. Higher latency per token (model is 100x larger)
2. Lower throughput per GPU dollar
3. High fixed cost even with zero traffic

**However, GLM-5 has advantages:**
1. Premium pricing ($1-3/M tokens vs $0.10-0.20 for small models)
2. Low competition (few providers can run 750B models)
3. Unique capability (most capable open-source model)

---

## 4. The Winning Strategy: Two-Phase Deployment

### Phase 1: Start Small (Week 1-4)

```
Deploy: Llama 3.1 8B on RTX 4090
Cost: $8.16/day
Expected Revenue: $50-80/day at 40-60% utilization
Expected Profit: $40-70/day

Action: Build OpenRouter reputation, generate initial profit
```

### Phase 2: Add GLM-5 Selectively (Month 2+)

**Only deploy GLM-5 when:**

1. **Tier 1 is profitable** → Use profits to subsidize GLM-5 experiments
2. **GLM-5 demand verified** → Monitor OpenRouter for GLM-5 request patterns
3. **Premium pricing confirmed** → Ensure $1.50-3.00/M rates are achievable

**GLM-5 Deployment Options:**

| Option | Strategy | Daily Cost | When to Use |
|--------|----------|------------|-------------|
| **Spot Instances** | Scale up during peak demand | $50-100 | High demand periods only |
| **Scheduled Hours** | Run 8hrs/day during peak | $96-160 | Predictable demand windows |
| **On-Demand** | 24/7 dedicated instance | $288-480 | Proven sustained demand |
| **Serverless (Modal)** | Pay per request | Variable | Uncertain/low demand |

---

## 5. GLM-5 Quick Start Commands

### RunPod Multi-GPU Setup

```bash
# 1. Create RunPod account: https://runpod.io
# 2. Go to "GPU Cloud" → "Secure Cloud"
# 3. Search for "8× A100" or "8× H100" instances
# 4. Select template: "vLLM" or "PyTorch"
# 5. Deploy instance

# SSH into instance
ssh root@<pod-ip>

# Install dependencies
pip install vllm transformers huggingface_hub accelerate

# Authenticate with HuggingFace
huggingface-cli login --token $HF_TOKEN

# Launch GLM-5 with tensor parallelism across 8 GPUs
python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --host 0.0.0.0 \
    --port 8000 \
    --tensor-parallel-size 8 \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching \
    --trust-remote-code
```

### Alternative: Use Quantized Version (If Available)

```bash
# Check for INT4/FP8 quantized versions on HuggingFace
# These would reduce VRAM requirements by 4-8x

# Example (if INT4 available):
python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5-INT4 \
    --tensor-parallel-size 4 \
    --dtype auto \
    --max-model-len 8192
```

---

## 6. GLM-5 on OpenRouter: Pricing Strategy

### Recommended Pricing

| Token Type | Your Rate | Market Rate | Margin |
|------------|-----------|-------------|--------|
| Prompt | $1.00/M | $1.50-2.00/M | Competitive |
| Completion | $2.00/M | $3.00-4.00/M | Competitive |

### Why These Rates?

1. **Slightly below market** → Attract traffic initially
2. **Still profitable at 60%+ utilization** → $200-400/day profit possible
3. **Premium positioning** → You're one of few providers running 750B

---

## 7. Final Recommendation: The Hybrid Fleet

### Optimal Configuration for $100-300/day Profit

```
┌─────────────────────────────────────────────────────────────┐
│                    KERNE INFERENCE FLEET                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  FLEET 1: Small Models (Always On)                         │
│  ───────────────────────────────────────                    │
│  GPU: 1-2× RTX 4090 on RunPod                               │
│  Cost: $8-16/day                                            │
│  Models: Llama 3.1 8B, Qwen 2.5 7B                          │
│  Revenue: $60-120/day                                       │
│  Profit: $50-100/day                                        │
│                                                             │
│  FLEET 2: GLM-5 (On-Demand/Spot)                            │
│  ───────────────────────────────────────                    │
│  GPU: 8× A100 on RunPod (spot instances)                    │
│  Cost: $50-150/day (variable, spot pricing)                 │
│  Models: GLM-5 750B                                         │
│  Revenue: $150-400/day (when running)                       │
│  Profit: $0-250/day                                         │
│                                                             │
│  TOTAL PROFIT: $50-350/day                                  │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### Execution Steps

1. **Today:** Deploy Llama 3.1 8B on RTX 4090 (use existing `deploy.sh`)
2. **Week 1:** Build OpenRouter reputation, generate $50-100/day profit
3. **Week 2-4:** Monitor GLM-5 demand on OpenRouter dashboard
4. **Month 2:** If demand exists, deploy GLM-5 on spot instances during peak hours
5. **Month 3+:** Scale GLM-5 to dedicated instance if utilization >50%

---

## 8. Risk Mitigation

### GLM-5 Specific Risks

| Risk | Mitigation |
|------|------------|
| **High fixed cost** | Use spot instances, start with scheduled hours |
| **Low utilization** | Monitor demand first, don't deploy blindly |
| **Model loading time** | Keep model loaded, use model caching |
| **Competition from big players** | Compete on price, reliability, support |

### Exit Strategy

If GLM-5 doesn't generate sufficient revenue:
- Scale down to Tier 1 (small models) which ARE profitable
- Maximum loss: 1-2 days of GPU rental (~$50-100)

---

## 9. Quick Decision Matrix

| Your Goal | Recommended Action |
|-----------|-------------------|
| **Start generating profit TODAY** | Deploy Llama 3.1 8B on RTX 4090 |
| **Test GLM-5 viability** | Run GLM-5 on spot instance for 4-8 hours |
| **Scale to $200+/day** | Hybrid fleet: 1× RTX 4090 + GLM-5 spot |
| **Maximum differentiation** | GLM-5 dedicated (requires proven demand) |

---

## 10. Bottom Line

**GLM-5 alone is NOT profitable at current OpenRouter rates unless you achieve 80%+ utilization.**

**The winning strategy:**
1. Deploy small models first → Guaranteed profit
2. Add GLM-5 selectively → Premium differentiation
3. Scale dynamically based on demand → Cost optimization

**Estimated profit with hybrid approach: $100-300/day**

---

*Created: 2026-02-12*
*Author: Kerne Protocol Team*