# Neural Net Continuous Learner Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY training/ ./training/
COPY *.py ./
COPY config.yaml .

# Create models directory
RUN mkdir -p /app/models/yield_predictor

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Health check
HEALTHCHECK --interval=60s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose API port
EXPOSE 8000

# Run continuous learner with API
CMD ["python", "-c", "from continuous_learner import ContinuousLearner; from inference_server import run_server_with_learner; learner = ContinuousLearner(); run_server_with_learner(learner)"]