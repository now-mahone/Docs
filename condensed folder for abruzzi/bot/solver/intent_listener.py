# Created: 2026-01-13
import aiohttp
import asyncio
from loguru import logger
from bot.solver.pricing_engine import PricingEngine
from bot.solver.hyperliquid_provider import HyperliquidProvider
import os
import time

COW_SWAP_API_BASE = "https://api.cow.fi/base/api/v1"

# UniswapX API endpoints per chain
UNISWAPX_API_CONFIG = {
    "base": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 8453,
        "order_type": "Priority",  # Base uses Priority Orders
        "reactor": "0x000000001Ec5656dcdB24D90DFa42742738De729"
    },
    "unichain": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 130,
        "order_type": "Priority",  # Unichain uses Priority Orders
        "reactor": "0x00000006021a6Bce796be7ba509BBBA71e956e37"
    },
    "arbitrum": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 42161,
        "order_type": "Dutch_V2",  # Arbitrum uses Dutch V2
        "reactor": "0x1bd1aAdc9E230626C44a139d7E70d842749351eb"
    },
    "mainnet": {
        "api_url": "https://api.uniswap.org/v2/orders",
        "chain_id": 1,
        "order_type": "Dutch_V2",  # Mainnet uses Dutch V2 with RFQ
        "reactor": "0x6000da47483062A0D734Ba3dc7576Ce6A0B645C4"
    }
}

