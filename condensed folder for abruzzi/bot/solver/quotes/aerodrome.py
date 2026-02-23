# Created: 2026-02-23
"""
Aerodrome (Base) quote provider.

Aerodrome is Base's primary DEX (Velodrome fork). It supports both
volatile and stable pools. We try both pool types and return the
better output.

Supported chains: Base (8453) only.
"""

import time
from typing import Optional
from loguru import logger
from web3 import Web3

from .base import BaseQuoteProvider, QuoteResult

# Aerodrome contracts on Base mainnet
AERODROME_ROUTER = "0xcF77a3Ba9A5CA399B7c97c478569a74DD55C726f"
AERODROME_FACTORY = "0x420DD381b31aEf6683db6B902084cB0FFECe40Da"

_ROUTER_ABI = [
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {
                "components": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "stable", "type": "bool"},
                    {"name": "factory", "type": "address"},
                ],
                "name": "routes",
                "type": "tuple[]",
            },
        ],
        "name": "getAmountsOut",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {
                "components": [
                    {"name": "from", "type": "address"},
                    {"name": "to", "type": "address"},
                    {"name": "stable", "type": "bool"},
                    {"name": "factory", "type": "address"},
                ],
                "name": "routes",
                "type": "tuple[]",
            },
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"},
        ],
        "name": "swapExactTokensForTokens",
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]

_SLIPPAGE_BPS = 50       # 0.5% slippage tolerance for calldata
_DEADLINE_SECONDS = 300  # 5-minute deadline


class AerodromeQuoteProvider(BaseQuoteProvider):
    """
    Quote provider for Aerodrome on Base.

    Strategy:
    1. Try volatile pool (stable=False) — best for ETH/LST pairs
    2. Try stable pool (stable=True)   — best for stablecoin pairs
    3. Return whichever gives the higher output
    """

    name = "Aerodrome"

    def supports_chain(self, chain_id: int) -> bool:
        return chain_id == 8453  # Base only

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
            router = w3.eth.contract(
                address=Web3.to_checksum_address(AERODROME_ROUTER),
                abi=_ROUTER_ABI,
            )

            best_output = 0
            best_stable = False

            for stable in (False, True):
                try:
                    routes = [(
                        Web3.to_checksum_address(token_in),
                        Web3.to_checksum_address(token_out),
                        stable,
                        Web3.to_checksum_address(AERODROME_FACTORY),
                    )]
                    amounts = router.functions.getAmountsOut(amount_in, routes).call()
                    if len(amounts) >= 2 and amounts[-1] > best_output:
                        best_output = amounts[-1]
                        best_stable = stable
                except Exception as e:
                    logger.debug(
                        f"Aerodrome: no {'stable' if stable else 'volatile'} route "
                        f"{token_in[:8]}→{token_out[:8]}: {e}"
                    )

            if best_output == 0:
                return None

            # Build calldata for the winning route
            min_out = best_output - (best_output * _SLIPPAGE_BPS // 10000)
            deadline = int(time.time()) + _DEADLINE_SECONDS
            best_routes = [(
                Web3.to_checksum_address(token_in),
                Web3.to_checksum_address(token_out),
                best_stable,
                Web3.to_checksum_address(AERODROME_FACTORY),
            )]

            calldata_hex = router.encodeABI(
                fn_name="swapExactTokensForTokens",
                args=[amount_in, min_out, best_routes, recipient, deadline],
            )
            calldata = bytes.fromhex(calldata_hex[2:])

            return QuoteResult(
                provider=self.name,
                calldata=calldata,
                router_address=AERODROME_ROUTER,
                expected_output=best_output,
                gas_estimate=200_000,
                price_impact_bps=0,
                extra={"stable": best_stable, "min_out": min_out},
            )

        except Exception as e:
            logger.warning(f"Aerodrome: unexpected error: {e}")
            return None