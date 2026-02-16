#!/bin/bash
# Created: 2026-02-12
# Kerne OpenRouter Inference Provider - GLM-5 (750B) Deployment Script
# WARNING: This requires 8+ A100/H100 GPUs (~$12-30/hr)

set -e

echo "=========================================="
echo "Kerne GLM-5 (750B) Inference Deployment"
echo "=========================================="
echo ""
echo "⚠️  WARNING: This model requires:"
echo "   - 8× A100 80GB OR 8× H100 80GB"
echo "   - Estimated cost: $12-30/hour"
echo "   - Daily cost: $288-720/day"
echo ""
read -p "Continue? (y/n) " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Configuration
MODEL_NAME="${MODEL_NAME:-zai-org/GLM-5}"
PORT="${PORT:-8000}"
TENSOR_PARALLEL="${TENSOR_PARALLEL:-8}"
MAX_MODEL_LEN="${MAX_MODEL_LEN:-4096}"
GPU_MEMORY_UTIL="${GPU_MEMORY_UTIL:-0.95}"

# Check GPU count
GPU_COUNT=$(nvidia-smi --query-gpu=count --format=csv,noheader | head -1 | tr -d ' ')
echo "Detected $GPU_COUNT GPUs"

if [ "$GPU_COUNT" -lt 8 ]; then
    echo "❌ ERROR: GLM-5 requires at least 8 GPUs. Detected: $GPU_COUNT"
    echo "Please provision a larger instance."
    exit 1
fi

echo "✅ GPU count verified: $GPU_COUNT GPUs available"

# Install dependencies
echo ""
echo "[1/5] Installing dependencies..."
pip install --upgrade pip
pip install vllm transformers huggingface_hub accelerate deepspeed

# Check HuggingFace token
if [ -z "$HF_TOKEN" ]; then
    echo ""
    echo "⚠️  HF_TOKEN not set. You may need to authenticate for gated models."
    echo "Run: export HF_TOKEN=your_token_here"
    read -p "Enter your HuggingFace token (or press Enter to skip): " HF_TOKEN_INPUT
    if [ -n "$HF_TOKEN_INPUT" ]; then
        export HF_TOKEN="$HF_TOKEN_INPUT"
        huggingface-cli login --token "$HF_TOKEN"
    fi
else
    echo "[2/5] Authenticating with HuggingFace..."
    huggingface-cli login --token $HF_TOKEN
fi

# Check available GPU memory
echo ""
echo "[3/5] Checking GPU memory..."
nvidia-smi --query-gpu=name,memory.total,memory.free --format=csv
TOTAL_MEMORY=$(nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits | head -1)
echo "Total GPU memory per device: ${TOTAL_MEMORY}MB"

# Download model (optional pre-download)
echo ""
echo "[4/5] Model download..."
echo "The model will be downloaded automatically by vLLM on first run."
echo "This may take 30-60 minutes depending on bandwidth."
read -p "Pre-download model now? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Downloading GLM-5..."
    huggingface-cli download $MODEL_NAME --local-dir /models/glm-5
fi

# Start vLLM server
echo ""
echo "[5/5] Starting GLM-5 vLLM server..."
echo ""
echo "Configuration:"
echo "  Model: $MODEL_NAME"
echo "  Port: $PORT"
echo "  Tensor Parallel Size: $TENSOR_PARALLEL"
echo "  Max Context: $MAX_MODEL_LEN tokens"
echo "  GPU Memory Utilization: $GPU_MEMORY_UTIL"
echo ""

# Choose deployment method
echo "Select deployment method:"
echo "  1) vLLM (recommended)"
echo "  2) DeepSpeed (alternative)"
read -p "Choice (1-2): " -n 1 -r DEPLOY_METHOD
echo ""

if [ "$DEPLOY_METHOD" = "2" ]; then
    echo "Starting with DeepSpeed..."
    deepspeed --num_gpus $TENSOR_PARALLEL \
        -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_NAME" \
        --host 0.0.0.0 \
        --port "$PORT" \
        --tensor-parallel-size "$TENSOR_PARALLEL" \
        --dtype auto \
        --max-model-len "$MAX_MODEL_LEN" \
        --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
        --enable-prefix-caching
else
    echo "Starting with vLLM..."
    python -m vllm.entrypoints.openai.api_server \
        --model "$MODEL_NAME" \
        --host 0.0.0.0 \
        --port "$PORT" \
        --tensor-parallel-size "$TENSOR_PARALLEL" \
        --dtype auto \
        --max-model-len "$MAX_MODEL_LEN" \
        --gpu-memory-utilization "$GPU_MEMORY_UTIL" \
        --enable-prefix-caching
fi

# Note: For background execution, use:
# nohup bash deploy_glm5.sh > glm5_inference.log 2>&1 &

echo ""
echo "GLM-5 server stopped."