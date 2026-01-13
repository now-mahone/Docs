# Created: 2026-01-13
import asyncio
from loguru import logger
from bot.solver.hyperliquid_provider import HyperliquidProvider
from bot.chain_manager import ChainManager
import os
import time

class SolverSentinel:
    """
    Monitors the solver's health and rebalances collateral between 
    Base (Vault) and Hyperliquid (Margin).
    """
    def __init__(self):
        self.hl_provider = HyperliquidProvider()
        self.chain_manager = ChainManager()
        self.target_leverage = 3.0
        self.max_leverage = 5.0
        self.min_margin_usd = 500.0 # Minimum buffer on HL
        
    async def check_and_rebalance(self):
        """
        Checks HL margin and Base vault balance to ensure we have 
        enough collateral for new hedges.
        """
        logger.info("Sentinel: Checking solver health and collateral...")
        
        # 1. Get HL Account Summary
        user_state = await self.hl_provider.get_account_summary()
        if not user_state:
            logger.error("Sentinel: Could not fetch HL user state")
            return

        margin_summary = user_state.get('marginSummary', {})
        account_value = float(margin_summary.get('accountValue', 0))
        total_margin_used = float(margin_summary.get('marginUsed', 0))
        
        current_leverage = total_margin_used / account_value if account_value > 0 else 0
        logger.info(f"Sentinel: HL Account Value: ${account_value:.2f}, Current Leverage: {current_leverage:.2fx}")

        # 2. Check if leverage is too high
        if current_leverage > self.max_leverage:
            logger.warning(f"Sentinel: Leverage too high ({current_leverage:.2fx})! Need to deleverage or add collateral.")
            # In production, we'd trigger an alert or automated deposit from vault
            
        # 3. Check if margin is too low for new trades
        if account_value < self.min_margin_usd:
            logger.warning(f"Sentinel: HL Margin low (${account_value:.2f}). Minimum: ${self.min_margin_usd}")
            # Trigger deposit logic here
            
    async def run_loop(self):
        logger.info("Starting Solver Sentinel loop...")
        while True:
            try:
                await self.check_and_rebalance()
            except Exception as e:
                logger.error(f"Sentinel Loop Error: {e}")
            await asyncio.sleep(300) # Check every 5 minutes

if __name__ == "__main__":
    sentinel = SolverSentinel()
    asyncio.run(sentinel.run_loop())
