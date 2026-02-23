# Created: 2026-01-13
from fastapi import FastAPI
import pandas as pd
import os
from loguru import logger

app = FastAPI(title="Kerne Solver Analytics API")

PROFIT_LOG_PATH = "bot/solver/profit_log.csv"

@app.get("/stats")
async def get_solver_stats():
    """
    Returns high-level solver performance metrics.
    """
    if not os.path.exists(PROFIT_LOG_PATH):
        return {"error": "No data available"}

    try:
        df = pd.read_csv(PROFIT_LOG_PATH)
        total_intents = len(df)
        successful_hedges = len(df[df['status'] == 'HEDGED'])
        win_rate = successful_hedges / total_intents if total_intents > 0 else 0
        
        # Calculate total profit in bps (simplified)
        total_profit_bps = df[df['status'] == 'HEDGED']['profit_bps'].sum()
        
        return {
            "total_intents": total_intents,
            "successful_hedges": successful_hedges,
            "win_rate": f"{win_rate:.2%}",
            "total_profit_bps": f"{total_profit_bps:.2f}",
            "daily_target_status": "ON_TRACK" if total_profit_bps > 50 else "BELOW_TARGET"
        }
    except Exception as e:
        logger.error(f"API Error: {e}")
        return {"error": str(e)}

@app.get("/recent")
async def get_recent_trades():
    """
    Returns the last 10 trades.
    """
    if not os.path.exists(PROFIT_LOG_PATH):
        return []
    
    try:
        df = pd.read_csv(PROFIT_LOG_PATH)
        return df.tail(10).to_dict(orient="records")
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
