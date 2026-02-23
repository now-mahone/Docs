# Created: 2026-02-23
"""
QuoteAggregator — queries all registered QuoteProviders in parallel
and returns the best (highest expected_output) result.

Key features:
  - Parallel async execution via asyncio.gather
  - Per-pair quote caching (TTL configurable, default 8s)
  - Provider-level error isolation (one failure never blocks others)
  - Detailed logging of all quotes for debugging
  - Automatic provider filtering by chain support
"""

import asyncio
import time
from typing import Dict, List, Optional, Tuple
from loguru import logger
from web3 import Web3

from .base import BaseQuoteProvider, QuoteResult
from .aerodrome import AerodromeQuoteProvider
from .uniswap_v3 import UniswapV3QuoteProvider
from .one_inch import OneInchQuoteProvider
from .paraswap import ParaswapQuoteProvider

# Default quote cache TTL in seconds.
# 8s is short enough to stay fresh during active intent processing
# but long enough to avoid hammering APIs on repeated identical pairs.
_DEFAULT_CACHE_TTL = 8.0


class QuoteAggregator:
    """
    Queries all registered QuoteProviders in parallel and returns
    the best quote for a given token pair and amount.

    Usage:
        aggregator = QuoteAggregator()
        quote = await aggregator.get_best_quote(
            chain_id=8453,
            token_in="0x4200...",
            token_out="0x8335...",
            amount_in=1_000_000,   # 1 USDC (6 decimals)
            recipient="0xYourAddress",
            w3=w3_instance,
        )
        if quote:
            print(f"Best: {quote.provider} → {quote.expected_output}")
    """

    def __init__(
        self,
        providers: Optional[List[BaseQuoteProvider]] = None,
        cache_ttl: float = _DEFAULT_CACHE_TTL,
    ):
        """
        Args:
            providers   List of QuoteProvider instances. If None, uses the
                        default set: Aerodrome, UniswapV3, 1inch, Paraswap.
            cache_ttl   Seconds to cache quotes for identical (chain, in, out, amount).
        """
        if providers is None:
            self.providers: List[BaseQuoteProvider] = [
                AerodromeQuoteProvider(),
                UniswapV3QuoteProvider(),
                OneInchQuoteProvider(),
                ParaswapQuoteProvider(),
            ]
        else:
            self.providers = providers

        self.cache_ttl = cache_ttl
        # Cache: key → (QuoteResult, timestamp)
        self._cache: Dict[str, Tuple[QuoteResult, float]] = {}

        logger.info(
            f"QuoteAggregator initialized with {len(self.providers)} providers: "
            + ", ".join(p.name for p in self.providers)
        )

    # ── Cache helpers ─────────────────────────────────────────────────────────

    @staticmethod
    def _cache_key(chain_id: int, token_in: str, token_out: str, amount_in: int) -> str:
        return f"{chain_id}:{token_in.lower()}:{token_out.lower()}:{amount_in}"

    def _get_cached(self, key: str) -> Optional[QuoteResult]:
        entry = self._cache.get(key)
        if entry and (time.time() - entry[1]) < self.cache_ttl:
            return entry[0]
        return None

    def _set_cached(self, key: str, result: QuoteResult):
        self._cache[key] = (result, time.time())

    def invalidate(self, chain_id: int, token_in: str, token_out: str, amount_in: int):
        """Manually invalidate a cached entry (e.g. after a successful fill)."""
        key = self._cache_key(chain_id, token_in, token_out, amount_in)
        self._cache.pop(key, None)

    def clear_cache(self):
        """Clear all cached quotes."""
        self._cache.clear()

    # ── Core quoting logic ────────────────────────────────────────────────────

    async def _fetch_one(
        self,
        provider: BaseQuoteProvider,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        recipient: str,
        w3: Web3,
    ) -> Optional[QuoteResult]:
        """Fetch a single provider's quote, swallowing all exceptions."""
        try:
            return await provider.get_quote(
                chain_id=chain_id,
                token_in=token_in,
                token_out=token_out,
                amount_in=amount_in,
                recipient=recipient,
                w3=w3,
            )
        except Exception as e:
            logger.warning(f"QuoteAggregator: {provider.name} raised unexpectedly: {e}")
            return None

    async def get_best_quote(
        self,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        recipient: str,
        w3: Web3,
        use_cache: bool = True,
    ) -> Optional[QuoteResult]:
        """
        Query all compatible providers in parallel and return the best quote.

        Args:
            chain_id    EVM chain ID.
            token_in    Input token address (any case).
            token_out   Output token address (any case).
            amount_in   Exact input amount in raw token units.
            recipient   Address that will receive the output tokens.
            w3          Connected Web3 instance.
            use_cache   If True (default), return cached result when fresh.

        Returns:
            The QuoteResult with the highest expected_output, or None if
            no provider returned a valid quote.
        """
        # Normalise addresses
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)

        cache_key = self._cache_key(chain_id, token_in, token_out, amount_in)

        if use_cache:
            cached = self._get_cached(cache_key)
            if cached:
                logger.debug(
                    f"QuoteAggregator: cache hit for {token_in[:8]}→{token_out[:8]} "
                    f"({cached.provider}, out={cached.expected_output})"
                )
                return cached

        # Filter providers that support this chain
        active_providers = [p for p in self.providers if p.supports_chain(chain_id)]
        if not active_providers:
            logger.warning(f"QuoteAggregator: no providers support chain {chain_id}")
            return None

        # Fire all providers concurrently
        tasks = [
            self._fetch_one(p, chain_id, token_in, token_out, amount_in, recipient, w3)
            for p in active_providers
        ]
        results: List[Optional[QuoteResult]] = await asyncio.gather(*tasks)

        # Filter valid results and pick the best
        valid: List[QuoteResult] = [r for r in results if r is not None and r.expected_output > 0]

        if not valid:
            logger.debug(
                f"QuoteAggregator: no valid quotes for "
                f"{token_in[:8]}→{token_out[:8]} on chain {chain_id}"
            )
            return None

        # Log all quotes for transparency
        if len(valid) > 1:
            sorted_quotes = sorted(valid, key=lambda q: q.expected_output, reverse=True)
            logger.debug(
                f"QuoteAggregator: {len(valid)} quotes for "
                f"{token_in[:8]}→{token_out[:8]}:"
            )
            for q in sorted_quotes:
                logger.debug(
                    f"  {q.provider:<12} out={q.expected_output:>20}  "
                    f"gas={q.gas_estimate:>7}  impact={q.price_impact_bps}bps"
                )

        best = max(valid, key=lambda q: q.expected_output)
        logger.info(
            f"QuoteAggregator: best={best.provider} "
            f"out={best.expected_output} "
            f"gas={best.gas_estimate} "
            f"for {token_in[:8]}→{token_out[:8]}"
        )

        if use_cache:
            self._set_cached(cache_key, best)

        return best

    async def get_all_quotes(
        self,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        recipient: str,
        w3: Web3,
    ) -> List[QuoteResult]:
        """
        Return all valid quotes (not just the best).
        Useful for analytics and debugging.
        """
        token_in = Web3.to_checksum_address(token_in)
        token_out = Web3.to_checksum_address(token_out)

        active_providers = [p for p in self.providers if p.supports_chain(chain_id)]
        tasks = [
            self._fetch_one(p, chain_id, token_in, token_out, amount_in, recipient, w3)
            for p in active_providers
        ]
        results = await asyncio.gather(*tasks)
        return [r for r in results if r is not None and r.expected_output > 0]

    # ── Stats ─────────────────────────────────────────────────────────────────

    @property
    def cache_size(self) -> int:
        return len(self._cache)

    @property
    def provider_names(self) -> List[str]:
        return [p.name for p in self.providers]