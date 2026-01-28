# CoW Swap Solver Deployment Runbook
**Created:** 2026-01-27
**Status:** READY_FOR_DEPLOYMENT

---

## Overview

This runbook covers deploying the Kerne CoW Swap Solver API endpoint for the CoW Protocol solver competition.

The solver endpoint receives auction batches from CoW Protocol's driver and returns solutions using Kerne's ZIN (Zero-Fee Intent Network) infrastructure.

---

## Quick Start (Local Testing)

### 1. Test the solver locally:

```bash
cd bot
python -m solver.cowswap_solver_api
```

The API will start on `http://localhost:8080`

### 2. Verify it's running:

```bash
curl http://localhost:8080/health
# Expected: {"status":"ok"}

curl http://localhost:8080/info
# Returns solver configuration
```

### 3. Test a quote:

```bash
curl -X POST http://localhost:8080/quote \
  -H "Content-Type: application/json" \
  -d '{
    "sellToken": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
    "buyToken": "0x4200000000000000000000000000000000000006",
    "sellAmount": "1000000"
  }'
```

---

## Production Deployment Options

### Option A: Railway.app (Recommended - Free Tier)

1. Create account at https://railway.app
2. Connect GitHub repo
3. Create new project from `bot/` directory
4. Set environment variables:
   - `SOLVER_HOST=0.0.0.0`
   - `SOLVER_PORT=8080`
   - `BASE_RPC_URL=https://mainnet.base.org`
   - `ZIN_EXECUTOR_ADDRESS=0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995`
   - `ZIN_POOL_ADDRESS=0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7`
5. Set start command: `python -m solver.cowswap_solver_api`
6. Deploy and get URL (e.g., `https://kerne-solver.up.railway.app`)

### Option B: Render.com (Free Tier)

1. Create account at https://render.com
2. New Web Service → Connect repo
3. Root Directory: `bot`
4. Build Command: `pip install -r requirements.txt && pip install fastapi uvicorn pydantic`
5. Start Command: `python -m solver.cowswap_solver_api`
6. Add environment variables (same as above)
7. Deploy and get URL (e.g., `https://kerne-solver.onrender.com`)

### Option C: Docker (VPS/Cloud)

```bash
cd bot
docker-compose up -d kerne-cowswap-solver
```

Then expose port 8081 via nginx/caddy with SSL.

### Option D: Vercel Serverless (Advanced)

Convert to serverless function - requires code modification.

---

## Endpoint URL Format

Once deployed, your solver endpoint will be:

```
https://YOUR_DOMAIN/solve
```

For example:
- Railway: `https://kerne-solver.up.railway.app/solve`
- Render: `https://kerne-solver.onrender.com/solve`
- Custom: `https://solver.kerne.ai/solve`

---

## What to Tell Bram (CoW Swap)

Once deployed, respond with:

```
Hi Bram,

Our solver endpoint is ready:

Endpoint: https://YOUR_DEPLOYED_URL/solve

Solver Details:
- Name: Kerne
- Chain: Base (8453)
- Supported Tokens: USDC, WETH, wstETH, cbETH
- Infrastructure: ZIN (Zero-Fee Intent Network)

Additional endpoints for verification:
- Health: https://YOUR_DEPLOYED_URL/health
- Info: https://YOUR_DEPLOYED_URL/info

Let us know if you need any additional information for the shadow competition setup.

Best,
@Kerne_Protocol
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Health check with solver info |
| `/health` | GET | Simple health check |
| `/info` | GET | Solver configuration details |
| `/solve` | POST | Main solver endpoint (CoW Protocol calls this) |
| `/quote` | POST | Test quote endpoint |
| `/metrics` | GET | Solver performance metrics |

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `SOLVER_HOST` | `0.0.0.0` | API host |
| `SOLVER_PORT` | `8080` | API port |
| `BASE_RPC_URL` | `https://mainnet.base.org` | Base RPC endpoint |
| `ZIN_EXECUTOR_ADDRESS` | `0x04F52...` | ZIN Executor contract |
| `ZIN_POOL_ADDRESS` | `0xB9BdF...` | ZIN Pool contract |
| `ZIN_MIN_PROFIT_BPS` | `5` | Minimum profit threshold |
| `ZIN_MAX_GAS_PRICE_GWEI` | `50` | Max gas price |

---

## Monitoring

After deployment, monitor:

1. **Health endpoint**: Should return `{"status":"ok"}`
2. **Logs**: Check for incoming auction requests
3. **Metrics endpoint**: Track solutions generated

---

## Troubleshooting

### "No quote available"
- Check RPC connectivity
- Verify token addresses are correct
- Ensure Aerodrome has liquidity for the pair

### "Insufficient liquidity"
- ZIN Pool needs to be seeded with tokens
- Check `maxFlashLoan()` returns > 0

### Connection errors
- Verify RPC URL is accessible
- Check firewall/network settings

---

## Next Steps After Deployment

1. ✅ Deploy solver endpoint
2. ✅ Verify health check works
3. ✅ Send endpoint URL to Bram
4. ⏳ Wait for shadow competition onboarding
5. ⏳ Monitor solver performance
6. ⏳ Optimize based on competition results
