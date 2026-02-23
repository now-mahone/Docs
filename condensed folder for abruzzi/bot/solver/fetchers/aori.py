# Created: 2026-01-26
import time
import aiohttp
from typing import List, Optional, Dict
from loguru import logger
from .base import BaseIntentFetcher, ChainContext, IntentData, IntentVenue

class AoriIntentFetcher(BaseIntentFetcher):
    """Fetcher for Aori intents."""
    def __init__(self, solver):
        self.solver = solver
        self._last_fetch: Dict[str, float] = {}
        self._health_logged: Dict[str, bool] = {}

    async def fetch_intents(self, context: ChainContext) -> List[IntentData]:
        now = time.time()
        last_fetch = self._last_fetch.get(context.config.name, 0)
        if now - last_fetch < self.solver._min_fetch_interval:
            return []
        self._last_fetch[context.config.name] = now

        intents = []
        # Aori HTTP API
        url = "https://api.aori.io/data/query"
        
        params = {
            "chainId": context.config.chain_id,
            "status": "open"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    url,
                    params=params,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._health_logged.get(context.config.name):
                        self._health_logged[context.config.name] = True
                        if resp.status == 200:
                            logger.info(f"Aori: API reachable (chainId={context.config.chain_id})")
                        else:
                            logger.warning(f"Aori: API health check failed (status={resp.status})")

                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('orders', [])

                        if orders:
                            logger.debug(f"Aori: Fetched {len(orders)} open orders")

                        for order in orders:
                            intent = self._normalize_order(order, context)
                            if intent:
                                intents.append(intent)

            except Exception as e:
                logger.error(f"Aori: Error fetching intents: {e}")

        return intents

    def _normalize_order(self, order: Dict, context: ChainContext) -> Optional[IntentData]:
        try:
            order_hash = order.get('orderHash', '')
            input_token = order.get('inputToken', '').lower()
            output_token = order.get('outputToken', '').lower()
            input_amount = int(order.get('inputAmount', 0))
            output_amount = int(order.get('outputAmount', 0))
            offerer = order.get('offerer', '')
            
            if not all([order_hash, input_token, output_token, input_amount, output_amount, offerer]):
                return None

            if not self.solver._is_target_pair(input_token, output_token, context):
                return None

            deadline = int(order.get('endTime', 0))

            order_data = {
                "token_in_symbol": context.config.token_targets.get(input_token, "UNKNOWN"),
                "token_out_symbol": context.config.token_targets.get(output_token, "UNKNOWN"),
            }
            order_data.update(order)

            return IntentData(
                order_id=order_hash,
                venue=IntentVenue.AORI,
                user=offerer,
                token_in=input_token,
                token_out=output_token,
                amount_in=input_amount,
                amount_out=output_amount,
                price_limit=output_amount,
                deadline=deadline if deadline > 0 else int(time.time()) + 300,
                chain=context.config.name,
                raw_order=order_data
            )

        except Exception as e:
            logger.error(f"Aori: Error normalizing order: {e}")
            return None
