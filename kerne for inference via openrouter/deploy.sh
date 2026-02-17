#!/bin/bash
# Created: 2026-02-12
# Kerne OpenRouter Inference Provider - Deployment Script
# Run this on your GPU instance (RunPod/Vast.ai)

set -e

echo "=========================================="
echo "Kerne Inference Provider Deployment"
echo "=========================================="

# Configuration
MODEL_NAME="${MODEL_NAME:-meta-llama/Llama-3.1-8B-Instruct}"
PORT="${PORT:-8000}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-8192}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTIL:-0.9}"

# Install dependencies
echo "[1/4] Installing dependencies..."
pip install --upgrade pip
pip install vllm transformers huggingface_hub

# Login to HuggingFace (required for Llama models)
if [ -z "$HF_TOKEN" ]; then
    echo "Warning: HF_TOKEN not set. You may need to authenticate for gated models."
    echo "Run: huggingface-cli login"
else
    echo "[2/4] Authenticating with HuggingFace..."
    huggingface-cli login --token $HF_TOKEN
fi

# Download model (optional - vLLM will auto-download)
echo "[3/4] Pre-downloading model: $MODEL_NAME..."
python -c "from transformers import AutoModelForCausalLM, AutoTokenizer; \
    AutoTokenizer.from_pretrained('$MODEL_NAME'); \
    AutoModelForCausalLM.from_pretrained('$MODEL_NAME')" 2>/dev/null || \
    echo "Model will be downloaded on first run."

# Start vLLM server
echo "[4/4] Starting vLLM server on port $PORT..."
echo ""
echo "Model: $MODEL_NAME"
echo "Port: $PORT"
echo "Max Context: $MAX_MODEL_LEN tokens"
echo "GPU Memory Utilization: $GPU_MEMORY_UTIL"
echo ""

python -m vllm.entrypoints.openai.api_server \
    --model "$MODEL_NAME" \
    --host 0.0.0.0 \
    --port "$PORT" \
    --dtype auto \
    --max-model-len "$MAX_MODEL_LEN" \
    --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
    --enable-prefix-caching \
    --enable-chunked-prefill

# Note: For background execution, use:
# nohup bash deploy.sh > inference.log 2>&1 &