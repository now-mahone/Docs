# Created: 2026-01-16
from web3 import Web3
from typing import Tuple, List
from loguru import logger
from enum import IntEnum

class DEX(IntEnum):
    AERODROME = 0
    UNISWAP_V3 = 1
    UNISWAP_V2 = 2
    MAVERICK = 3
    PANCAKE_V3 = 4

class BaseGasEstimator:
    """
    Precise gas cost estimation for Base L2.
    Accounts for L2 execution gas and L1 data availability fees.
    """
    
    GAS_ORACLE = "0x420000000000000000000000000000000000000F"
    
    GAS_ORACLE_ABI = [
        {"inputs": [{"name": "_data", "type": "bytes"}], "name": "getL1Fee", 
         "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    ]
    
    # Empirical gas estimates per DEX swap
    GAS_PER_SWAP = {
        DEX.AERODROME: 180_000,
        DEX.UNISWAP_V3: 150_000,
        DEX.UNISWAP_V2: 120_000,
        DEX.MAVERICK: 200_000,
        DEX.PANCAKE_V3: 160_000,
    }
    
    BASE_FLASH_LOAN_GAS = 120_000  # Flash loan + contract overhead
    
    def __init__(self, w3: Web3):
        self.w3 = w3
        self.oracle = w3.eth.contract(
            address=Web3.to_checksum_address(self.GAS_ORACLE),
            abi=self.GAS_ORACLE_ABI
        )
    
    def estimate_arb_gas(self, swap_dexes: List[DEX], calldata: bytes) -> Tuple[int, int, int]:
        """
        Returns: (l2_gas_cost_wei, l1_fee_wei, total_cost_wei)
        """
        # L2 execution gas
        l2_gas_limit = self.BASE_FLASH_LOAN_GAS
        for dex in swap_dexes:
            l2_gas_limit += self.GAS_PER_SWAP.get(dex, 150_000)
        
        # Add buffer
        l2_gas_limit = int(l2_gas_limit * 1.2)
        
        l2_gas_price = self.w3.eth.gas_price
        l2_cost = l2_gas_limit * l2_gas_price
        
        # L1 data fee
        try:
            l1_fee = self.oracle.functions.getL1Fee(calldata).call()
        except Exception as e:
            logger.warning(f"L1 fee estimation failed: {e}")
            l1_fee = int(0.00005 * 1e18) # Conservative fallback
        
        return l2_cost, l1_fee, l2_cost + l1_fee
    
    def is_profitable_after_gas(
        self, 
        gross_profit_wei: int, 
        swap_dexes: List[DEX], 
        calldata: bytes,
        min_profit_usd: float,
        eth_price: float
    ) -> Tuple[bool, float]:
        """
        Returns: (is_profitable, net_profit_usd)
        """
        _, _, total_gas_cost = self.estimate_arb_gas(swap_dexes, calldata)
        
        if gross_profit_wei <= total_gas_cost:
            return False, 0.0
        
        net_profit_wei = gross_profit_wei - total_gas_cost
        net_profit_usd = (net_profit_wei / 1e18) * eth_price
        
        return net_profit_usd >= min_profit_usd, net_profit_usd
