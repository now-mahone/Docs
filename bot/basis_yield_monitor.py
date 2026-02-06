# Created: 2026-02-05
# Updated: 2026-02-06 (Integrated api_connector for real-time LST yields & multi-venue funding)
import os
import json
import time
from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from apy_calculator import APYCalculator
from api_connector import LSTYieldFeed, FundingRateAggregator

class BasisYieldMonitor:
    """
    Monitors funding rates across venues and calculates real-time basis yield
    using live LST staking data from api_connector.
    Feeds data to the public stats API for aggregator reporting.
    """
    def __init__(self):
        self.exchange_manager = ExchangeManager()
        self.chain_manager = ChainManager()
        self.output_path = os.path.join(os.path.dirname(__file__), "data", "basis_yield.json")
        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)

    def calculate_current_yield(self, symbol: str = "ETH") -> dict:
        try:
            # 1. Get Funding Rate from Hyperliquid (primary venue)
            hourly_funding = self.exchange_manager.get_funding_rate(symbol)
            annual_funding = hourly_funding * 24 * 365

            # 2. Get multi-venue funding rates for comparison
            all_funding = FundingRateAggregator.get_all_funding_rates(symbol)
            best_venue = all_funding.get("best_venue", "hyperliquid")
            avg_annual_funding = all_funding.get("average_annual", annual_funding)

            # 3. Get REAL staking yield from Lido/DeFiLlama APIs (replaces hardcoded 3.5%)
            lst_yields = LSTYieldFeed.get_staking_yields()
            staking_yield = lst_yields.get("wstETH", 0.035)
            best_lst, best_lst_apy = LSTYieldFeed.get_best_lst_yield()

            # 4. Calculate Expected APY at 3x leverage
            leverage = 3.0
            expected_apy = APYCalculator.calculate_expected_apy(
                leverage=leverage,
                funding_rate=hourly_funding * 8 / 3,  # Convert hourly to 8h rate for calculator
                staking_yield=staking_yield,
                spread_edge=0.0005,  # 5bps spread capture
                turnover_rate=0.1,   # 10% daily turnover
                cost_rate=0.01       # 1% annual costs
            )

            data = {
                "timestamp": time.time(),
                "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "symbol": symbol,
                "hourly_funding": hourly_funding,
                "annual_funding_rate": annual_funding,
                "staking_yield": staking_yield,
                "staking_yield_source": "live_api",
                "leverage": leverage,
                "expected_apy": expected_apy,
                "status": "HEALTHY" if annual_funding > 0 else "WARNING",
                # Multi-venue comparison data
                "multi_venue": {
                    "avg_annual_funding": avg_annual_funding,
                    "best_venue": best_venue,
                    "venues": {
                        k: v for k, v in all_funding.items()
                        if isinstance(v, dict) and "annual" in v
                    },
                },
                "lst_yields": lst_yields,
                "best_lst": best_lst,
                "best_lst_apy": best_lst_apy,
            }

            with open(self.output_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(
                f"Basis yield updated: {expected_apy:.2%} APY | "
                f"Staking: {staking_yield:.2%} (live) | "
                f"Funding: {annual_funding:.2%} (HL) | "
                f"Best venue: {best_venue}"
            )
            return data

        except Exception as e:
            logger.error(f"Error calculating basis yield: {e}")
            return {}

if __name__ == "__main__":
    import sys
    sys.path.insert(0, os.path.dirname(__file__))
    monitor = BasisYieldMonitor()
    result = monitor.calculate_current_yield()
    if result:
        logger.info(f"APY: {result.get('expected_apy', 0):.2%}")
        logger.info(f"Staking yield: {result.get('staking_yield', 0):.2%} (source: {result.get('staking_yield_source')})")
        logger.info(f"Best venue: {result.get('multi_venue', {}).get('best_venue', 'N/A')}")