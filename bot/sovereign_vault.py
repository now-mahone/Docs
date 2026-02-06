# Created: 2026-02-02
import os
from loguru import logger
from typing import Dict, List
from bot.chain_manager import ChainManager
from bot.exchange_manager import ExchangeManager

class SovereignVault:
    """
    The Autonomous Treasury Controller (ATC).
    Orchestrates capital movement between on-chain vaults, CEXs, and Hyperliquid.
    """
    def __init__(self, chain: ChainManager, exchange: ExchangeManager):
        self.chain = chain
        self.exchange = exchange
        
        # Watch-only addresses (e.g., Trezor, Cold Storage)
        self.watch_only_addresses = os.getenv("WATCH_ONLY_ADDRESSES", "").split(",")
        self.watch_only_addresses = [a.strip() for a in self.watch_only_addresses if a.strip()]
        
        # HL Bridge on Arbitrum
        self.HL_BRIDGE_ADDRESS = "0x2Df1c51E09a42Ad01097321978c7035100396630"
        self.USDC_ARB_ADDRESS = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

    def get_total_managed_assets(self) -> Dict[str, float]:
        """
        Aggregates assets across all managed and watched venues.
        """
        # 1. On-chain Managed (MetaMask/Vaults)
        managed_onchain = self.chain.get_multi_chain_tvl()
        
        # 2. Exchange Managed (Hyperliquid, Binance, etc.)
        managed_exchanges = {
            name: ex.get_total_equity() for name, ex in self.exchange.exchanges.items()
        }
        
        # 3. Watch-only (Trezor)
        watch_only_total = 0.0
        for addr in self.watch_only_addresses:
            # Simple ETH balance check for now, can be expanded to LSTs
            try:
                balance = self.chain.w3.eth.get_balance(addr)
                watch_only_total += float(self.chain.w3.from_wei(balance, 'ether'))
            except Exception as e:
                logger.error(f"Failed to fetch balance for watch-only address {addr}: {e}")
            
        return {
            "managed_onchain": managed_onchain,
            "managed_exchanges": managed_exchanges,
            "watch_only_eth": watch_only_total,
            "total_tvl_eth": sum(managed_onchain.values()) + watch_only_total
        }

    def rebalance_to_hyperliquid(self, amount_usd: float):
        """
        Moves USDC from Arbitrum wallet to Hyperliquid.
        """
        if not self.chain.arb_w3:
            logger.error("Arbitrum RPC not configured for rebalance.")
            return False
            
        logger.info(f"Initiating autonomous deposit of {amount_usd} USDC to Hyperliquid...")
        
        # 1. Check USDC balance on Arbitrum
        try:
            tx_hash = self.chain.transfer_erc20(
                token_address=self.USDC_ARB_ADDRESS,
                to_address=self.HL_BRIDGE_ADDRESS,
                amount=amount_usd,
                chain_name="Arbitrum"
            )
            if tx_hash:
                logger.success(f"Autonomous deposit to Hyperliquid successful: {tx_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to rebalance to HL: {e}")
            return False

    def sync_hedge_to_total_assets(self):
        """
        Adjusts the Hyperliquid short position to cover Managed + Watch-only assets.
        """
        assets = self.get_total_managed_assets()
        total_to_hedge = assets["total_tvl_eth"]
        
        hl = self.exchange.get_exchange("hyperliquid")
        if not hl:
            return
            
        current_short, _ = hl.get_position("ETH")
        delta = total_to_hedge - current_short
        
        if abs(delta) > 0.1: # Min threshold
            logger.info(f"Adjusting global hedge. Delta: {delta} ETH")
            if delta > 0:
                hl.execute_order("ETH", delta, "sell")
            else:
                hl.execute_order("ETH", abs(delta), "buy")

    def sync_l1_assets_to_vault(self):
        """
        Reports the Hyperliquid L1 equity back to the KerneVault contract.
        This fulfills the 'Sovereign Vault' native L1 settlement requirement.
        """
        hl = self.exchange.get_exchange("hyperliquid")
        if not hl:
            return False
            
        equity_usd = hl.get_total_equity()
        price = hl.get_market_price("ETH")
        equity_eth = equity_usd / price if price > 0 else 0
        
        logger.info(f"Syncing L1 Assets to Vault: {equity_eth:.4f} ETH (${equity_usd:.2f})")
        
        try:
            # Convert ETH to Wei for the contract call
            equity_wei = int(equity_eth * 1e18)
            
            # Call updateL1Assets on the vault
            tx_hash = self.chain.update_l1_assets(equity_wei)
            if tx_hash:
                logger.success(f"L1 Assets synced to vault: {tx_hash}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to sync L1 assets: {e}")
            return False
