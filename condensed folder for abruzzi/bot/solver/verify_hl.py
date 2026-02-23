# Created: 2026-01-13
import asyncio
from bot.solver.hyperliquid_provider import HyperliquidProvider
from loguru import logger
import os
from dotenv import load_dotenv

load_dotenv()

async def verify_hl():
    logger.info("Verifying Hyperliquid Connectivity...")
    
    pk = os.getenv("HYPERLIQUID_PRIVATE_KEY")
    if not pk or pk == "your_hyperliquid_private_key":
        logger.error("No private key found in .env")
        return

    provider = HyperliquidProvider()
    
    # 1. Check Account Summary
    summary = await provider.get_account_summary()
    if summary:
        # Handle different response formats
        margin = 0.0
        if isinstance(summary, dict):
            # Check for 'withdrawable' in the user state
            margin = float(summary.get('withdrawable', 0))
            
        logger.success(f"Connected! Margin Available: ${margin}")
        
        if margin < 1.0:
            logger.warning("Balance too low for trading.")
    else:
        logger.error("Failed to fetch account summary. Check API key.")

    # 2. Check Funding Rates
    funding = await provider.get_funding_rate("ETH")
    logger.info(f"Current ETH Annualized Funding: {funding*100:.2f}%")

if __name__ == "__main__":
    asyncio.run(verify_hl())
