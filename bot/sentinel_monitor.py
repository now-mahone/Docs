import asyncio
import time
from loguru import logger
from typing import Dict, List
from chain_manager import ChainManager
from exchange_manager import ExchangeManager
from sentinel.risk_engine import RiskEngine

# Created: 2026-01-12

class SentinelMonitor:
    """
    Kerne Sentinel: Real-time Liquidation & Rebalancing Monitor.
    Monitors health factors across all venues and triggers flash-rebalancing.
    """
    def __init__(self):
        self.chain = ChainManager()
        self.exchange = ExchangeManager()
        self.risk_engine = RiskEngine(w3=self.chain.w3, private_key=self.chain.private_key)
        
        # Multi-venue support
        self.venues = {
            "binance": self.exchange,
            "bybit": ExchangeManager("bybit"),
            "okx": ExchangeManager("okx")
        }
        
        self.REBALANCE_THRESHOLD = 0.05 # 5% deviation triggers rebalance
        self.CRITICAL_CR = 1.30 # 130% Collateral Ratio

    async def monitor_loop(self):
        """
        Main monitoring loop.
        """
        logger.info("Sentinel Monitor starting...")
        while True:
            try:
                await self.check_health()
                await asyncio.sleep(15) # High-frequency monitoring
            except Exception as e:
                logger.error(f"Monitor loop error: {e}")
                await asyncio.sleep(5)

    async def check_health(self):
        """
        Checks health factors and triggers rebalancing if necessary.
        """
        vault_tvl = self.chain.get_vault_tvl()
        price = self.exchange.get_market_price('ETH/USDT')
        
        total_short = 0.0
        venue_data = {}
        
        for name, ex in self.venues.items():
            try:
                pos, pnl = ex.get_short_position('ETH/USDT:USDT')
                collateral = ex.get_collateral_balance('USDT')
                total_short += pos
                
                cr = (collateral + pnl) / (pos * price) if pos > 0 else 10.0
                venue_data[name] = {"pos": pos, "cr": cr}
                
                if cr < self.CRITICAL_CR:
                    logger.critical(f"CRITICAL HEALTH on {name}: CR {cr:.2f}. Triggering Flash-Rebalance.")
                    await self.flash_rebalance(name)
            except Exception as e:
                logger.error(f"Failed to fetch health for {name}: {e}")

        # Global Delta Check
        delta = vault_tvl - total_short
        if abs(delta) / vault_tvl > self.REBALANCE_THRESHOLD:
            logger.warning(f"Global Delta Deviation: {delta:.4f} ETH ({abs(delta)/vault_tvl:.2%}). Triggering rebalance.")
            # Rebalancing logic is handled by the main engine, but Sentinel can trigger it
            from engine import HedgingEngine
            engine = HedgingEngine(self.exchange, self.chain)
            engine.run_cycle()

    async def flash_rebalance(self, failing_venue: str):
        """
        Moves funds from a healthy venue to a failing one or closes positions.
        """
        logger.warning(f"Initiating Flash-Rebalance for {failing_venue}...")
        # 1. Find healthiest venue
        healthiest = max(self.venues.keys(), key=lambda v: self.venues[v].get_collateral_balance('USDT') if v != failing_venue else 0)
        
        # 2. In a real scenario, we'd use CEX internal transfers or on-chain bridging
        # For now, we'll reduce position on failing venue to restore CR
        pos, _ = self.venues[failing_venue].get_short_position('ETH/USDT:USDT')
        reduction = pos * 0.2 # Reduce by 20%
        
        logger.info(f"Reducing position on {failing_venue} by {reduction:.4f} ETH to restore health.")
        self.venues[failing_venue].execute_buy('ETH/USDT:USDT', reduction)
        
        # 3. Increase position on healthiest venue to maintain delta-neutrality
        logger.info(f"Increasing position on {healthiest} by {reduction:.4f} ETH to maintain delta.")
        self.venues[healthiest].execute_short('ETH/USDT:USDT', reduction)

if __name__ == "__main__":
    monitor = SentinelMonitor()
    asyncio.run(monitor.monitor_loop())