class IntentListener:
    def __init__(self):
        self.pricing_engine = PricingEngine()
        self.hl_provider = HyperliquidProvider()
        self.is_live = os.getenv("SOLVER_LIVE", "false").lower() == "true"
        self.profit_log_path = "bot/solver/profit_log.csv"
        self.active_chain = os.getenv("ACTIVE_CHAIN", "base").lower()
        self.uniswapx_config = UNISWAPX_API_CONFIG.get(self.active_chain, UNISWAPX_API_CONFIG["base"])
        self._uniswapx_health_logged = False
        self._init_log()
        logger.info(f"Kerne Intent Listener initialized (LIVE={self.is_live}, Chain={self.active_chain})")
        
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
        """
        Fetches open orders from the UniswapX API for the active chain.
        Supports Priority Orders (Base/Unichain) and Dutch V2 (Arbitrum/Mainnet).
        
        API Docs: https://api.uniswap.org/v2/uniswapx/docs
        """
        config = self.uniswapx_config
        api_url = config["api_url"]
        chain_id = config["chain_id"]
        order_type = config["order_type"]
        
        params = {
            "orderStatus": "open",
            "chainId": chain_id,
            "orderType": order_type,
            "limit": 100,  # Max orders per request
        }
        
        headers = {
            "Accept": "application/json",
            "Origin": "https://app.uniswap.org"
        }
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(api_url, params=params, headers=headers) as resp:
                    if not self._uniswapx_health_logged:
                        self._uniswapx_health_logged = True
                        if resp.status == 200:
                            logger.info(
                                "UniswapX: API reachable (chainId={}, orderType={}, endpoint={})".format(
                                    chain_id,
                                    order_type,
                                    api_url
                                )
                            )
                        else:
                            logger.warning(
                                "UniswapX: API health check failed (status={}, chainId={}, endpoint={})".format(
                                    resp.status,
                                    chain_id,
                                    api_url
                                )
                            )

                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('orders', [])
                        
                        if orders:
                            logger.info(f"UniswapX: Fetched {len(orders)} open orders on chain {chain_id}")
                        
                        # Normalize UniswapX orders to match CowSwap format for unified processing
                        normalized_orders = []
                        for order in orders:
                            normalized = self._normalize_uniswapx_order(order)
                            if normalized:
                                normalized_orders.append(normalized)
                        
                        return normalized_orders
                    elif resp.status == 429:
                        logger.warning("UniswapX: Rate limited (429). Backing off...")
                        return []
                    else:
                        logger.debug(f"UniswapX: API returned status {resp.status}")
                        return []
            except aiohttp.ClientError as e:
                logger.error(f"UniswapX: Network error fetching orders: {e}")
                return []
            except Exception as e:
                logger.error(f"UniswapX: Unexpected error fetching orders: {e}")
                return []
    
    def _normalize_uniswapx_order(self, uniswapx_order: dict) -> dict:
        """
        Normalizes UniswapX order format to match the internal format used by process_order().
        
        UniswapX Order Structure (Priority/Dutch):
        {
            "orderHash": "0x...",
            "orderStatus": "open",
            "chainId": 8453,
            "input": {"token": "0x...", "amount": "1000000000000000000"},
            "outputs": [{"token": "0x...", "amount": "..."}],
            "swapper": "0x...",
            "createdAt": 1234567890,
            "encodedOrder": "0x..."
        }
        
        Internal format (CowSwap-like):
        {
            "orderHash": "0x...",
            "buyToken": "0x...",
            "buyAmount": "...",
            "sellToken": "0x...",
            "sellAmount": "...",
            "_raw": {...}  # Original order for submission
        }
        """
        try:
            order_hash = uniswapx_order.get('orderHash', '')
            
            # Extract input (what the user is selling)
            input_data = uniswapx_order.get('input', {})
            sell_token = input_data.get('token', '').lower()
            sell_amount = input_data.get('amount', '0')
            
            # Extract outputs (what the user wants to buy)
            # UniswapX can have multiple outputs, we take the primary one
            outputs = uniswapx_order.get('outputs', [])
            if not outputs:
                return None
            
            primary_output = outputs[0]
            buy_token = primary_output.get('token', '').lower()
            buy_amount = primary_output.get('amount', '0')
            
            # Skip if missing critical data
            if not buy_token or not buy_amount or buy_amount == '0':
                return None
            
            normalized = {
                "orderHash": order_hash,
                "uid": order_hash,  # Alias for compatibility
                "buyToken": buy_token,
                "buyAmount": buy_amount,
                "sellToken": sell_token,
                "sellAmount": sell_amount,
                "swapper": uniswapx_order.get('swapper', ''),
                "chainId": uniswapx_order.get('chainId', 8453),
                "createdAt": uniswapx_order.get('createdAt', 0),
                "encodedOrder": uniswapx_order.get('encodedOrder', ''),
                "_venue": "UniswapX",
                "_order_type": uniswapx_order.get('type', 'Priority'),
                "_raw": uniswapx_order  # Keep raw for submission
            }
            
            return normalized
            
        except Exception as e:
            logger.error(f"UniswapX: Error normalizing order: {e}")
            return None

    async def process_order(self, order, venue="CowSwap"):
        buy_token = order.get('buyToken', '').lower()
        
        # Micro-scale safety check
        account_summary = await self.hl_provider.get_account_summary()
        if account_summary:
            margin_available = float(account_summary.get('withdrawable', 0))
            if margin_available < 5.0:
                logger.error(f"Micro-scale Safety: Insufficient margin (${margin_available}). Need at least $5.")
                return

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
                market_price, funding_rate, hedging_cost, buy_amount
            )
            
            if is_profitable:
                # Calculate expected profit in bps for logging
                daily_funding = funding_rate / 365
                profit_bps = (daily_funding * 10000) - (hedging_cost * 10000) - 1
                
                # Micro-scale position cap
                # WETH address on Base, using a dummy to_token for price fetch
                eth_price = await self.pricing_engine.get_dex_price(
                    "0x4200000000000000000000000000000000000006",  # WETH
                    "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",  # USDC on Base
                    int(1e18)
                )
                position_usd = buy_amount * eth_price
                if position_usd > 15.0:
                    logger.warning(f"Micro-scale Safety: Position size ${position_usd:.2f} exceeds $15 cap. Scaling down.")
                    buy_amount = 15.0 / eth_price

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
