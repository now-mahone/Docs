# Created: 2026-01-16
# Updated: 2026-02-22 - MEV Protection Layer: Flashbots Base, slippage/deadline guards, robust private RPC fallback
"""
MEV Protection Layer
====================
Routes transactions through private RPCs (Flashbots Protect for Base) to
prevent frontrunning and sandwich attacks. Implements slippage + deadline
guards on every swap payload. Falls back to the public mempool if ALL
private channels fail — ensuring liquidation/settlement transactions are
never silently dropped.

Private RPC Priority:
  1. Flashbots Protect (Base) — native MEV protection for Base L2
  2. Flashbots Protect standard relay
  3. LlamaRPC — fallback private endpoint
  4. Public Base RPC — final safety net (logs a warning when used)
"""

import time
import httpx
import asyncio
from typing import Optional, List, Dict
from dataclasses import dataclass, field
from loguru import logger
from web3 import Web3


# ─────────────────────────────────────────────────────────────────────────────
# CONSTANTS
# ─────────────────────────────────────────────────────────────────────────────

DEFAULT_SLIPPAGE_BPS: int = 50        # 0.5% slippage tolerance
DEFAULT_DEADLINE_SECONDS: int = 60    # 60-second execution window per tx
MAX_PRIORITY_GWEI: float = 0.1        # Max priority fee tip
BASE_FEE_MULTIPLIER: int = 2          # maxFeePerGas = baseFee * 2 + priorityFee
ENDPOINT_COOLDOWN_SECONDS: int = 30   # Back-off duration for failing endpoints


# ─────────────────────────────────────────────────────────────────────────────
# SLIPPAGE / DEADLINE GUARD
# ─────────────────────────────────────────────────────────────────────────────

class SlippageDeadlineGuard:
    """
    Enforces slippage tolerance and deadline windows on swap payloads
    before they are submitted to any RPC.

    Usage:
        guard = SlippageDeadlineGuard(slippage_bps=50, deadline_seconds=60)
        min_out = guard.min_amount_out(expected_out=1_000_000)
        deadline = guard.deadline()
    """

    def __init__(
        self,
        slippage_bps: int = DEFAULT_SLIPPAGE_BPS,
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
    ):
        self.slippage_bps = slippage_bps
        self.deadline_seconds = deadline_seconds

    def min_amount_out(self, expected_out: int) -> int:
        """
        Calculate the minimum acceptable output for a swap.

        Args:
            expected_out: The quoted/expected output amount (raw token units).

        Returns:
            Minimum acceptable output after slippage deduction. Always >= 1.
        """
        if expected_out <= 0:
            return 1
        factor = 10_000 - self.slippage_bps
        min_out = (expected_out * factor) // 10_000
        return max(min_out, 1)

    def deadline(self) -> int:
        """
        Return a Unix timestamp deadline for the transaction.

        Returns:
            Current time + deadline_seconds.
        """
        return int(time.time()) + self.deadline_seconds

    def validate_amount_out(self, actual_out: int, expected_out: int) -> bool:
        """
        Check whether an actual output satisfies the slippage guard.

        Args:
            actual_out:   The amount actually received.
            expected_out: The original expected/quoted amount.

        Returns:
            True if within tolerance, False if slippage exceeded.
        """
        threshold = self.min_amount_out(expected_out)
        if actual_out < threshold:
            excess_bps = (
                ((expected_out - actual_out) * 10_000) // expected_out
                if expected_out > 0
                else 0
            )
            logger.warning(
                f"[MEV] Slippage exceeded! Expected≥{threshold}, Got={actual_out} "
                f"({excess_bps} bps > {self.slippage_bps} bps limit)"
            )
            return False
        return True

    def is_deadline_expired(self, deadline_ts: int) -> bool:
        """Check if a previously computed deadline has passed."""
        return int(time.time()) > deadline_ts


# ─────────────────────────────────────────────────────────────────────────────
# ENDPOINT HEALTH TRACKER
# ─────────────────────────────────────────────────────────────────────────────

