// Created: 2026-02-12

# Quick Start Guide: Kerne OpenRouter Inference Provider

## Prerequisites

1. **HuggingFace Token** - Required for Llama models
   - Get one at: https://huggingface.co/settings/tokens
   - Accept Llama 3.1 license: https://huggingface.co/meta-llama/Llama-3.1-8B-Instruct

2. **OpenRouter Provider Account**
   - Sign up at: https://openrouter.ai
   - Apply as a provider: https://openrouter.ai/docs/provider-guide

---

## Option A: RunPod (Recommended)

### Step 1: Create RunPod Account
1. Go to https://runpod.io
2. Sign up and add payment method
3. Go to "GPU Cloud" → "Secure Cloud"

### Step 2: Deploy RTX 4090 Instance
1. Select **RTX 4090** ($0.34/hr)
2. Choose template: **vLLM** or **PyTorch 2.0**
3. Click "Deploy"
4. Wait for instance to start (~2 minutes)

### Step 3: Connect to Instance
```bash
# SSH via RunPod terminal or
ssh root@<pod-ip> -p <port>
```

### Step 4: Run Quick Deploy
```bash
# Set your HuggingFace token
export HF_TOKEN=your_token_here

# Download and run the deployment script
curl -O https://raw.githubusercontent.com/your-repo/deploy.sh
chmod +x deploy.sh
./deploy.sh
```

Or manually:
```bash
pip install vllm huggingface_hub
huggingface-cli login --token $HF_TOKEN
python -m vllm.entrypoints.openai.api_server \
    --model meta-llama/Llama-3.1-8B-Instruct \
    --host 0.0.0.0 --port 8000 \
    --dtype auto --max-model-len 8192
```

### Step 5: Configure OpenRouter
1. Get your pod's public IP from RunPod dashboard
2. In OpenRouter provider settings, add endpoint:
   - URL: `http://<pod-ip>:8000/v1`
   - Model: `meta-llama/llama-3.1-8b-instruct`
   - Pricing: Set slightly below market ($0.12/$0.25 per M tokens)

---

## Option B: Vast.ai (Alternative)

### Step 1: Create Account
1. Go to https://vast.ai
2. Sign up and add credits ($10 minimum)

### Step 2: Find RTX 4090 Instance
1. Go to "Search" → "GPU Instances"
2. Filter: 
   - GPU: RTX 4090
   - Reliability: >95%
   - Price: $0.30-0.45/hr
3. Sort by "Price/GPU"

### Step 3: Rent Instance
1. Select instance with good bandwidth
2. Choose "PyTorch" template
3. Click "Rent"

### Step 4: Deploy vLLM
Same as RunPod steps 3-5 above.

---

## Option C: Docker Deployment

### On any GPU server:

```bash
# Clone the repo
git clone <your-repo>
cd kerne-for-inference-via-openrouter

# Set environment
export HF_TOKEN=your_token_here

# Build and run
docker-compose up -d

# Check logs
docker logs kerne-llama-8b

# Run monitor
docker exec -it kerne-monitor python monitor.py
```

---

## Verification

### Test Local Inference
```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.1-8B-Instruct",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### Expected Response
```json
{
  "id": "cmpl-...",
  "object": "chat.completion",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you today?"
    }
  }]
}
```

---

## Monitoring Profit

### Run the monitor
```bash
python monitor.py
```

### Commands
- `s` - Show status
- `p` - Show daily projection
- `r` - Reset metrics
- `q` - Quit

---

## Cost Breakdown

| Item | Daily Cost | Notes |
|------|------------|-------|
| RTX 4090 (RunPod) | $8.16 | $0.34/hr × 24hr |
| RTX 4090 (Vast.ai) | $7.20-9.60 | Variable pricing |
| Network/Bandwidth | ~$0-2 | Usually included |

### Break-Even Point
- At $0.15/M prompt tokens + $0.30/M completion tokens
- Need ~50M tokens/day to generate $15-20 revenue
- Break-even at ~25-30% GPU utilization

---

## Troubleshooting

### "CUDA out of memory"
```bash
# Reduce context length
--max-model-len 4096

