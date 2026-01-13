# Created: 2026-01-13
import math
from loguru import logger

def calculate_scofield_point(funding_rate: float, lst_yield: float, volatility: float, risk_aversion: float = 2.0) -> float:
    """
    Calculates the optimal leverage (Scofield Point) for delta-neutral hedging.
    
    Formula: L* = (Funding_Rate + LST_Yield) / (Volatility^2 * Risk_Aversion_Factor)
    
    Args:
        funding_rate: Annualized funding rate (e.g., 0.10 for 10%)
        lst_yield: Annualized LST yield (e.g., 0.04 for 4%)
        volatility: Annualized volatility of the underlying asset (e.g., 0.50 for 50%)
        risk_aversion: Risk aversion factor (default 2.0)
        
    Returns:
        Optimal leverage factor (e.g., 1.5)
    """
    try:
        if volatility <= 0:
            return 1.0
            
        numerator = funding_rate + lst_yield
        denominator = (volatility ** 2) * risk_aversion
        
        optimal_leverage = numerator / denominator
        
        # Safety bounds: Never go below 0.5x or above 3.0x for delta-neutral stability
        clamped_leverage = max(0.5, min(3.0, optimal_leverage))
        
        logger.info(f"Scofield Point Calculation: Funding={funding_rate:.2%}, Yield={lst_yield:.2%}, Vol={volatility:.2%}")
        logger.info(f"Optimal Leverage: {optimal_leverage:.2f}x (Clamped to {clamped_leverage:.2f}x)")
        
        return clamped_leverage
    except Exception as e:
        logger.error(f"Error calculating Scofield Point: {e}")
        return 1.0 # Default to 1x leverage on error
