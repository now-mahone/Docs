# Created: 2026-02-12
# Kerne OpenRouter Inference Provider - Docker Configuration

FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
RUN pip3 install --no-cache-dir \
    vllm==0.6.3 \
    transformers \
    huggingface_hub \
    accelerate \
    fastapi \
    uvicorn

# Copy monitoring script
COPY monitor.py /app/monitor.py

# Copy deployment script
COPY deploy.sh /app/deploy.sh
RUN chmod +x /app/deploy.sh

# Create model cache directory
RUN mkdir -p /root/.cache/huggingface

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5m --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Default environment variables
ENV MODEL_NAME=meta-llama/Llama-3.1-8B-Instruct
ENV PORT=8000
ENV MAX_MODEL_LEN=8192
ENV GPU_MEMORY_UTIL=0.9

# Start vLLM server
CMD python3 -m vllm.entrypoints.openai.api_server \
    --model ${MODEL_NAME} \
    --host 0.0.0.0 \
    --port ${PORT} \
    --dtype auto \
    --max-model-len ${MAX_MODEL_LEN} \
    --gpu-memory-utilization ${GPU_MEMORY_UTIL} \
    --enable-prefix-caching