# Reduce GPU memory utilization
--gpu-memory-utilization 0.8
```

### Model download slow
```bash
# Pre-download model
pip install huggingface_hub
huggingface-cli download meta-llama/Llama-3.1-8B-Instruct --local-dir /models/llama
```

### Server not responding
```bash
# Check if port is exposed
netstat -tlnp | grep 8000

# Check vLLM logs
docker logs kerne-llama-8b
```

### Low utilization on OpenRouter
- Lower your prices slightly
- Check server latency
- Ensure health check passes
- Verify model name matches OpenRouter's expected format

---

## Scaling Up

### Add More Models (Multi-GPU)
```bash
# On port 8000: Llama 3.1 8B
# On port 8001: Qwen 2.5 7B (GPU 1)
# On port 8002: Mistral 7B (GPU 2)
```

### Add More GPUs
```bash
# RunPod: Select multi-GPU pod
# Or deploy multiple single-GPU pods
```

---

## GLM-5 (750B) Deployment Guide

**⚠️ WARNING: GLM-5 requires enterprise-grade infrastructure (8+ A100/H100 GPUs)**

### Hardware Requirements
| Configuration | GPUs Required | Est. Cost/Hour |
|---------------|---------------|----------------|
| Minimum (FP8) | 8× A100 80GB | $12-16/hr |
| Recommended | 8× H100 80GB | $20-30/hr |
| Optimal | 16× A100 80GB | $24-32/hr |

### RunPod GLM-5 Setup

1. **Create Multi-GPU Instance**
   - Go to RunPod → "Secure Cloud"
   - Select "8× A100 80GB" or "8× H100 80GB"
   - Choose "PyTorch 2.0" template
   - Deploy instance

2. **Download GLM-5**
```bash
# Set HuggingFace token
export HF_TOKEN=your_token_here
huggingface-cli login --token $HF_TOKEN

# Download model (may take 30-60 minutes)
huggingface-cli download zai-org/GLM-5 --local-dir /models/glm-5
```

3. **Launch vLLM Server**
```bash
python -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --host 0.0.0.0 --port 8000 \
    --tensor-parallel-size 8 \
    --dtype auto \
    --max-model-len 4096 \
    --gpu-memory-utilization 0.95 \
    --enable-prefix-caching
```

### Lambda Labs GLM-5 Setup (Alternative)

```bash
# Lambda Labs offers GH200 Grace Hopper instances
# 8-10× GH200 recommended for GLM-5

# Launch command
deepspeed --num_gpus 8 \
    -m vllm.entrypoints.openai.api_server \
    --model zai-org/GLM-5 \
    --tensor-parallel-size 8 \
    --host 0.0.0.0 --port 8000
```

### AWS Spot Instance (Cost-Optimized)

```bash
# Request spot instance: p5.48xlarge (8× H100 80GB)
# Spot price: ~$30/hr (vs $98/hr on-demand)

# Using AWS CLI
aws ec2 request-spot-instances \
    --instance-type p5.48xlarge \
    --spot-price "30" \
    --instance-count 1
```

### GLM-5 Cost Management

**CRITICAL: Monitor utilization closely!**

| Utilization | Daily Cost | Break-Even Revenue |
|-------------|------------|---------------------|
| 24/7 operation | $288-360/day | $300+ revenue needed |
| 12hr/day | $144-180/day | $150+ revenue needed |
| Spot (6hr/day) | $90-120/day | $100+ revenue needed |

### GLM-5 Testing

```bash
curl http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "zai-org/GLM-5",
    "messages": [{"role": "user", "content": "Explain quantum computing."}],
    "max_tokens": 100
  }'
```

### Recommended GLM-5 Strategy

1. **Start Small**: Deploy Llama 3.1 8B first to build demand
2. **Validate Market**: Check if GLM-5 has sufficient OpenRouter demand
3. **Use Spot Instances**: Start with spot to minimize risk
4. **Scale Gradually**: Only run GLM-5 during peak demand hours

---

## Support Resources

- vLLM Docs: https://vllm.readthedocs.io/
- OpenRouter Provider Guide: https://openrouter.ai/docs/provider-guide
- RunPod Discord: https://discord.gg/runpod
- HuggingFace Forums: https://discuss.huggingface.co/