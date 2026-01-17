from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from credits_manager import CreditsManager
import json
import os
import random
import math

# Created: 2025-12-28
# Updated: 2026-01-16 (Multi-Exchange & Solvency Bridge)

class HedgingEngine:
    """
    The core logic for maintaining delta-neutrality and protocol solvency.
    Aggregates equity across multiple CEXs and reports to the on-chain vault.
    """
    def __init__(self, exchange: ExchangeManager, chain: ChainManager, credits: CreditsManager = None):
        self.exchange = exchange
        self.chain = chain
        self.credits = credits or CreditsManager()
        
        # Hysteresis threshold to prevent over-trading
        self.THRESHOLD_ETH = 0.05 
        self.SYMBOL = 'ETH'

        # Dynamic Leverage Parameters
        self.MIN_LEVERAGE = 1.5
        self.MAX_LEVERAGE = 12.0
        self.RISK_AVERSION_FACTOR = 2.5 
        
        # Settlement Threshold (in ETH)
        self.SETTLEMENT_THRESHOLD = 0.01 
        
        logger.info(f"HedgingEngine initialized with Solvency Bridge. Symbol: {self.SYMBOL}")

    def calculate_optimal_leverage(self, funding_rate: float, lst_yield: float = 0.035) -> float:
        try:
            base_vol = 0.05
            annual_funding = funding_rate * 24 * 365
            numerator = annual_funding + lst_yield
            denominator = (base_vol ** 2) * self.RISK_AVERSION_FACTOR
            if denominator == 0: return self.MIN_LEVERAGE
            optimal = numerator / denominator
            return max(self.MIN_LEVERAGE, min(self.MAX_LEVERAGE, optimal))
        except Exception as e:
            logger.error(f"Error calculating optimal leverage: {e}")
            return self.MIN_LEVERAGE

    def run_cycle(self, dry_run: bool = False, **kwargs):
        """
        Executes one rebalancing, solvency verification, and reporting cycle.
        """
        seed_only = kwargs.get('seed_only', False)
        try:
            logger.info(f"Starting automated solvency bridge cycle... {'(SEED ONLY)' if seed_only else ''}")
            
            # 0. Health Check
            if not dry_run and self.chain.vault.functions.paused().call():
                logger.warning("VAULT IS PAUSED. Rebalancing suspended to maintain delta-neutrality.")
                # We do NOT close shorts automatically, as that would leave the protocol long ETH.
                # Only alert and wait for manual intervention or unpause.
                return

            # 1. Fetch Data
            multi_chain_tvl = self.chain.get_multi_chain_tvl()
            total_vault_tvl = sum(multi_chain_tvl.values())
            on_chain_assets = self.chain.get_on_chain_assets()
            
            logger.info(f"On-chain TVL: {total_vault_tvl:.4f} ETH (Liquid: {on_chain_assets:.4f} ETH)")
            
            if dry_run:
                market_price = 2500.0
                funding_rate = 0.00002
                agg_pos = {"size": 0.0, "upnl": 0.0}
                total_cex_equity_usd = 100000.0
            else:
                market_price = self.exchange.get_market_price(self.SYMBOL)
                funding_rate = self.exchange.get_funding_rate(self.SYMBOL)
                agg_pos = self.exchange.get_aggregate_position(self.SYMBOL)
                total_cex_equity_usd = self.exchange.get_total_equity()

            short_pos = agg_pos["size"]
            total_upnl = agg_pos["upnl"]

            # 2. Solvency Calculation
            offchain_value_eth = total_cex_equity_usd / market_price if market_price > 0 else 0
            total_protocol_assets = on_chain_assets + offchain_value_eth
            
            solvency_ratio = (total_protocol_assets / total_vault_tvl) if total_vault_tvl > 0 else 1.0
            logger.info(f"Solvency Analysis: Assets {total_protocol_assets:.4f} ETH / Liabilities {total_vault_tvl:.4f} ETH")
            logger.info(f"Current Solvency Ratio: {solvency_ratio*100:.2f}%")

            if solvency_ratio < 1.0:
                logger.warning(f"PROTOCOL UNDERCOLLATERALIZED: {solvency_ratio*100:.2f}%")
                # In a real scenario, we might trigger an alert or emergency rebalance

            # 3. Target Hedge Calculation
            # We hedge 100% of the TVL to stay delta-neutral.
            target_short = total_vault_tvl 
            delta = target_short - short_pos
            logger.info(f"Hedge Status: Target {target_short:.4f} ETH, Current {short_pos:.4f} ETH, Delta {delta:.4f}")

            # 4. Rebalance & Settlement
            if not dry_run:
                # Rebalance if delta exceeds threshold
                if abs(delta) > self.THRESHOLD_ETH:
                    if delta > 0:
                        self.exchange.execute_short(self.SYMBOL, delta)
                    else:
                        self.exchange.execute_buy(self.SYMBOL, abs(delta))
                
                # Automated PnL Settlement (Capture Wealth)
                # If unrealized PnL is significantly positive, we report it to grow totalAssets on-chain
                # If we want to realize it, we would need to close positions, but here we just report equity.
                
                # 5. Reporting to Chain
                self.chain.update_offchain_value(offchain_value_eth)
                self.chain.update_yield_oracle()
                
                # If we have significant profit, capture founder wealth (fees)
                # This assumes 'pnl' here is the profit since last report. 
                # For simplicity, we use a small fraction of total equity as 'yield' if solvency > 101%
                if solvency_ratio > 1.01:
                    excess_yield = total_protocol_assets - total_vault_tvl
                    if excess_yield > self.SETTLEMENT_THRESHOLD:
                        logger.info(f"Settling excess yield: {excess_yield:.4f} ETH")
                        self.chain.capture_founder_wealth(excess_yield)

            logger.success("Solvency bridge cycle completed.")
            
        except Exception as e:
            logger.error(f"Error in hedging cycle: {e}")

    def _trigger_panic(self, reason: str):
        logger.critical(f"PANIC: {reason}")
        agg_pos = self.exchange.get_aggregate_position(self.SYMBOL)
        if agg_pos["size"] > 0:
            self.exchange.execute_buy(self.SYMBOL, agg_pos["size"])

if __name__ == "__main__":
    # Mock objects for dry run
    from exchange_manager import ExchangeManager
    from chain_manager import ChainManager
    
    # This will fail if env vars are missing, so we use mocks if needed
    try:
        engine = HedgingEngine(ExchangeManager(), ChainManager())
        engine.run_cycle(dry_run=True)
    except Exception as e:
        logger.warning(f"Could not initialize real managers: {e}")
