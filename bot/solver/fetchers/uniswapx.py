# Created: 2026-01-26
import asyncio
import time
import aiohttp
from typing import List, Optional, Dict, Any
from loguru import logger
from .base import BaseIntentFetcher, ChainContext, IntentData, IntentVenue

class UniswapXFetcher(BaseIntentFetcher):
    """Fetcher for UniswapX intents."""
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
        config = context.config.uniswapx_config

        params = {
            "orderStatus": "open",
            "chainId": config["chain_id"],
            "orderType": config["order_type"],
            "limit": 100,
        }

        headers = {
            "Accept": "application/json",
            "Origin": "https://app.uniswap.org"
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(
                    config["api_url"],
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if not self._health_logged.get(context.config.name):
                        self._health_logged[context.config.name] = True
                        if resp.status == 200:
                            logger.info(
                                f"UniswapX: API reachable (chainId={config['chain_id']}, "
                                f"orderType={config['order_type']})"
                            )
                        else:
                            logger.warning(
                                f"UniswapX: API health check failed (status={resp.status})"
                            )

                    if resp.status == 200:
                        data = await resp.json()
                        orders = data.get('orders', [])

                        if orders:
                            logger.debug(f"UniswapX: Fetched {len(orders)} open orders")

                        for order in orders:
                            intent = self._normalize_order(order, context)
                            if intent:
                                intents.append(intent)

                    elif resp.status == 429:
                        logger.warning("UniswapX: Rate limited (429). Backing off...")
                    else:
                        logger.debug(f"UniswapX: API returned status {resp.status}")

            except asyncio.TimeoutError:
                logger.warning("UniswapX: Request timeout")
            except aiohttp.ClientError as e:
                logger.error(f"UniswapX: Network error: {e}")
            except Exception as e:
                logger.error(f"UniswapX: Unexpected error: {e}")

        return intents

    def _normalize_order(self, order: Dict, context: ChainContext) -> Optional[IntentData]:
        try:
            order_hash = order.get('orderHash', '')
            input_data = order.get('input', {})
            sell_token = input_data.get('token', '').lower()
            sell_amount = int(input_data.get('amount', 0))

            outputs = order.get('outputs', [])
            if not outputs:
                return None

            primary_output = outputs[0]
            buy_token = primary_output.get('token', '').lower()
            buy_amount = int(primary_output.get('amount', 0))

            swapper = order.get('swapper', '')
            encoded_order = order.get('encodedOrder', '')

            if not all([order_hash, sell_token, buy_token, sell_amount, buy_amount, swapper]):
                return None

            if not self.solver._is_target_pair(sell_token, buy_token, context):
                return None

            # Check if we have liquidity for the output token
            if not self.solver._has_output_liquidity(buy_token, context):
                logger.debug(f"UniswapX: Skipping intent - no liquidity for output token {buy_token[:10]}...")
                return None

            deadline = int(time.time()) + 120

            order_data = {
                "token_in_symbol": context.config.token_targets.get(sell_token, "UNKNOWN"),
                "token_out_symbol": context.config.token_targets.get(buy_token, "UNKNOWN"),
            }
            order_data.update(order)

            return IntentData(
                order_id=order_hash,
                venue=IntentVenue.UNISWAPX,
                user=swapper,
                token_in=sell_token,
                token_out=buy_token,
                amount_in=sell_amount,
                amount_out=buy_amount,
                price_limit=buy_amount,
                deadline=deadline,
                chain=context.config.name,
                encoded_order=encoded_order,
                raw_order=order_data
            )

        except Exception as e:
            logger.error(f"UniswapX: Error normalizing order: {e}")
            return None
