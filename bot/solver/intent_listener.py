# Created: 2026-01-13
import aiohttp
import asyncio
from loguru import logger
from bot.solver.pricing_engine import PricingEngine
from bot.solver.hyperliquid_provider import HyperliquidProvider
import os
import json
import time

COW_SWAP_API_BASE = "https://api.cow.fi/base/api/v1"
UNISWAP_X_API_BASE = "https://api.uniswap.org/v2/uniswapx/orders" # Example endpoint

class IntentListener:
    def __init__(self):
        self.pricing_engine = PricingEngine()
        self.hl_provider = HyperliquidProvider()
        self.is_live = os.getenv("SOLVER_LIVE", "false").lower() == "true"
        self.profit_log_path = "bot/solver/profit_log.csv"
        self._init_log()
        logger.info(f"Kerne Intent Listener initialized (LIVE={self.is_live})")
        
    def _init_log(self):
        if not os.path.exists(self.profit_log_path):
            with open(self.profit_log_path, "w") as f:
                f.write("timestamp,venue,order_id,coin,amount,profit_bps,status\n")

    def log_profit(self, venue, order_id, coin, amount, profit_bps, status):
        with open(self.profit_log_path, "a") as f:
            f.write(f"{time.time()},{venue},{order_id},{coin},{amount},{profit_bps},{status}\n")

    async def fetch_cowswap_orders(self):
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(f"{COW_SWAP_API_BASE}/auction") as resp:
                    if resp.status == 200:
                        auction_data = await resp.json()
                        return auction_data.get('orders', [])
                    return []
            except Exception as e:
                logger.error(f"Error fetching CowSwap orders: {e}")
                return []

    async def fetch_uniswapx_orders(self):
        # UniswapX integration placeholder
        # In production, we'd poll their orderbook API
        return []

    async def process_order(self, order, venue="CowSwap"):
        buy_token = order.get('buyToken', '').lower()
        
        # LST Targets on Base
        lst_targets = {
            "0xc1cba3fc4d133901b3e238628f5514533683e0bf": "ETH", # wstETH
            "0x2ae3f1ec7f1f5012cfeab2295b6240137331713f": "ETH", # cbETH
            "0x2416092f14337c05d1e22757d24c3e1749e03b44": "ETH", # rETH
            "0x9e5aac1ba1a2e6aed6b32689dfcf62a509ca96f3": "ETH", # stEUR (Hedge with ETH for now or EUR perps)
        }
        
        if buy_token in lst_targets:
            coin = lst_targets[buy_token]
            buy_amount_wei = int(order.get('buyAmount', 0))
            buy_amount = buy_amount_wei / 1e18
            order_id = order.get('uid') or order.get('orderHash')
            
            logger.warning(f"!!! {venue} LST INTENT DETECTED: {coin} for {buy_amount} ETH !!!")
            
            # 1. Get Funding Rate
            funding_rate = await self.hl_provider.get_funding_rate(coin)
            
            # 2. Get Real-time DEX Price
            market_price = await self.pricing_engine.get_dex_price(buy_token, "0x4200000000000000000000000000000000000006", buy_amount_wei)
            
            hedging_cost = 0.0005 # 5 bps
            
            offer_price, is_profitable = self.pricing_engine.calculate_intent_price(
                market_price, funding_rate, hedging_cost
            )
            
            if is_profitable:
                # Calculate expected profit in bps for logging
                daily_funding = funding_rate / 365
                profit_bps = (daily_funding * 10000) - (hedging_cost * 10000) - 1
                
                logger.success(f"WINNING BID CALCULATED: {offer_price}")
                if self.is_live:
                    success = await self.hl_provider.open_short(coin, buy_amount, leverage=3)
                    if success:
                        logger.success(f"Hedge opened on Hyperliquid for {buy_amount} {coin}")
                        self.log_profit(venue, order_id, coin, buy_amount, profit_bps, "HEDGED")
                    else:
                        logger.error("Failed to open hedge, aborting bid.")
                        self.log_profit(venue, order_id, coin, buy_amount, profit_bps, "HEDGE_FAILED")
                else:
                    logger.info("[DRY RUN] Would have opened hedge and submitted bid.")
                    self.log_profit(venue, order_id, coin, buy_amount, profit_bps, "DRY_RUN")

    async def listen_loop(self):
        logger.info("Starting Intent Listener loop...")
        while True:
            # Optimize spread based on history
            self.pricing_engine.optimize_spread()
            
            # Fetch from multiple venues
            cow_orders = await self.fetch_cowswap_orders()
            uni_orders = await self.fetch_uniswapx_orders()
            
            tasks = []
            for order in cow_orders:
                tasks.append(self.process_order(order, "CowSwap"))
            for order in uni_orders:
                tasks.append(self.process_order(order, "UniswapX"))
                
            if tasks:
                await asyncio.gather(*tasks)
                
            await asyncio.sleep(10)

if __name__ == "__main__":
    listener = IntentListener()
    asyncio.run(listener.listen_loop())
