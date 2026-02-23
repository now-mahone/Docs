# Created: 2026-01-26
import asyncio
import time
import aiohttp
from typing import List, Optional, Dict
from loguru import logger
from .base import BaseIntentFetcher, ChainContext, IntentData, IntentVenue

class CowSwapFetcher(BaseIntentFetcher):
    """Fetcher for CowSwap intents."""
    def __init__(self, solver):
        self.solver = solver
        self._last_fetch: Dict[str, float] = {}
        self._health_logged: Dict[str, bool] = {}

    async def fetch_intents(self, context: ChainContext) -> List[IntentData]:
        if not context.config.cowswap_api_base:
            return []

        now = time.time()
        last_fetch = self._last_fetch.get(context.config.name, 0)
        if now - last_fetch < self.solver._min_fetch_interval:
            return []
        self._last_fetch[context.config.name] = now

        intents = []

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    f"{context.config.cowswap_api_base}/auction",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._health_logged.get(context.config.name):
                        self._health_logged[context.config.name] = True
                        if resp.status == 200:
                            logger.info(f"CowSwap: API reachable (endpoint={context.config.cowswap_api_base})")
                        elif resp.status == 403:
                            logger.info("CowSwap: Auction API requires solver registration (403) - using UniswapX only")
                        else:
                            logger.warning(f"CowSwap: API health check failed (status={resp.status})")

                    if resp.status == 200:
                        auction_data = await resp.json()
                        orders = auction_data.get('orders', [])

                        if orders:
                            logger.debug(f"CowSwap: Fetched {len(orders)} orders from auction")

                        for order in orders:
                            intent = self._normalize_order(order, context)
                            if intent:
                                intents.append(intent)

                    elif resp.status == 429:
                        logger.warning("CowSwap: Rate limited (429). Backing off...")
                    else:
                        logger.debug(f"CowSwap: API returned status {resp.status}")

            except asyncio.TimeoutError:
                logger.warning("CowSwap: Request timeout")
            except aiohttp.ClientError as e:
                logger.error(f"CowSwap: Network error: {e}")
            except Exception as e:
                logger.error(f"CowSwap: Unexpected error: {e}")

        return intents

    def _normalize_order(self, order: Dict, context: ChainContext) -> Optional[IntentData]:
        try:
            order_id = order.get('uid', '')
            sell_token = order.get('sellToken', '').lower()
            buy_token = order.get('buyToken', '').lower()
            sell_amount = int(order.get('sellAmount', 0))
            buy_amount = int(order.get('buyAmount', 0))
            valid_to = int(order.get('validTo', 0))
            owner = order.get('owner', '')
            signature = order.get('signature', '')

            if not all([order_id, sell_token, buy_token, sell_amount, buy_amount, owner]):
                return None

            if valid_to < int(time.time()):
                return None

            if not self.solver._is_target_pair(sell_token, buy_token, context):
                return None

            order_data = {
                "token_in_symbol": context.config.token_targets.get(sell_token, "UNKNOWN"),
                "token_out_symbol": context.config.token_targets.get(buy_token, "UNKNOWN"),
            }
            order_data.update(order)

            return IntentData(
                order_id=order_id,
                venue=IntentVenue.COWSWAP,
                user=owner,
                token_in=sell_token,
                token_out=buy_token,
                amount_in=sell_amount,
                amount_out=buy_amount,
                price_limit=buy_amount,
                deadline=valid_to,
                chain=context.config.name,
                signature=signature,
                raw_order=order_data
            )

        except Exception as e:
            logger.error(f"CowSwap: Error normalizing order: {e}")
            return None
