# Created: 2026-02-23
"""
Paraswap quote provider (Augustus Swapper).

Paraswap is particularly strong for LST/ETH pairs and often beats
1inch on stablecoin routes. No API key required — uses the public
Paraswap API v6.2.

Supported chains: Base (8453), Arbitrum (42161), Mainnet (1).
"""

from typing import Optional
from loguru import logger
from web3 import Web3

try:
    import aiohttp
    _AIOHTTP_AVAILABLE = True
except ImportError:
    _AIOHTTP_AVAILABLE = False

from .base import BaseQuoteProvider, QuoteResult

# Augustus Swapper V6 addresses per chain
_AUGUSTUS: dict = {
    8453:  "0x59C7C832e96D2568bea6db468C1aAdcbbDa08A52",  # Base
    42161: "0x0927FD43a7a87E3E8b81Df2c44B03C4756849655",  # Arbitrum
    1:     "0x6A000F20005980200259B80c5102003040001068",  # Mainnet
}

_API_BASE = "https://api.paraswap.io"
_TIMEOUT_SECONDS = 10
_SLIPPAGE_BPS = 50  # 0.5%

# Paraswap partner tag for tracking
_PARTNER = "kerne"


class ParaswapQuoteProvider(BaseQuoteProvider):
    """
    Quote provider using the Paraswap API v6.2.

    Two-step process:
    1. GET /prices  — fetch the best route and expected output
    2. POST /transactions — build the swap calldata

    No API key required. Paraswap is especially competitive for:
    - wstETH / ETH pairs (uses Lido's own pools)
    - Large USDC trades (aggregates Curve + Uniswap)
    """

    name = "Paraswap"

    def supports_chain(self, chain_id: int) -> bool:
        return _AIOHTTP_AVAILABLE and chain_id in _AUGUSTUS

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

        try:
            async with aiohttp.ClientSession() as session:
                # ── Step 1: Get price route ───────────────────────────────
                price_url = f"{_API_BASE}/prices"
                price_params = {
                    "srcToken": Web3.to_checksum_address(token_in),
                    "destToken": Web3.to_checksum_address(token_out),
                    "amount": str(amount_in),
                    "side": "SELL",
                    "network": str(chain_id),
                    "partner": _PARTNER,
                }

                async with session.get(
                    price_url,
                    params=price_params,
                    timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SECONDS),
                ) as resp:
                    if resp.status != 200:
                        logger.debug(f"Paraswap: prices HTTP {resp.status}")
                        return None

                    price_data = await resp.json()

                price_route = price_data.get("priceRoute")
                if not price_route:
                    logger.debug("Paraswap: no price route returned")
                    return None

                dest_amount = int(price_route.get("destAmount", 0))
                if dest_amount == 0:
                    return None

                # ── Step 2: Build transaction calldata ────────────────────
                min_out = dest_amount - (dest_amount * _SLIPPAGE_BPS // 10000)
                tx_url = f"{_API_BASE}/transactions/{chain_id}"
                tx_body = {
                    "srcToken": Web3.to_checksum_address(token_in),
                    "destToken": Web3.to_checksum_address(token_out),
                    "srcAmount": str(amount_in),
                    "destAmount": str(min_out),
                    "priceRoute": price_route,
                    "userAddress": Web3.to_checksum_address(recipient),
                    "receiver": Web3.to_checksum_address(recipient),
                    "partner": _PARTNER,
                }

                async with session.post(
                    tx_url,
                    json=tx_body,
                    timeout=aiohttp.ClientTimeout(total=_TIMEOUT_SECONDS),
                ) as tx_resp:
                    if tx_resp.status != 200:
                        err = await tx_resp.text()
                        logger.debug(f"Paraswap: tx build HTTP {tx_resp.status}: {err[:100]}")
                        return None

                    tx_data = await tx_resp.json()

                calldata_hex = tx_data.get("data", "")
                gas_estimate = int(tx_data.get("gas", 350_000))
                augustus_addr = _AUGUSTUS[chain_id]

                if not calldata_hex:
                    return None

                calldata = bytes.fromhex(
                    calldata_hex[2:] if calldata_hex.startswith("0x") else calldata_hex
                )

                return QuoteResult(
                    provider=self.name,
                    calldata=calldata,
                    router_address=augustus_addr,
                    expected_output=dest_amount,
                    gas_estimate=gas_estimate,
                    price_impact_bps=int(
                        float(price_route.get("percentChange", 0)) * 100
                    ),
                    extra={
                        "min_out": min_out,
                        "best_route": price_route.get("bestRoute", []),
                    },
                )

        except Exception as e:
            logger.warning(f"Paraswap: unexpected error: {e}")
            return None