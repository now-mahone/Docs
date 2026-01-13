# Created: 2026-01-13
import aiohttp
import asyncio
from loguru import logger
from bot.solver.pricing_engine import PricingEngine
from bot.solver.hyperliquid_provider import HyperliquidProvider
import os

COW_SWAP_API_BASE = "https://api.cow.fi/base/api/v1"

class IntentListener:
    def __init__(self):
        self.pricing_engine = PricingEngine()
        self.hl_provider = HyperliquidProvider()
        self.is_live = os.getenv("SOLVER_LIVE", "false").lower() == "true"
        logger.info(f"Kerne Intent Listener initialized (LIVE={self.is_live})")
        
    async def fetch_orders(self):
        """
        Fetches open orders from CowSwap that match our LST criteria.
        """
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{COW_SWAP_API_BASE}/auction") as resp:
                    if resp.status == 200:
                        auction_data = await resp.json()
                        orders = auction_data.get('orders', [])
                        logger.info(f"Fetched {len(orders)} orders from CowSwap auction")
                        return orders
                    else:
                        logger.error(f"Failed to fetch auction: {resp.status}")
                        return []
            except Exception as e:
                logger.error(f"Error fetching orders: {e}")
                return []

    async def process_order(self, order):
        buy_token = order.get('buyToken', '').lower()
        sell_token = order.get('sellToken', '').lower()
        
        # LST Targets on Base
        # wstETH: 0xc1cba3fc4d133901b3e238628f5514533683e0bf
        # cbETH: 0x2ae3f1ec7f1f5012cfeab2295b6240137331713f
        lst_targets = {
            "0xc1cba3fc4d133901b3e238628f5514533683e0bf": "ETH", # wstETH -> Hedge with ETH
            "0x2ae3f1ec7f1f5012cfeab2295b6240137331713f": "ETH", # cbETH -> Hedge with ETH
        }
        
        if buy_token in lst_targets:
            coin = lst_targets[buy_token]
            buy_amount = int(order.get('buyAmount', 0)) / 1e18
            logger.warning(f"!!! LST INTENT DETECTED: {coin} for {buy_amount} ETH !!!")
            
            # 1. Get Funding Rate
            funding_rate = await self.hl_provider.get_funding_rate(coin)
            
            # 2. Calculate Price
            # In production, we'd fetch real-time DEX price here
            market_price = 1.0 # Simplified for now (1 LST = 1 ETH approx)
            hedging_cost = 0.0005 # 5 bps for HL fees + slippage
            
            offer_price, is_profitable = self.pricing_engine.calculate_intent_price(
                market_price, funding_rate, hedging_cost
            )
            
            if is_profitable:
                logger.success(f"WINNING BID CALCULATED: {offer_price}")
                if self.is_live:
                    # 3. Open Hedge on Hyperliquid
                    success = await self.hl_provider.open_short(coin, buy_amount, leverage=3)
                    if success:
                        logger.success(f"Hedge opened on Hyperliquid for {buy_amount} {coin}")
                        # 4. Submit Bid to CowSwap (Requires Solver API key and signing)
                        logger.info("Submitting bid to CowSwap auction...")
                    else:
                        logger.error("Failed to open hedge, aborting bid.")
                else:
                    logger.info("[DRY RUN] Would have opened hedge and submitted bid.")

    async def listen_loop(self):
        logger.info("Starting Intent Listener loop...")
        while True:
            orders = await self.fetch_orders()
            tasks = [self.process_order(order) for order in orders]
            await asyncio.gather(*tasks)
            await asyncio.sleep(10)

if __name__ == "__main__":
    listener = IntentListener()
    asyncio.run(listener.listen_loop())
