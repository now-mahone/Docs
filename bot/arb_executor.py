# Created: 2026-01-16
# Updated: 2026-02-22 - MEV Protection Layer: per-hop slippage protection via SlippageDeadlineGuard
import asyncio
import time
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger
from web3 import Web3
from web3.contract import Contract

from bot.mev_protection import SlippageDeadlineGuard, DEFAULT_SLIPPAGE_BPS


@dataclass
class ExecutionResult:
    success: bool
    tx_hash: Optional[str] = None
    profit_usd: float = 0.0
    gas_used: int = 0
    error: Optional[str] = None
    revert_reason: Optional[str] = None


class LenderPriority(Enum):
    PSM = 1      # 0% fee, kUSD only
    VAULT = 2    # 0% fee, ETH/LSTs
    AAVE = 3     # 0.09% fee, fallback


class RobustArbExecutor:
    """
    Production-grade arb execution with:
    - Multi-lender fallback
    - Simulation before execution
    - Per-hop slippage protection (MEV sandwich defence)
    - Deadline enforcement on every transaction
    - Revert handling & retry
    - Nonce management
    """

    MAX_RETRIES = 2
    SIMULATION_GAS_BUFFER = 1.3

    def __init__(
        self,
        w3: Web3,
        arb_bot_contract: Contract,
        private_key: str,
        mev_submitter=None,
        slippage_bps: int = DEFAULT_SLIPPAGE_BPS,
    ):
        self.w3 = w3
        self.arb_bot = arb_bot_contract
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
        self.mev_submitter = mev_submitter
        self._nonce_lock = asyncio.Lock()
        self._current_nonce = None

        # Slippage / deadline guard — shared with mev_submitter if available
        self.guard = (
            mev_submitter.guard
            if mev_submitter and hasattr(mev_submitter, "guard")
            else SlippageDeadlineGuard(slippage_bps=slippage_bps)
        )

    async def execute_with_fallback(
        self,
        opp: Any,  # ArbPath
        lenders: List[Tuple[str, LenderPriority]],
    ) -> ExecutionResult:
        """Try execution with lender fallback on failure."""
        sorted_lenders = sorted(lenders, key=lambda x: x[1].value)

        for lender_addr, priority in sorted_lenders:
            for attempt in range(self.MAX_RETRIES):
                result = await self._attempt_execution(opp, lender_addr)

                if result.success:
                    return result

                if result.revert_reason:
                    if "UnauthorizedLender" in result.revert_reason:
                        logger.warning(f"Lender {lender_addr} not authorized, trying next lender")
                        break
                    if "ArbNotProfitable" in result.revert_reason:
                        logger.info("Arb no longer profitable, aborting cycle")
                        return result
                    if "SlippageExceeded" in result.revert_reason:
                        logger.warning("Slippage check failed on-chain — market moved, aborting")
                        return result

                # Retry on transient errors (e.g. network timeout)
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))

        return ExecutionResult(success=False, error="All lenders and retries failed")

    async def _attempt_execution(self, opp: Any, lender: str) -> ExecutionResult:
        """
        Build, simulate, sign and submit a single arb transaction.

        uses `opp.hop_amounts` (list of per-hop expected outputs) if present,
        falling back to a conservative estimate derived from `opp.expected_profit`
        and `opp.amount_in` for backward compatibility.
        """
        # Guard: abort if the opportunity deadline has already expired
        if hasattr(opp, "created_at") and self.guard.is_deadline_expired(
            opp.created_at + self.guard.deadline_seconds
        ):
            logger.warning("[Executor] Opportunity deadline expired before submission — skipping.")
            return ExecutionResult(success=False, error="Opportunity deadline expired")

        try:
            swaps = self._build_swaps(opp)
            arb_params = (
                Web3.to_checksum_address(lender),
                Web3.to_checksum_address(opp.tokens[0].address),
                int(opp.amount_in),
                swaps,
            )

            # Simulation
            try:
                gas_estimate = self.arb_bot.functions.executeArbitrage(arb_params).estimate_gas(
                    {"from": self.account.address}
                )
            except Exception as e:
                revert_reason = self._parse_revert(str(e))
                logger.debug(f"[Executor] Simulation failed: {e}")
                return ExecutionResult(
                    success=False, error="Simulation failed", revert_reason=revert_reason
                )

            # Nonce management
            async with self._nonce_lock:
                if self._current_nonce is None:
                    self._current_nonce = self.w3.eth.get_transaction_count(
                        self.account.address
                    )
                nonce = self._current_nonce
                self._current_nonce += 1

            # Build transaction
            tx_dict = self.arb_bot.functions.executeArbitrage(arb_params).build_transaction(
                {
                    "from": self.account.address,
                    "nonce": nonce,
                    "gas": int(gas_estimate * self.SIMULATION_GAS_BUFFER),
                }
            )

            if self.mev_submitter:
                tx_dict = self.mev_submitter.build_with_priority(tx_dict)
            else:
                tx_dict["gasPrice"] = int(self.w3.eth.gas_price * 1.1)

            signed = self.w3.eth.account.sign_transaction(tx_dict, self.private_key)

            # Submission — private RPC with automatic public fallback
            if self.mev_submitter:
                tx_hash = await self.mev_submitter.submit_private(
                    signed.raw_transaction,
                    is_critical=False,  # Arb: accept MEV risk if private fails
                )
            else:
                tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction).hex()

            if not tx_hash:
                return ExecutionResult(success=False, error="Submission failed (no tx_hash)")

            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            if receipt.status == 1:
                return ExecutionResult(
                    success=True,
                    tx_hash=tx_hash,
                    profit_usd=opp.profit_usd,
                    gas_used=receipt.gasUsed,
                )
            else:
                return ExecutionResult(
                    success=False,
                    tx_hash=tx_hash,
                    error="Transaction reverted on-chain",
                )

        except Exception as e:
            async with self._nonce_lock:
                self._current_nonce = None  # Reset nonce on error
            return ExecutionResult(
                success=False,
                error=str(e),
                revert_reason=self._parse_revert(str(e)),
            )

    def _build_swaps(self, opp: Any) -> List[tuple]:
        """
        Build the SwapParams tuple list for the flash arb contract.

        Slippage protection:
          - Intermediate hops: minAmountOut = guard.min_amount_out(expected_hop_out)
          - Final hop: minAmountOut = amount_in (must at least break even for the
            contract's profitability check to pass, then contract enforces minProfitBps)

        Expected per-hop amounts are sourced from `opp.hop_amounts` if available
        (populated by GraphArbScanner.evaluate_cycle). If not present, a conservative
        estimate is used.
        """
        n = len(opp.pools)
        hop_amounts: List[int] = getattr(opp, "hop_amounts", [])

        swaps = []
        for i, pool in enumerate(opp.pools):
            token_in = opp.tokens[i]
            token_out = pool.token1 if pool.token0.address == token_in.address else pool.token0

            # Determine minAmountOut for this hop
            if i < n - 1:
                # Intermediate hop: apply slippage to expected output
                if i < len(hop_amounts) and hop_amounts[i] > 0:
                    min_out = self.guard.min_amount_out(hop_amounts[i])
                else:
                    # Fallback: conservative 1% below input amount (rough estimate)
                    in_amount = opp.amount_in if i == 0 else (
                        hop_amounts[i - 1] if i - 1 < len(hop_amounts) else opp.amount_in
                    )
                    min_out = self.guard.min_amount_out(in_amount)
            else:
                # Final hop: must return at least the original borrowed amount
                # The contract enforces minProfitBps on top of this
                expected_final = (
                    hop_amounts[i] if i < len(hop_amounts) and hop_amounts[i] > 0
                    else opp.amount_in + opp.expected_profit
                )
                min_out = self.guard.min_amount_out(expected_final)
                # Ensure we require at least break-even
                min_out = max(min_out, opp.amount_in)

            swaps.append((
                int(pool.dex),
                Web3.to_checksum_address(pool.router)
                if pool.router
                else "0x0000000000000000000000000000000000000000",
                Web3.to_checksum_address(token_in.address),
                Web3.to_checksum_address(token_out.address),
                int(opp.amount_in if i == 0 else 0),
                int(min_out),
                pool.stable,
                pool.fee,
                pool.extra_data,
            ))

        logger.debug(
            f"[Executor] Built {n} swaps with slippage={self.guard.slippage_bps} bps. "
            f"hop_amounts={hop_amounts}"
        )
        return swaps

    def _parse_revert(self, error_str: str) -> Optional[str]:
        for reason in [
            "ArbNotProfitable",
            "UnauthorizedLender",
            "SolvencyCheckFailed",
            "SwapFailed",
            "SlippageExceeded",
        ]:
            if reason in error_str:
                return reason
        return None