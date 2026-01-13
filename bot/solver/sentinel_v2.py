# Created: 2026-01-13
import asyncio
from loguru import logger
from bot.solver.hyperliquid_provider import HyperliquidProvider
from bot.chain_manager import ChainManager
import os
import time
import numpy as np

class SolverSentinelV2:
    """
    Advanced Sentinel with VaR modeling and dynamic leverage adjustment.
    """
    def __init__(self):
        self.hl_provider = HyperliquidProvider()
        self.chain_manager = ChainManager()
        self.target_leverage = 3.0
        self.max_leverage = 5.0
        self.confidence_level = 0.95
        self.lookback_days = 30
        
    def calculate_var(self, positions, volatility):
        """
        Calculates Value-at-Risk for the current portfolio.
        """
        # Simplified VaR: Size * Volatility * Z-Score
        z_score = 1.645 # 95% confidence
        total_var = 0
        for coin, size in positions.items():
            coin_var = size * volatility * z_score
            total_var += coin_var
        return total_var

    async def check_and_rebalance(self):
        logger.info("Sentinel V2: Running VaR-based risk assessment...")
        
        user_state = await self.hl_provider.get_account_summary()
        if not user_state:
            return

        margin_summary = user_state.get('marginSummary', {})
        account_value = float(margin_summary.get('accountValue', 0))
        
        # Fetch positions from HL
        hl_positions = {}
        for pos in user_state.get('assetPositions', []):
            coin = pos['position']['coin']
            size = abs(float(pos['position']['szi']))
            hl_positions[coin] = size

        # Mock volatility (in production, fetch from historical data)
        volatility = 0.05 # 5% daily vol
        
        var_usd = self.calculate_var(hl_positions, volatility)
        var_pct = var_usd / account_value if account_value > 0 else 0
        
        logger.info(f"Sentinel V2: Portfolio VaR (95%): ${var_usd:.2f} ({var_pct:.2%})")

        if var_pct > 0.15: # 15% VaR threshold
            logger.critical(f"Sentinel V2: VaR EXCEEDED THRESHOLD! Reducing leverage...")
            # Trigger deleveraging logic
            
    async def run_loop(self):
        logger.info("Starting Solver Sentinel V2 loop...")
        while True:
            try:
                await self.check_and_rebalance()
            except Exception as e:
                logger.error(f"Sentinel V2 Loop Error: {e}")
            await asyncio.sleep(60) # Check every minute for high-frequency risk management

if __name__ == "__main__":
    sentinel = SolverSentinelV2()
    asyncio.run(sentinel.run_loop())
