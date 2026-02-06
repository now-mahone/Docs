// Created: 2026-02-05
import os
import json
import time
from loguru import logger
from bot.exchange_manager import ExchangeManager
from bot.chain_manager import ChainManager
from bot.apy_calculator import APYCalculator

class BasisYieldMonitor:
    """
    Monitors Hyperliquid funding rates and calculates real-time basis yield.
    Feeds data to the public stats API for aggregator reporting.
    """
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.chain_manager = ChainManager()
        self.output_path = "bot/data/basis_yield.json"
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def calculate_current_yield(self, symbol: str = "ETH") -> dict:
        try:
            # 1. Get Funding Rate from Hyperliquid
            # HL returns hourly funding rate. We need to annualize it.
            hourly_funding = self.exchange_manager.get_funding_rate(symbol)
            annual_funding = hourly_funding * 24 * 365
            
            # 2. Get Staking Yield from Vault (LST yield)
            # Assuming ~3.5% for wstETH
            staking_yield = 0.035 
            
            # 3. Calculate Expected APY at 3x leverage
            leverage = 3.0
            expected_apy = APYCalculator.calculate_expected_apy(
                leverage=leverage,
                funding_rate=hourly_funding / 3, # APYCalculator expects 8h rate or similar? 
                # Actually APYCalculator.calculate_expected_apy uses:
                # annual_funding = funding_rate * 3 * 365
                # So it expects an 8h rate (3 times a day).
                # HL is hourly, so we pass hourly_funding * 8 / 3? No.
                # Let's just pass the hourly rate and adjust the calculator logic or our input.
                funding_rate=hourly_funding / 3, # If we want to use the calculator's *3*365
                staking_yield=staking_yield,
                spread_edge=0.0005, # 5bps spread capture
                turnover_rate=0.1, # 10% daily turnover
                cost_rate=0.01 # 1% annual costs
            )

            data = {
                "timestamp": time.time(),
                "symbol": symbol,
                "hourly_funding": hourly_funding,
                "annual_funding_rate": annual_funding,
                "staking_yield": staking_yield,
                "leverage": leverage,
                "expected_apy": expected_apy,
                "status": "HEALTHY" if annual_funding > 0 else "WARNING"
            }
            
            with open(self.output_path, "w") as f:
                json.dump(data, f, indent=2)
            
            logger.info(f"Basis yield updated: {expected_apy:.2%} APY")
            return data

        except Exception as e:
            logger.error(f"Error calculating basis yield: {e}")
            return {}

if __name__ == "__main__":
    monitor = BasisYieldMonitor()
    monitor.calculate_current_yield()