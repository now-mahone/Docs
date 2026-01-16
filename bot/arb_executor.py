# Created: 2026-01-16
import asyncio
import time
from enum import Enum
from typing import List, Optional, Tuple, Dict, Any
from dataclasses import dataclass
from loguru import logger
from web3 import Web3
from web3.contract import Contract

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
    - Revert handling & retry
    - Nonce management
    """
    
    MAX_RETRIES = 2
    SIMULATION_GAS_BUFFER = 1.3
    
    def __init__(self, w3: Web3, arb_bot_contract: Contract, private_key: str, mev_submitter=None):
        self.w3 = w3
        self.arb_bot = arb_bot_contract
        self.private_key = private_key
        self.account = w3.eth.account.from_key(private_key)
        self.mev_submitter = mev_submitter
        self._nonce_lock = asyncio.Lock()
        self._current_nonce = None
    
    async def execute_with_fallback(
        self, 
        opp: Any, # ArbPath
        lenders: List[Tuple[str, LenderPriority]]
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
                
                # Retry on transient errors (e.g. network timeout)
                if attempt < self.MAX_RETRIES - 1:
                    await asyncio.sleep(0.5 * (attempt + 1))
        
        return ExecutionResult(success=False, error="All lenders and retries failed")

    async def _attempt_execution(self, opp: Any, lender: str) -> ExecutionResult:
        try:
            swaps = self._build_swaps(opp)
            arb_params = (
                Web3.to_checksum_address(lender),
                Web3.to_checksum_address(opp.tokens[0].address),
                int(opp.amount_in),
                swaps
            )
            
            # Simulation
            try:
                gas_estimate = self.arb_bot.functions.executeArbitrage(arb_params).estimate_gas({
                    'from': self.account.address
                })
            except Exception as e:
                revert_reason = self._parse_revert(str(e))
                return ExecutionResult(success=False, error="Simulation failed", revert_reason=revert_reason)
            
            # Nonce management
            async with self._nonce_lock:
                if self._current_nonce is None:
                    self._current_nonce = self.w3.eth.get_transaction_count(self.account.address)
                nonce = self._current_nonce
                self._current_nonce += 1
            
            # Build transaction
            tx_dict = self.arb_bot.functions.executeArbitrage(arb_params).build_transaction({
                'from': self.account.address,
                'nonce': nonce,
                'gas': int(gas_estimate * self.SIMULATION_GAS_BUFFER),
            })
            
            if self.mev_submitter:
                tx_dict = self.mev_submitter.build_with_priority(tx_dict)
            else:
                tx_dict['gasPrice'] = int(self.w3.eth.gas_price * 1.1)
                
            signed = self.w3.eth.account.sign_transaction(tx_dict, self.private_key)
            
            # Submission
            if self.mev_submitter:
                tx_hash = await self.mev_submitter.submit_private(signed.raw_transaction)
            else:
                tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction).hex()
            
            if not tx_hash:
                return ExecutionResult(success=False, error="Submission failed (no tx_hash)")
                
            # Wait for receipt
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)
            
            if receipt.status == 1:
                return ExecutionResult(success=True, tx_hash=tx_hash, profit_usd=opp.profit_usd, gas_used=receipt.gasUsed)
            else:
                return ExecutionResult(success=False, tx_hash=tx_hash, error="Transaction reverted on-chain")
                
        except Exception as e:
            async with self._nonce_lock:
                self._current_nonce = None # Reset nonce on error
            return ExecutionResult(success=False, error=str(e), revert_reason=self._parse_revert(str(e)))

    def _build_swaps(self, opp: Any) -> List[tuple]:
        swaps = []
        for i, pool in enumerate(opp.pools):
            token_in = opp.tokens[i]
            token_out = pool.token1 if pool.token0.address == token_in.address else pool.token0
            
            swaps.append((
                int(pool.dex),
                Web3.to_checksum_address(pool.router) if pool.router else "0x0000000000000000000000000000000000000000",
                Web3.to_checksum_address(token_in.address),
                Web3.to_checksum_address(token_out.address),
                int(opp.amount_in if i == 0 else 0),
                1, # minAmountOut
                pool.stable,
                pool.fee,
                pool.extra_data
            ))
        return swaps

    def _parse_revert(self, error_str: str) -> Optional[str]:
        for reason in ["ArbNotProfitable", "UnauthorizedLender", "SolvencyCheckFailed", "SwapFailed"]:
            if reason in error_str:
                return reason
        return None
