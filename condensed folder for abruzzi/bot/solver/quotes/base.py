# Created: 2026-02-23
"""
Abstract base class for all ZIN quote providers.

Each provider implements get_quote() and returns a QuoteResult.
The QuoteAggregator queries all registered providers in parallel
and selects the best (highest expected_output) result.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from web3 import Web3


@dataclass
class QuoteResult:
    """
    Standardized quote result returned by every QuoteProvider.

    Fields:
        provider        Name of the aggregator/DEX that produced this quote.
        calldata        ABI-encoded calldata to pass to the executor contract.
        router_address  The contract address the executor should call.
        expected_output Amount of token_out the user will receive (raw units).
        gas_estimate    Estimated gas units for the swap.
        price_impact_bps Price impact in basis points (0 = unknown).
        extra           Provider-specific metadata (e.g. route path, pool fees).
    """
    provider: str
    calldata: bytes
    router_address: str
    expected_output: int
    gas_estimate: int
    price_impact_bps: int = 0
    extra: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        # Normalise router address to checksum form
        if self.router_address:
            try:
                self.router_address = Web3.to_checksum_address(self.router_address)
            except Exception:
                pass


class BaseQuoteProvider(ABC):
    """
    Abstract quote provider.

    Subclasses must implement get_quote() and return a QuoteResult or None
    if no route is available for the requested pair/amount.

    Design contract:
    - get_quote() MUST NOT raise — catch all exceptions internally and return None.
    - get_quote() MUST be async (called with await inside QuoteAggregator).
    - Providers are stateless with respect to individual quotes; they may
      maintain internal caches but must be safe to call concurrently.
    """

    # Human-readable name used in logs and QuoteResult.provider
    name: str = "Unknown"

    @abstractmethod
    async def get_quote(
        self,
        chain_id: int,
        token_in: str,
        token_out: str,
        amount_in: int,
        recipient: str,
        w3: Web3,
    ) -> Optional[QuoteResult]:
        """
        Fetch a swap quote.

        Args:
            chain_id    EVM chain ID (e.g. 8453 for Base).
            token_in    Checksummed address of the input token.
            token_out   Checksummed address of the output token.
            amount_in   Exact input amount in raw token units.
            recipient   Address that will receive the output tokens.
            w3          Connected Web3 instance for on-chain calls.

        Returns:
            QuoteResult if a route exists, None otherwise.
        """
        ...

    def supports_chain(self, chain_id: int) -> bool:
        """
        Return True if this provider supports the given chain.
        Override in subclasses to restrict to specific chains.
        Default: supports all chains.
        """
        return True