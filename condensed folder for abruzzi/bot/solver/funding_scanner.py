# Created: 2026-01-13
import time
from loguru import logger
from bot.solver.hyperliquid_provider import HyperliquidProvider
from bot.solver.scofield_point import calculate_scofield_point

class FundingScanner:
    def __init__(self, provider: HyperliquidProvider):
        self.provider = provider
        self.min_annualized_funding = 0.15 # 15% APR minimum to consider
        
    def scan(self):
        """Scans for the best funding opportunities."""
        logger.info("Scanning Hyperliquid for funding opportunities...")
        rates = self.provider.get_all_funding_rates()
        
        opportunities = [r for r in rates if r["funding_rate_annualized"] >= self.min_annualized_funding]
        
        if not opportunities:
            logger.info("No high-yield funding opportunities found.")
            return []
            
        logger.info(f"Found {len(opportunities)} opportunities above {self.min_annualized_funding:.0%}")
        for opt in opportunities[:5]: # Show top 5
            logger.info(f"Pair: {opt['symbol']} | APR: {opt['funding_rate_annualized']:.2%} | Price: ${opt['mark_price']:.4f}")
            
        return opportunities

    def get_best_opportunity(self):
        opportunities = self.scan()
        if opportunities:
            return opportunities[0]
        return None

if __name__ == "__main__":
    # Quick test
    try:
        provider = HyperliquidProvider()
        scanner = FundingScanner(provider)
        scanner.scan()
    except Exception as e:
        print(f"Setup error: {e}")
