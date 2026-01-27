# Created: 2026-01-26
import time
import aiohttp
import os
from typing import List, Optional, Dict
from loguru import logger
from .base import BaseIntentFetcher, ChainContext, IntentData, IntentVenue

ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY")

class FusionIntentFetcher(BaseIntentFetcher):
    """Fetcher for 1inch Fusion intents."""
    def __init__(self, solver):
        self.solver = solver
        self._last_fetch: Dict[str, float] = {}
        self._health_logged: Dict[str, bool] = {}

    async def fetch_intents(self, context: ChainContext) -> List[IntentData]:
        if not ONE_INCH_API_KEY:
            return []

        now = time.time()
        last_fetch = self._last_fetch.get(context.config.name, 0)
        if now - last_fetch < self.solver._min_fetch_interval:
            return []
        self._last_fetch[context.config.name] = now

        intents = []
        # 1inch Fusion Orderbook API
        url = f"https://api.1inch.dev/fusion/v1.0/{context.config.chain_id}/orders/all"
        
        params = {
            "limit": 50,
            "status": "active"
        }
        
        headers = {
            "Authorization": f"Bearer {ONE_INCH_API_KEY}",
            "Accept": "application/json"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._health_logged.get(context.config.name):
                        self._health_logged[context.config.name] = True
                        if resp.status == 200:
                            logger.info(f"1inch Fusion: API reachable (chainId={context.config.chain_id})")
                        else:
                            logger.warning(f"1inch Fusion: API health check failed (status={resp.status})")

                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('items', [])

                        if orders:
                            logger.debug(f"1inch Fusion: Fetched {len(orders)} active orders")

                        for order_wrapper in orders:
                            order = order_wrapper.get('order', {})
                            intent = self._normalize_order(order, context)
                            if intent:
                                intents.append(intent)

                    elif resp.status == 429:
                        logger.warning("1inch Fusion: Rate limited")
                    else:
                        logger.debug(f"1inch Fusion: API returned status {resp.status}")

            except Exception as e:
                logger.error(f"1inch Fusion: Error fetching orders: {e}")

        return intents

    def _normalize_order(self, order: Dict, context: ChainContext) -> Optional[IntentData]:
        try:
            order_hash = order.get('orderHash', '')
            maker_asset = order.get('makerAsset', '').lower()
            taker_asset = order.get('takerAsset', '').lower()
            making_amount = int(order.get('makingAmount', 0))
            taking_amount = int(order.get('takingAmount', 0))
            maker = order.get('maker', '')
            
            if not all([order_hash, maker_asset, taker_asset, making_amount, taking_amount, maker]):
                return None

            if not self.solver._is_target_pair(maker_asset, taker_asset, context):
                return None

            # Fusion orders are Dutch auctions
            deadline = int(time.time()) + 300 # Default fallback

            order_data = {
                "token_in_symbol": context.config.token_targets.get(maker_asset, "UNKNOWN"),
                "token_out_symbol": context.config.token_targets.get(taker_asset, "UNKNOWN"),
            }
            order_data.update(order)

            return IntentData(
                order_id=order_hash,
                venue=IntentVenue.FUSION,
                user=maker,
                token_in=maker_asset,
                token_out=taker_asset,
                amount_in=making_amount,
                amount_out=taking_amount,
                price_limit=taking_amount,
                deadline=deadline,
                chain=context.config.name,
                raw_order=order_data
            )

        except Exception as e:
            logger.error(f"1inch Fusion: Error normalizing order: {e}")
            return None
