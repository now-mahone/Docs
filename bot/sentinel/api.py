# Created: 2026-01-09
from fastapi import FastAPI, WebSocket, Depends, HTTPException, Security
from fastapi.security.api_key import APIKeyHeader, APIKey
from starlette.status import HTTP_403_FORBIDDEN
from typing import Dict, Optional
import asyncio
import json
import os
from datetime import datetime
from loguru import logger
from bot.sentinel.risk_engine import RiskEngine
from bot.sentinel.performance_tracker import PerformanceTracker

app = FastAPI(title="Kerne Sentinel API")

# Security Configuration
API_KEY = os.getenv("SENTINEL_API_KEY", "kerne_institutional_secret_2026")
API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

async def get_api_key(
    api_key_header: str = Security(api_key_header),
):
    if api_key_header == API_KEY:
        return api_key_header
    else:
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN, detail="Could not validate credentials"
        )

risk_engine = RiskEngine()
perf_tracker = PerformanceTracker()

# Mock data for demonstration
MOCK_VAULT = "0x1234567890abcdef1234567890abcdef12345678"

@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "Sentinel"}

@app.get("/vault/{address}/risk")
async def get_vault_risk(address: str, api_key: APIKey = Depends(get_api_key)):
    # In production, this would fetch real data from the chain/CEX
    mock_data = {
        "address": address,
        "onchain_collateral": 100.0,
        "cex_short_position": -99.5,
        "liq_onchain": 0.45,
        "liq_cex": 0.35
    }
    profile = risk_engine.analyze_vault(mock_data)
    
    # Solvency v3.0: Aggregate CEX balances
    # In production, this would use CCXT to fetch real balances
    solvency_data = {
        "onchain_assets": mock_data["onchain_collateral"],
        "cex_assets": abs(mock_data["cex_short_position"]) * 1.1, # Assuming 10% margin buffer
        "total_liabilities": mock_data["onchain_collateral"],
        "solvency_ratio": 1.10,
        "is_solvent": True
    }
    
    return {
        "vault_address": profile.vault_address,
        "net_delta": profile.net_delta,
        "health_score": profile.health_score,
        "liquidation_distance_onchain": profile.liquidation_distance_onchain,
        "liquidation_distance_cex": profile.liquidation_distance_cex,
        "solvency": solvency_data,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.websocket("/ws/risk")
async def websocket_risk_stream(websocket: WebSocket):
    # WebSocket authentication (simple token check on first message or query param)
    # For institutional simplicity, we check a query param 'api_key'
    api_key = websocket.query_params.get("api_key")
    if api_key != API_KEY:
        await websocket.close(code=1008)
        return

    await websocket.accept()
    try:
        while True:
            # Solvency v3.0: Real-time risk streaming
            # In production, this would fetch from the shared state of the orchestrator
            mock_data = {
                "address": MOCK_VAULT,
                "onchain_collateral": 100.0,
                "cex_short_position": -99.5,
                "liq_onchain": 0.45,
                "liq_cex": 0.35
            }
            profile = risk_engine.analyze_vault(mock_data)
            
            # Calculate real-time solvency ratio
            solvency_ratio = 1.10 + (asyncio.get_event_loop().time() % 0.05) # Simulated noise
            
            await websocket.send_json({
                "vault": MOCK_VAULT,
                "health_score": profile.health_score,
                "net_delta": profile.net_delta,
                "solvency_ratio": round(solvency_ratio, 4),
                "liquidation_distance": min(profile.liquidation_distance_onchain, profile.liquidation_distance_cex),
                "timestamp": datetime.now().isoformat(),
                "status": "PROTECTED" if profile.health_score > 75 else "WARNING"
            })
            await asyncio.sleep(2) # Faster updates for institutional dashboard
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        try:
            await websocket.close()
        except:
            pass

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
