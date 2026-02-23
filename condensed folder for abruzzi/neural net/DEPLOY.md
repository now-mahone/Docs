# Neural Net Deployment Guide

## DigitalOcean Deployment

### Prerequisites
- DigitalOcean account
- Droplet with GPU (recommended) or CPU-only
- Docker and Docker Compose installed

### Quick Deploy

```bash
# 1. SSH into your DigitalOcean droplet
ssh root@your-droplet-ip

# 2. Clone the repository
git clone https://github.com/enerzy17/kerne-feb-2026.git
cd kerne-feb-2026/neural\ net

# 3. Build and run
docker-compose up -d --build

# 4. Check logs
docker-compose logs -f
```

### API Endpoints

Once running, the neural net exposes these endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/status` | GET | System status and metrics |
| `/predictions` | GET | All cached predictions |
| `/predict/yield` | POST | Predict yield for a pool |

### Example Usage

```bash
# Check health
curl http://localhost:8001/health

# Get all predictions
curl http://localhost:8001/predictions

# Get system status
curl http://localhost:8001/status
```

### Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRAIN_INTERVAL_HOURS` | 6 | Hours between retraining |
| `DATA_FETCH_INTERVAL_MINUTES` | 60 | Minutes between data fetches |
| `MIN_NEW_SAMPLES` | 100 | Minimum samples before retraining |
| `EPOCHS_PER_RETRAIN` | 5 | Epochs per training session |

### How It Works

1. **Data Collection** (every 60 min)
   - Fetches latest yield data from DeFiLlama
   - Fetches historical data for top stablecoin pools
   - Stores in training buffer

2. **Continuous Training** (every 6 hours)
   - Trains on accumulated data
   - Updates model incrementally
   - Saves checkpoint automatically

3. **Prediction Cache** (updated hourly)
   - Maintains predictions for top 20 pools
   - Multi-horizon: 1h, 24h, 7d, 30d
   - Includes uncertainty quantification

### Monitoring

```bash
# View real-time logs
docker-compose logs -f

# Check container status
docker-compose ps

# Check resource usage
docker stats kerne-neural-net
```

### Updating

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose up -d --build
```

### Troubleshooting

**Container won't start:**
```bash
# Check logs
docker-compose logs

# Rebuild from scratch
docker-compose build --no-cache
docker-compose up -d
```

**Out of memory:**
- Reduce `MIN_NEW_SAMPLES` to 50
- Reduce `EPOCHS_PER_RETRAIN` to 3
- Add swap space to droplet

**Model not improving:**
- Check data fetch logs
- Increase `MIN_NEW_SAMPLES`
- Increase `EPOCHS_PER_RETRAIN`