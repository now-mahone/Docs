FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy bot code
COPY . .

# Ensure subdirectories exist (for volume mapping and runtime)
RUN mkdir -p sentinel solver exchanges data reports

# Run the bot
CMD ["python", "main.py"]
