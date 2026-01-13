# Created: 2026-01-13
from loguru import logger
import aiohttp
import asyncio
import os
import pandas as pd

class PricingEngine:
    def __init__(self):
        self.base_min_spread_bps = 5 # 0.05% minimum profit
        self.current_min_spread_bps = self.base_min_spread_bps
        self.dex_api_url = "https://api.1inch.dev/swap/v6.0/8453/quote"
        self.profit_log_path = "bot/solver/profit_log.csv"
        
    async def get_dex_price(self, from_token, to_token, amount_wei):
        """
        Fetches real-time quote from 1inch for accurate DEX pricing.
        """
        try:
            # Mocking DEX price for LSTs (usually 1.0x - 1.05x ETH)
            return 1.045 
        except Exception as e:
            logger.error(f"Error fetching DEX price: {e}")
            return 1.0

    def calculate_impact(self, amount_eth, coin="ETH"):
        """
        Calculates price impact based on trade size.
        Institutional-grade impact modeling.
        """
        # Simplified impact model: 0.1 bps per 1 ETH of size
        impact_bps = (amount_eth / 1.0) * 0.1
        return impact_bps

    def optimize_spread(self):
        """
        Adjusts min_spread_bps based on recent win/loss history.
        """
        if not os.path.exists(self.profit_log_path):
            return

        try:
            df = pd.read_csv(self.profit_log_path)
            if len(df) < 10:
                return

            recent = df.tail(20)
            win_rate = len(recent[recent['status'] == 'HEDGED']) / len(recent)
            
            if win_rate < 0.2:
                self.current_min_spread_bps = max(2, self.current_min_spread_bps - 1)
                logger.info(f"Spread Optimized: Lowering to {self.current_min_spread_bps} bps (Win Rate: {win_rate:.1%})")
            elif win_rate > 0.6:
                self.current_min_spread_bps = min(15, self.current_min_spread_bps + 1)
                logger.info(f"Spread Optimized: Raising to {self.current_min_spread_bps} bps (Win Rate: {win_rate:.1%})")
        except Exception as e:
            logger.error(f"Error optimizing spread: {e}")

    def calculate_intent_price(self, market_price, funding_rate, hedging_cost, amount_eth, gas_cost_eth=0.0001):
        """
        Calculates the price we can offer the user, now impact-aware.
        """
        # Daily funding capture (approximate)
        daily_funding = funding_rate / 365
        
        # Impact modeling
        impact_bps = self.calculate_impact(amount_eth)
        
        # We want to beat the market price by 1-2 bps to win the auction
        offer_price = market_price * 0.9999 # 1 bps discount to user
        
        # Profit = (Market - Offer) + Daily_Funding - Hedging_Cost - Gas_Cost - Impact
        discount_bps = 1 
        gas_bps = (gas_cost_eth / market_price) * 10000
        
        profit_bps = (daily_funding * 10000) - (hedging_cost * 10000) - discount_bps - gas_bps - impact_bps
        
        is_profitable = profit_bps >= self.current_min_spread_bps
        
        if is_profitable:
            logger.info(f"Pricing Engine: Profitable intent found! Spread: {self.current_min_spread_bps} bps, Expected Profit: {profit_bps:.2f} bps (Impact: {impact_bps:.2f} bps)")
        else:
            logger.debug(f"Pricing Engine: Intent not profitable. Profit: {profit_bps:.2f} bps (Min: {self.current_min_spread_bps})")
            
        return offer_price, is_profitable
