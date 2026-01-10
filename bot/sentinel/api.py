# Created: 2026-01-09
from fastapi import FastAPI, WebSocket
from typing import Dict
import asyncio
import json
from bot.sentinel.risk_engine import RiskEngine
from bot.sentinel.performance_tracker import PerformanceTracker

app = FastAPI(title="Kerne Sentinel API")
risk_engine = RiskEngine()
perf_tracker = PerformanceTracker()

# Mock data for demonstration
MOCK_VAULT = "0x1234567890abcdef1234567890abcdef12345678"

@app.get("/health")
async def health_check():
    return {"status": "online", "engine": "Sentinel"}

@app.get("/vault/{address}/risk")
async def get_vault_risk(address: str):
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
        "risk_profile": profile,
        "solvency": solvency_data,
        "timestamp": asyncio.get_event_loop().time()
    }

@app.websocket("/ws/risk")
async def websocket_risk_stream(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            # Simulate real-time updates
            mock_data = {
                "address": MOCK_VAULT,
                "onchain_collateral": 100.0,
                "cex_short_position": -99.5,
                "liq_onchain": 0.45,
                "liq_cex": 0.35
            }
            profile = risk_engine.analyze_vault(mock_data)
            await websocket.send_json({
                "vault": MOCK_VAULT,
                "health_score": profile.health_score,
                "net_delta": profile.net_delta,
                "timestamp": asyncio.get_event_loop().time()
            })
            await asyncio.sleep(5)
    except Exception as e:
        print(f"WebSocket error: {e}")
    finally:
        await websocket.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
