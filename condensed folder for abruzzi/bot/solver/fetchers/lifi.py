# Created: 2026-01-26
import time
import aiohttp
from typing import List, Optional, Dict
from loguru import logger
from .base import BaseIntentFetcher, ChainContext, IntentData, IntentVenue

class LifiIntentFetcher(BaseIntentFetcher):
    """Fetcher for LI.FI intents."""
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
        # LI.FI Intent API
        url = "https://li.quest/v1/intents"
        
        params = {
            "chainId": context.config.chain_id,
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
                            logger.info(f"LI.FI: API reachable (chainId={context.config.chain_id})")
                        else:
                            logger.warning(f"LI.FI: API health check failed (status={resp.status})")

                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('intents', [])

                        if orders:
                            logger.debug(f"LI.FI: Fetched {len(orders)} intents")

                        for order in orders:
                            intent = self._normalize_order(order, context)
                            if intent:
                                intents.append(intent)

            except Exception as e:
                logger.error(f"LI.FI: Error fetching intents: {e}")

        return intents

    def _normalize_order(self, order: Dict, context: ChainContext) -> Optional[IntentData]:
        try:
            order_id = order.get('id', '')
            input_token = order.get('inputToken', '').lower()
            output_token = order.get('outputToken', '').lower()
            input_amount = int(order.get('inputAmount', 0))
            output_amount = int(order.get('outputAmount', 0))
            user = order.get('user', '')
            
            if not all([order_id, input_token, output_token, input_amount, output_amount, user]):
                return None

            if not self.solver._is_target_pair(input_token, output_token, context):
                return None

            deadline = int(order.get('deadline', 0))

            order_data = {
                "token_in_symbol": context.config.token_targets.get(input_token, "UNKNOWN"),
                "token_out_symbol": context.config.token_targets.get(output_token, "UNKNOWN"),
            }
            order_data.update(order)

            return IntentData(
                order_id=order_id,
                venue=IntentVenue.LIFI,
                user=user,
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
            logger.error(f"LI.FI: Error normalizing order: {e}")
            return None