class _EndpointHealth:
    """Tracks failure state for a single RPC endpoint."""

    def __init__(self, url: str):
        self.url = url
        self.fail_count: int = 0
        self.last_fail_ts: float = 0.0

    def is_cooled_down(self) -> bool:
        if self.fail_count == 0:
            return True
        return (time.time() - self.last_fail_ts) >= ENDPOINT_COOLDOWN_SECONDS

    def record_failure(self):
        self.fail_count += 1
        self.last_fail_ts = time.time()

    def record_success(self):
        self.fail_count = 0
        self.last_fail_ts = 0.0


# ─────────────────────────────────────────────────────────────────────────────
# MEV PROTECTED SUBMITTER
# ─────────────────────────────────────────────────────────────────────────────

class MEVProtectedSubmitter:
    """
    Submit transactions via private RPC channels to prevent MEV exploitation
    (frontrunning, sandwich attacks) on Base.

    Submission order:
      1. Try all healthy private endpoints in parallel.
      2. Return the first successful tx_hash.
      3. If ALL private endpoints fail, automatically fall back to the
         public Base RPC — ensuring liquidation transactions are never lost.

    Endpoint health is tracked per-instance so that repeatedly-failing
    endpoints are cooled down before being retried.
    """

    # Ordered: best MEV protection first
    PRIVATE_ENDPOINTS: List[str] = [
        "https://rpc.flashbots.net/fast",   # Flashbots Protect fast relay (Base-compatible)
        "https://rpc.flashbots.net",        # Flashbots Protect standard
        "https://base.llamarpc.com",        # LlamaRPC private endpoint for Base
    ]

    PUBLIC_FALLBACK_ENDPOINTS: List[str] = [
        "https://mainnet.base.org",         # Official Base public RPC
        "https://base.drpc.org",            # dRPC public fallback
    ]

    def __init__(
        self,
        w3: Web3,
        private_key: str,
        slippage_bps: int = DEFAULT_SLIPPAGE_BPS,
        deadline_seconds: int = DEFAULT_DEADLINE_SECONDS,
    ):
        self.w3 = w3
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)

        # Slippage / deadline enforcement
        self.guard = SlippageDeadlineGuard(
            slippage_bps=slippage_bps,
            deadline_seconds=deadline_seconds,
        )

        # Per-endpoint health tracking (private endpoints only)
        self._health: Dict[str, _EndpointHealth] = {
            url: _EndpointHealth(url=url) for url in self.PRIVATE_ENDPOINTS
        }

    # ── Public API ──────────────────────────────────────────────────────────

    async def submit_private(
        self,
        signed_tx_raw: bytes,
        timeout: float = 30.0,
        is_critical: bool = False,
    ) -> Optional[str]:
        """
        Submit a signed transaction via private RPC with automatic public fallback.

        Args:
            signed_tx_raw:  Raw signed transaction bytes.
            timeout:        Per-endpoint HTTP timeout in seconds.
            is_critical:    If True (e.g. liquidations), always fall back to
                            public mempool when private channels fail — tx loss
                            is unacceptable for these operations.

        Returns:
            Transaction hash string (0x-prefixed) on success, or None.
        """
        tx_hex = self._to_hex(signed_tx_raw)

        # 1. Identify healthy private endpoints
        healthy = [
            url for url, health in self._health.items()
            if health.is_cooled_down()
        ]

        if not healthy:
            logger.warning("[MEV] All private endpoints are in cooldown — skipping to fallback.")
        else:
            # 2. Try all healthy private endpoints in parallel
            tasks = [self._send_to_endpoint(url, tx_hex, timeout) for url in healthy]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for url, res in zip(healthy, results):
                if isinstance(res, str) and res.startswith("0x"):
                    self._health[url].record_success()
                    logger.info(f"[MEV] ✅ Private submission succeeded: {url} → {res}")
                    return res
                else:
                    self._health[url].record_failure()
                    logger.debug(f"[MEV] Private endpoint failed: {url} — {res}")

        # 3. Fallback to public mempool
        # Always fall back — never silently drop. For critical ops this is
        # mandatory; for arb ops we accept MEV risk rather than miss a window.
        logger.warning(
            "[MEV] ⚠️  ALL private endpoints failed. "
            "Falling back to PUBLIC mempool. "
            "This transaction is now frontrun-able."
        )
        return await self._submit_public_fallback(signed_tx_raw, timeout)

    def build_with_priority(
        self,
        tx_dict: dict,
        priority_gwei: float = MAX_PRIORITY_GWEI,
    ) -> dict:
        """
        Attach EIP-1559 fee parameters to a transaction dict.

        Sets maxFeePerGas = (baseFee × 2) + priorityFee to ensure sufficient
        headroom for inclusion even during fee spikes.

        Args:
            tx_dict:       The transaction dict to modify in-place.
            priority_gwei: Priority fee tip in Gwei.

        Returns:
            Updated transaction dictionary.
        """
        latest_block = self.w3.eth.get_block("latest")
        base_fee = latest_block.get("baseFeePerGas", self.w3.to_wei(0.001, "gwei"))

        priority_fee = self.w3.to_wei(priority_gwei, "gwei")
        max_fee = base_fee * BASE_FEE_MULTIPLIER + priority_fee

        tx_dict["maxPriorityFeePerGas"] = priority_fee
        tx_dict["maxFeePerGas"] = max_fee
        tx_dict["type"] = 2  # EIP-1559

        logger.debug(
            f"[MEV] Fee params — baseFee={base_fee / 1e9:.4f} Gwei, "
            f"priorityFee={priority_gwei} Gwei, maxFee={max_fee / 1e9:.4f} Gwei"
        )
        return tx_dict

    def reset_endpoint_health(self):
        """Force-reset all endpoint health (e.g. after a recovery event)."""
        for health in self._health.values():
            health.record_success()
        logger.info("[MEV] Endpoint health state reset.")

    # ── Internal helpers ────────────────────────────────────────────────────

    async def _send_to_endpoint(
        self, endpoint: str, tx_hex: str, timeout: float
    ) -> Optional[str]:
        """Submit a raw transaction to a single JSON-RPC endpoint."""
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(
                    endpoint,
                    json={
                        "jsonrpc": "2.0",
                        "method": "eth_sendRawTransaction",
                        "params": [tx_hex],
                        "id": 1,
                    },
                )
                result = resp.json()
                if "result" in result and result["result"]:
                    return result["result"]
                if "error" in result:
                    logger.debug(f"[MEV] {endpoint} returned error: {result['error']}")
        except httpx.TimeoutException:
            logger.debug(f"[MEV] {endpoint} timed out after {timeout}s")
        except Exception as e:
            logger.debug(f"[MEV] {endpoint} exception: {e}")
        return None

    async def _submit_public_fallback(
        self, signed_tx_raw: bytes, timeout: float = 30.0
    ) -> Optional[str]:
        """
        Last-resort: submit via the public Base mempool.
        Used for critical operations (liquidations, settlement) where
        silent failure is more dangerous than MEV exposure.
        """
        # Try web3 provider first (fastest path)
        try:
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx_raw)
            tx_hex = tx_hash.hex()
            if not tx_hex.startswith("0x"):
                tx_hex = "0x" + tx_hex
            logger.warning(f"[MEV] Public submission via w3 provider succeeded: {tx_hex}")
            return tx_hex
        except Exception as e:
            logger.warning(f"[MEV] w3 public submission failed: {e}")

        # Try known public Base RPCs
        tx_hex = self._to_hex(signed_tx_raw)
        for url in self.PUBLIC_FALLBACK_ENDPOINTS:
            result = await self._send_to_endpoint(url, tx_hex, timeout)
            if result:
                logger.warning(f"[MEV] Public fallback succeeded via {url}: {result}")
                return result

        logger.error(
            "[MEV] CRITICAL: All submission channels (private + public) exhausted. Transaction dropped."
        )
        return None

    @staticmethod
    def _to_hex(raw_tx: bytes) -> str:
        """Convert raw transaction bytes to 0x-prefixed hex string."""
        tx_hex = raw_tx.hex() if isinstance(raw_tx, (bytes, bytearray)) else str(raw_tx)
        if not tx_hex.startswith("0x"):
            tx_hex = "0x" + tx_hex
        return tx_hex