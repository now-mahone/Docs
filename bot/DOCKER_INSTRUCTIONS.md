# Kerne Bot Dockerization

## Dockerfile
```dockerfile
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Run the bot
CMD ["python", "main.py"]
```

## docker-compose.yml
```yaml
version: '3.8'

services:
  kerne-bot:
    build: .
    container_name: kerne-bot
    restart: always
    env_file:
      - .env
    volumes:
      - ./.env:/app/.env
      - ../out:/app/out
```
