# Created: 2026-02-23
"""
1inch Swap API v6 quote provider.

Requires ONE_INCH_API_KEY environment variable.
Supports all chains where 1inch has deployed (Base, Arbitrum, Mainnet, etc.).

Falls back gracefully if the API key is missing or the request fails.
"""

import os
from typing import Optional
from loguru import logger
from web3 import Web3

try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _AIOHTTP_AVAILABLE = False

from .base import BaseQuoteProvider, QuoteResult

ONE_INCH_API_KEY = os.getenv("ONE_INCH_API_KEY", "")

# 1inch Aggregation Router V6 addresses per chain
_ROUTER: dict = {
    8453:  "0x111111125421cA6dc452d289314280a0f8842A65",  # Base
    42161: "0x111111125421cA6dc452d289314280a0f8842A65",  # Arbitrum
    1:     "0x111111125421cA6dc452d289314280a0f8842A65",  # Mainnet
    10:    "0x111111125421cA6dc452d289314280a0f8842A65",  # Optimism
}

_API_BASE = "https://api.1inch.dev/swap/v6.0"
_TIMEOUT_SECONDS = 10
_SLIPPAGE_PCT = "0.5"  # 0.5% slippage passed to 1inch


class OneInchQuoteProvider(BaseQuoteProvider):
    """
    Quote provider using the 1inch Swap API v6.

    1inch aggregates hundreds of DEXs and typically finds the best
    route for large trades. Requires an API key from portal.1inch.dev.

    Rate limits: 1 RPS on free tier — the QuoteAggregator's parallel
    execution means this may occasionally 429; errors are handled
    gracefully and the provider returns None on failure.
    """

    name = "1inch"

    def supports_chain(self, chain_id: int) -> bool:
        return bool(ONE_INCH_API_KEY) and chain_id in _ROUTER

    async def get_quote(
        self,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        recipient: str,
        w3: Web3,
    ) -> Optional[QuoteResult]:
        if not self.supports_chain(chain_id):
            return None

        if not _AIOHTTP_AVAILABLE:
            logger.debug("1inch: aiohttp not installed")
            return None

        url = f"{_API_BASE}/{chain_id}/swap"
        params = {
            "src": Web3.to_checksum_address(token_in),
            "dst": Web3.to_checksum_address(token_out),
            "amount": str(amount_in),
            "from": Web3.to_checksum_address(recipient),
            "slippage": _SLIPPAGE_PCT,
            "disableEstimate": "true",
            "allowPartialFill": "false",
        }
        headers = {
            "Authorization": f"Bearer {ONE_INCH_API_KEY}",
            "Accept": "application/json",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    url,
                    params=params,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        tx_data = data.get("tx", {})
                        calldata_hex = tx_data.get("data", "")
                        output_amount = int(data.get("dstAmount", 0))
                        gas_estimate = int(tx_data.get("gas", 350_000))

                        if not calldata_hex or output_amount == 0:
                            logger.debug("1inch: empty response")
                            return None

                        calldata = bytes.fromhex(
                            calldata_hex[2:] if calldata_hex.startswith("0x") else calldata_hex
                        )
                        router_addr = _ROUTER[chain_id]

                        return QuoteResult(
                            provider=self.name,
                            calldata=calldata,
                            router_address=router_addr,
                            expected_output=output_amount,
                            gas_estimate=gas_estimate,
                            price_impact_bps=0,
                            extra={"protocols": data.get("protocols", [])},
                        )

                    elif resp.status == 429:
                        logger.warning("1inch: rate limited (429)")
                    elif resp.status == 400:
                        err = await resp.json()
                        logger.debug(f"1inch: bad request — {err.get('description', 'unknown')}")
                    else:
                        logger.debug(f"1inch: HTTP {resp.status}")

        except Exception as e:
            logger.warning(f"1inch: request error: {e}")

        return None