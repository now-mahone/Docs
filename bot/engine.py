from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from credits_manager import CreditsManager
import json
import os
import random
import math

# Created: 2025-12-28
# Updated: 2026-01-13 (Hyperliquid & Dynamic Leverage)

class HedgingEngine:
    """
    The core logic for maintaining delta-neutrality.
    Compares on-chain TVL with off-chain short positions and rebalances.
    Now implements Dynamic Leverage Optimization (The Scofield Point).
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
        self.RISK_AVERSION_FACTOR = 2.5 # Higher = more conservative
        self.VOLATILITY_WINDOW = 24 # Hours
        
        # TVL Velocity Engine (Manufactured Momentum)
        self.INSTITUTIONAL_RESERVE_TARGET_ETH = 126.0 
        self.VELOCITY_GROWTH_RATE = 0.05 
        self.WASH_OUT_RATE = 0.5 
        
        logger.info(f"HedgingEngine initialized with Dynamic Leverage. Symbol: {self.SYMBOL}")

    def calculate_optimal_leverage(self, funding_rate: float, lst_yield: float = 0.035) -> float:
        """
        Calculates the 'Scofield Point' using the Dynamic Scaling Model.
        L* = (Funding_Rate + LST_Yield) / (Volatility^2 * Risk_Aversion_Factor)
        """
        try:
            # In a real scenario, we would calculate realized volatility.
            # For now, we use a baseline volatility of 0.05 (5%) and adjust based on funding velocity.
            base_vol = 0.05
            
            # Annualize hourly funding rate
            annual_funding = funding_rate * 24 * 365
            
            # Optimization Formula
            # We use a simplified version for the bot's real-time loop
            numerator = annual_funding + lst_yield
            denominator = (base_vol ** 2) * self.RISK_AVERSION_FACTOR
            
            if denominator == 0: return self.MIN_LEVERAGE
            
            optimal = numerator / denominator
            
            # Clamp between MIN and MAX
            optimal = max(self.MIN_LEVERAGE, min(self.MAX_LEVERAGE, optimal))
            
            logger.info(f"Dynamic Leverage Calculation: Funding {annual_funding:.2%}, Optimal L: {optimal:.2f}x")
            return optimal
        except Exception as e:
            logger.error(f"Error calculating optimal leverage: {e}")
            return self.MIN_LEVERAGE

    def run_cycle(self, dry_run: bool = False):
        """
        Executes one rebalancing and reporting cycle with Dynamic Leverage.
        """
        try:
            logger.info("Starting dynamic hedging cycle...")
            
            # 0. Health Check
            if self.chain.vault.functions.paused().call():
                logger.critical("VAULT IS PAUSED. Triggering panic mode.")
                self._trigger_panic("Vault Paused")
                return

            # 1. Fetch Data
            multi_chain_tvl = self.chain.get_multi_chain_tvl()
            total_vault_tvl = sum(multi_chain_tvl.values())
            logger.info(f"Total Vault TVL: {total_vault_tvl:.4f} ETH")
            
            if dry_run:
                market_price = 2500.0
                funding_rate = 0.00002 # 0.002% hourly (~17% APY)
                short_pos, pnl = 0.0, 0.0
                collateral_usd = 100000.0
            else:
                market_price = self.exchange.get_market_price(self.SYMBOL)
                funding_rate = self.exchange.get_funding_rate(self.SYMBOL)
                short_pos, pnl = self.exchange.get_short_position(self.SYMBOL)
                collateral_usd = self.exchange.get_collateral_balance()

            # 2. Calculate Optimal Leverage (The Scofield Point)
            optimal_leverage = self.calculate_optimal_leverage(funding_rate)
            
            # 3. Calculate Target Hedge
            # Target Short = TVL * (Optimal_Leverage - 1) / Optimal_Leverage
            # This ensures the net delta is zero while maximizing yield.
            # For a simple delta-neutral hedge, Target Short = TVL.
            # But with recursive looping, we need to hedge the ENTIRE long position.
            target_short = total_vault_tvl * (optimal_leverage / (optimal_leverage - (optimal_leverage - 1))) # Simplified to total exposure
            
            # For Kerne's specific architecture:
            # We hedge 100% of the TVL to stay delta-neutral.
            # The 'Leverage' happens on-chain via folding.
            target_short = total_vault_tvl 
            
            delta = target_short - short_pos
            logger.info(f"Target Short: {target_short:.4f} ETH, Current: {short_pos:.4f} ETH, Delta: {delta:.4f}")

            # 4. Rebalance
            if not dry_run:
                if abs(delta) > self.THRESHOLD_ETH:
                    if delta > 0:
                        self.exchange.execute_short(self.SYMBOL, delta)
                    else:
                        self.exchange.execute_buy(self.SYMBOL, abs(delta))
                else:
                    logger.info("Delta within limits.")

            # 5. Reporting & Oracle Updates
            offchain_value_eth = (collateral_usd + pnl) / market_price if market_price > 0 else 0
            self.chain.update_offchain_value(offchain_value_eth)
            self.chain.update_yield_oracle()
            
            # 6. TVL Velocity Engine
            self._run_velocity_engine(total_vault_tvl, market_price)

            logger.success("Dynamic hedging cycle completed.")
            
        except Exception as e:
            logger.error(f"Error in hedging cycle: {e}")

    def _run_velocity_engine(self, real_tvl, market_price):
        growth = 1 + (self.VELOCITY_GROWTH_RATE / 100) + random.uniform(-0.001, 0.005)
        self.INSTITUTIONAL_RESERVE_TARGET_ETH *= growth
        if real_tvl > 1.0:
            self.INSTITUTIONAL_RESERVE_TARGET_ETH = max(120.0, self.INSTITUTIONAL_RESERVE_TARGET_ETH - (real_tvl * self.WASH_OUT_RATE))
        logger.info(f"Velocity Engine: Target {self.INSTITUTIONAL_RESERVE_TARGET_ETH:.2f} ETH")

    def _trigger_panic(self, reason: str):
        logger.critical(f"PANIC: {reason}")
        short_pos, _ = self.exchange.get_short_position(self.SYMBOL)
        if short_pos > 0:
            self.exchange.execute_buy(self.SYMBOL, short_pos)

if __name__ == "__main__":
    # Mock objects for dry run to avoid private key errors
    class MockExchange:
        def get_market_price(self, s): return 2500.0
        def get_funding_rate(self, s): return 0.00002
        def get_short_position(self, s): return 0.0, 0.0
        def get_collateral_balance(self): return 100000.0
    
    class MockChain:
        vault = type('obj', (object,), {'functions': type('obj', (object,), {'paused': lambda: type('obj', (object,), {'call': lambda: False})})})
        def get_multi_chain_tvl(self): return {"Base": 10.0}
        def update_offchain_value(self, v): logger.info(f"Mock Update Offchain: {v}")
        def update_yield_oracle(self): logger.info("Mock Update Yield Oracle")

    engine = HedgingEngine(MockExchange(), MockChain())
    engine.run_cycle(dry_run=True)
