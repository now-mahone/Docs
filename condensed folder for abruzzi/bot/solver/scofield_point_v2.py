# Created: 2026-01-13
import math
from loguru import logger
import pandas as pd
import os

def calculate_scofield_point_v2(funding_rate: float, lst_yield: float, volatility: float, solver_revenue_bps: float = 0.0, risk_aversion: float = 2.0) -> float:
    """
    Calculates the optimal leverage (Scofield Point v2) including solver revenue.
    
    Formula: L* = (Funding_Rate + LST_Yield + Solver_Revenue_Capture) / (Volatility^2 * Risk_Aversion_Factor)
    """
    try:
        if volatility <= 0:
            return 1.0
            
        # Solver revenue capture is annualized bps
        solver_yield = solver_revenue_bps / 10000
        
        numerator = funding_rate + lst_yield + solver_yield
        denominator = (volatility ** 2) * risk_aversion
        
        optimal_leverage = numerator / denominator
        
        # Safety bounds: Higher cap for v2 due to solver edge
        clamped_leverage = max(0.5, min(5.0, optimal_leverage))
        
        logger.info(f"Scofield Point v2: Funding={funding_rate:.2%}, Solver={solver_yield:.2%}, Vol={volatility:.2%}")
        logger.info(f"Optimal Leverage: {optimal_leverage:.2f}x (Clamped to {clamped_leverage:.2f}x)")
        
        return clamped_leverage
    except Exception as e:
        logger.error(f"Error calculating Scofield Point v2: {e}")
        return 1.0

def get_recent_solver_revenue_bps():
    """
    Fetches the last 24h solver revenue from the profit log.
    """
    log_path = "bot/solver/profit_log.csv"
    if not os.path.exists(log_path):
        return 0.0
    try:
        df = pd.read_csv(log_path)
        # Simplified: sum of last 50 trades
        recent_profit = df[df['status'] == 'HEDGED']['profit_bps'].tail(50).sum()
        return float(recent_profit)
    except Exception as e:
        logger.error(f"Error reading profit log: {e}")
        return 0.0
