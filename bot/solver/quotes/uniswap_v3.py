# Created: 2026-02-23
"""
Uniswap V3 quote provider (on-chain Quoter V2).

Uses the Uniswap V3 QuoterV2 contract for exact-input quotes.
Tries the three standard fee tiers (500, 3000, 10000) and returns
the best output. Builds calldata for the SwapRouter02.

Supported chains: Base (8453), Arbitrum (42161), Mainnet (1).
"""

import time
from typing import Optional, List, Tuple
from loguru import logger
from web3 import Web3

from .base import BaseQuoteProvider, QuoteResult

# ── Contract addresses per chain ─────────────────────────────────────────────

_QUOTER_V2: dict = {
    8453:  "0x3d4e44Eb1374240CE5F1B136041212501e4a8139",  # Base
    42161: "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",  # Arbitrum
    1:     "0x61fFE014bA17989E743c5F6cB21bF9697530B21e",  # Mainnet
}

_SWAP_ROUTER_02: dict = {
    8453:  "0x2626664c2603336E57B271c5C0b26F421741e481",  # Base
    42161: "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # Arbitrum
    1:     "0x68b3465833fb72A70ecDF485E0e4C7bD8665Fc45",  # Mainnet
}

# Standard Uniswap V3 fee tiers (bps * 100)
_FEE_TIERS: List[int] = [100, 500, 3000, 10000]

_SLIPPAGE_BPS = 50       # 0.5%
_DEADLINE_SECONDS = 300  # 5 minutes

# ── ABIs ─────────────────────────────────────────────────────────────────────

_QUOTER_V2_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]

_SWAP_ROUTER_ABI = [
    {
        "inputs": [
            {
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "fee", "type": "uint24"},
                    {"name": "recipient", "type": "address"},
                    {"name": "amountIn", "type": "uint256"},
                    {"name": "amountOutMinimum", "type": "uint256"},
                    {"name": "sqrtPriceLimitX96", "type": "uint160"},
                ],
                "name": "params",
                "type": "tuple",
            }
        ],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    }
]


class UniswapV3QuoteProvider(BaseQuoteProvider):
    """
    Quote provider using Uniswap V3 QuoterV2 (on-chain, no API key needed).

    Tries all standard fee tiers and returns the best single-hop quote.
    Falls back gracefully if a pool doesn't exist for a given fee tier.
    """

    name = "UniswapV3"

    def supports_chain(self, chain_id: int) -> bool:
        return chain_id in _QUOTER_V2

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

        quoter_addr = _QUOTER_V2.get(chain_id)
        router_addr = _SWAP_ROUTER_02.get(chain_id)
        if not quoter_addr or not router_addr:
            return None

        try:
            quoter = w3.eth.contract(
                address=Web3.to_checksum_address(quoter_addr),
                abi=_QUOTER_V2_ABI,
            )
            router = w3.eth.contract(
                address=Web3.to_checksum_address(router_addr),
                abi=_SWAP_ROUTER_ABI,
            )

            best_output: int = 0
            best_fee: int = 0
            best_gas: int = 300_000

            for fee in _FEE_TIERS:
                try:
                    result = quoter.functions.quoteExactInputSingle({
                        "tokenIn": Web3.to_checksum_address(token_in),
                        "tokenOut": Web3.to_checksum_address(token_out),
                        "amountIn": amount_in,
                        "fee": fee,
                        "sqrtPriceLimitX96": 0,
                    }).call()

                    amount_out = result[0]
                    gas_est = result[3]

                    if amount_out > best_output:
                        best_output = amount_out
                        best_fee = fee
                        best_gas = int(gas_est) if gas_est else 300_000

                except Exception as e:
                    logger.debug(
                        f"UniswapV3: no pool for fee={fee} "
                        f"{token_in[:8]}→{token_out[:8]}: {e}"
                    )

            if best_output == 0:
                return None

            # Build calldata for SwapRouter02.exactInputSingle
            min_out = best_output - (best_output * _SLIPPAGE_BPS // 10000)
            calldata_hex = router.encodeABI(
                fn_name="exactInputSingle",
                args=[{
                    "tokenIn": Web3.to_checksum_address(token_in),
                    "tokenOut": Web3.to_checksum_address(token_out),
                    "fee": best_fee,
                    "recipient": Web3.to_checksum_address(recipient),
                    "amountIn": amount_in,
                    "amountOutMinimum": min_out,
                    "sqrtPriceLimitX96": 0,
                }],
            )
            calldata = bytes.fromhex(calldata_hex[2:])

            return QuoteResult(
                provider=self.name,
                calldata=calldata,
                router_address=router_addr,
                expected_output=best_output,
                gas_estimate=best_gas + 50_000,  # buffer for executor overhead
                price_impact_bps=0,
                extra={"fee_tier": best_fee, "min_out": min_out},
            )

        except Exception as e:
            logger.warning(f"UniswapV3: unexpected error: {e}")
            return None