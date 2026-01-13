# Created: 2026-01-13
import os
from loguru import logger

class MultiChainConfig:
    """
    Unified configuration layer for multi-chain solver operations.
    """
    def __init__(self):
        self.max_position_usd = float(os.getenv("MAX_POSITION_USD", "15.0")) # Safety cap for $20 balance
        self.min_profit_bps = float(os.getenv("MIN_PROFIT_BPS", "2.0"))
        self.chains = {
            "base": {
                "chain_id": 8453,
                "rpc": os.getenv("RPC_URL", "").split(',')[0],
                "executor": os.getenv("INTENT_EXECUTOR_BASE", "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd"),
                "lst_targets": ["wstETH", "cbETH", "rETH"]
            },
            "arbitrum": {
                "chain_id": 42161,
                "rpc": os.getenv("ARB_RPC_URL", ""),
                "executor": os.getenv("INTENT_EXECUTOR_ARB", ""),
                "lst_targets": ["wstETH", "rETH"]
            },
            "optimism": {
                "chain_id": 10,
                "rpc": os.getenv("OPT_RPC_URL", ""),
                "executor": os.getenv("INTENT_EXECUTOR_OPT", ""),
                "lst_targets": ["wstETH", "cbETH"]
            }
        }
        self.active_chain = os.getenv("ACTIVE_CHAIN", "base").lower()
        logger.info(f"Multi-Chain Config: Active Chain set to {self.active_chain}")

    def get_active_config(self):
        return self.chains.get(self.active_chain, self.chains["base"])

    def switch_chain(self, chain_name):
        if chain_name in self.chains:
            self.active_chain = chain_name
            logger.info(f"Multi-Chain Config: Switched to {chain_name}")
            return True
        return False

if __name__ == "__main__":
    config = MultiChainConfig()
    print(config.get_active_config())
