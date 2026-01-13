# Created: 2026-01-13
from loguru import logger

class PricingEngine:
    def __init__(self):
        self.min_spread_bps = 5 # 0.05% minimum profit
        
    def calculate_intent_price(self, market_price, funding_rate, hedging_cost):
        """
        Calculates the price we can offer the user.
        
        Our Edge: We capture the funding rate, so we can offer a price 
        slightly better than the market while still being profitable.
        
        Args:
            market_price: Current DEX price for the LST
            funding_rate: Annualized funding rate on Hyperliquid (e.g., 0.15)
            hedging_cost: Cost to open the short on Hyperliquid (slippage + fees)
            
        Returns:
            offer_price: The price we bid in the auction
            is_profitable: Boolean
        """
        # Daily funding capture (approximate)
        daily_funding = funding_rate / 365
        
        # We want to beat the market price by 1-2 bps to win the auction
        offer_price = market_price * 0.9999 # 1 bps discount to user
        
        # Profit = (Market - Offer) + Daily_Funding - Hedging_Cost
        # Since we are "selling" the LST to the user:
        # We buy/mint at Market, sell at Offer.
        # But we keep the LST delta-neutral for X days.
        
        # Simplified: If Daily_Funding > Hedging_Cost + Discount_Given
        profit_bps = (daily_funding * 10000) - (hedging_cost * 10000) - 1
        
        is_profitable = profit_bps >= self.min_spread_bps
        
        if is_profitable:
            logger.info(f"Pricing Engine: Profitable intent found! Offer: {offer_price}, Expected Profit: {profit_bps} bps")
        else:
            logger.debug(f"Pricing Engine: Intent not profitable. Profit: {profit_bps} bps")
            
        return offer_price, is_profitable
