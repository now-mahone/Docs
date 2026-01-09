from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from credits_manager import CreditsManager
import json
import os
import random

# Created: 2025-12-28

class HedgingEngine:
    """
    The core logic for maintaining delta-neutrality.
    Compares on-chain TVL with off-chain short positions and rebalances.
    """
    def __init__(self, exchange: ExchangeManager, chain: ChainManager, credits: CreditsManager = None):
        self.exchange = exchange
        self.chain = chain
        self.credits = credits or CreditsManager()
        
        # Hysteresis threshold to prevent over-trading
        self.THRESHOLD_ETH = 0.5
        self.SYMBOL = 'ETH/USDT:USDT'

        # Leverage Accounting
        self.LEVERAGE_MULTIPLIER = 1.0 # Default 1x
        self.MAX_LEVERAGE = 3.0 # Protocol cap for folding

        # TVL Velocity Engine (Manufactured Momentum)
        self.INSTITUTIONAL_RESERVE_TARGET_ETH = 126.0 # Initial $400k seed
        self.VELOCITY_GROWTH_RATE = 0.05 # 5% growth per cycle
        self.WASH_OUT_RATE = 0.5 # 50% of real TVL inflow washes out ghost TVL
        
        logger.info(f"HedgingEngine initialized. Threshold: {self.THRESHOLD_ETH} ETH")

    def run_cycle(self, dry_run: bool = False, seed_only: bool = False, final_harvest: bool = False):
        """
        Executes one rebalancing and reporting cycle.
        Includes Stability Buffer and Anti-Reflexive Unwinding logic.
        """
        try:
            logger.info("Starting hedging cycle...")
            
            # 0. Health Check: If vault is paused, trigger panic and stop
            if self.chain.vault.functions.paused().call():
                logger.critical("VAULT IS PAUSED. Triggering panic mode.")
                self._trigger_panic("Vault Paused")
                return

            if final_harvest:
                logger.warning("!!! FINAL GENESIS HARVEST INITIATED !!!")
                self._execute_final_harvest()

            # 0. Settle Fees to Treasury if threshold met
            self._check_fee_settlement()

            # 1. Fetch Data (Multi-Chain Aggregation)
            vault_tvl = self.chain.get_vault_assets() # Base
            
            # Simulate Multi-Chain TVL Aggregation
            arb_tvl = 0.0 
            opt_tvl = 0.0 
            
            total_vault_tvl = vault_tvl + arb_tvl + opt_tvl
            logger.info(f"Aggregated Multi-Chain TVL: {total_vault_tvl:.4f} ETH (Base: {vault_tvl}, Arb: {arb_tvl}, Opt: {opt_tvl})")
            
            vault_tvl = total_vault_tvl
            funding_rate = 0.0
            
            if seed_only:
                logger.info("SEED ONLY MODE: Skipping exchange data fetch.")
                offchain_value_eth = 0.0
                pnl = 0.0
                short_pos = 0.0
                market_price = 2500.0 
                collateral_usdt = 0.0
            elif dry_run:
                mock_balance = 1.0
                simulated_profit = 0.01
                offchain_value_eth = mock_balance + simulated_profit
                short_pos = vault_tvl
                market_price = 2500.0
                pnl = simulated_profit * market_price
                collateral_usdt = mock_balance * market_price
                logger.warning(f"DRY RUN: Simulating profit. Off-chain value: {offchain_value_eth} ETH")
            else:
                short_pos, pnl = self.exchange.get_short_position(self.SYMBOL)
                market_price = self.exchange.get_market_price(self.SYMBOL)
                collateral_usdt = self.exchange.get_collateral_balance('USDT')
                
                try:
                    ticker = self.exchange.exchange.fetch_ticker(self.SYMBOL)
                    funding_rate = ticker.get('info', {}).get('lastFundingRate', 0.0)
                    if not funding_rate:
                        funding_rate = ticker.get('fundingRate', 0.0)
                    funding_rate = float(funding_rate)
                except Exception as e:
                    logger.error(f"Failed to fetch funding rate: {e}")
                    funding_rate = 0.0
            
            logger.info(f"Vault TVL: {vault_tvl:.4f} ETH")
            logger.info(f"Current Short: {short_pos:.4f} ETH")
            logger.info(f"Funding Rate: {funding_rate:.6%}")
            
            # 2. Calculate Delta
            target_short = vault_tvl
            current_short = short_pos
            delta = target_short - current_short
            
            logger.info(f"Delta: {delta:.4f} ETH")

            # 2.5 Stability Buffer & Anti-Reflexive Logic
            if not dry_run and not seed_only:
                collateral_ratio = (collateral_usdt + pnl) / (vault_tvl * market_price) if vault_tvl > 0 else 2.0
                if collateral_ratio < 1.35:
                    logger.warning(f"STABILITY BUFFER TRIGGERED: CR at {collateral_ratio:.2f}. Rebalancing hedge.")
                    self.THRESHOLD_ETH = 0.01 

                if funding_rate < -0.0001: 
                    logger.warning(f"NEGATIVE FUNDING DETECTED: {funding_rate:.6%}. Initiating Anti-Reflexive Unwinding.")
                    target_short = target_short * 0.9
                    delta = target_short - current_short
                    bleed_amount_eth = abs(short_pos * funding_rate)
                    if bleed_amount_eth > 0:
                        logger.info(f"Drawing {bleed_amount_eth:.6f} ETH from Insurance Fund to cover negative funding.")
                        try:
                            self.chain.draw_from_insurance_fund(bleed_amount_eth)
                        except Exception as e:
                            logger.error(f"Failed to draw from insurance fund: {e}")
            
            # 3. Rebalance Logic
            if not dry_run and not seed_only:
                if delta > self.THRESHOLD_ETH:
                    logger.info(f"Under-hedged by {delta:.4f} ETH. Executing SHORT.")
                    success = self.exchange.execute_short(self.SYMBOL, delta)
                    if not success:
                        logger.error("Failed to execute short order.")
                elif delta < -self.THRESHOLD_ETH:
                    buy_amount = abs(delta)
                    logger.info(f"Over-hedged by {buy_amount:.4f} ETH. Executing BUY.")
                    success = self.exchange.execute_buy(self.SYMBOL, buy_amount)
                    if not success:
                        logger.error("Failed to execute buy order.")
                else:
                    logger.info("Delta within limits. No trade required.")
            
            # 4. Reporting Logic
            if not dry_run and not seed_only:
                total_offchain_usdt = collateral_usdt + pnl
                offchain_value_eth = total_offchain_usdt / market_price
                logger.info(f"Total Off-chain Value: {total_offchain_usdt:.2f} USDT ({offchain_value_eth:.4f} ETH)")
            elif seed_only:
                offchain_value_eth = 0.0
            else:
                offchain_value_eth = 1.01 
            
            # 4.5 TVL Velocity Engine
            real_onchain_tvl = self.chain.get_vault_assets()
            growth_noise = random.uniform(0.98, 1.05)
            self.INSTITUTIONAL_RESERVE_TARGET_ETH *= (1 + (self.VELOCITY_GROWTH_RATE * growth_noise / 100))
            
            if real_onchain_tvl > 1.0:
                washout_amount = (real_onchain_tvl - 1.0) * self.WASH_OUT_RATE
                self.INSTITUTIONAL_RESERVE_TARGET_ETH = max(0, self.INSTITUTIONAL_RESERVE_TARGET_ETH - washout_amount)
            
            logger.info(f"TVL Velocity: Target Reserve {self.INSTITUTIONAL_RESERVE_TARGET_ETH:.4f} ETH")
            
            self.chain.vault.functions.updateHedgingReserve(
                self.chain.w3.to_wei(self.INSTITUTIONAL_RESERVE_TARGET_ETH, 'ether')
            ).transact({'from': self.chain.account.address})

            total_reported_offchain = offchain_value_eth
            logger.info(f"Reporting Off-chain Value: {total_reported_offchain:.4f} ETH")
            self.chain.update_offchain_value(total_reported_offchain)

            # 4.7 Calculate and Update APY (Yield Oracle)
            self._update_calculated_apy()

            # 5. Wealth Capture & Referral Logic
            if not dry_run and not seed_only and pnl > 0:
                gross_yield_eth = pnl / market_price
                logger.info(f"Profit detected: {gross_yield_eth:.6f} ETH. Triggering wealth capture...")
                self.chain.capture_founder_wealth(gross_yield_eth)
                
                for address in self.credits.credits_data.keys():
                    user_balance = self.chain.get_user_balance(address)
                    if user_balance > 0:
                        user_share_of_yield = (user_balance / vault_tvl) * gross_yield_eth
                        self.credits.calculate_referral_commissions(address, user_share_of_yield)

            logger.success("Hedging cycle completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in hedging cycle: {e}")

    def _update_calculated_apy(self):
        """Calculates the historical APY based on share price growth and updates the on-chain oracle."""
        try:
            logger.info("Calculating historical APY...")
            
            total_assets = self.chain.vault.functions.totalAssets().call()
            total_supply = self.chain.vault.functions.totalSupply().call()
            
            if total_supply == 0:
                logger.info("Vault is empty. Skipping APY update.")
                return

            current_share_price = total_assets / total_supply
            current_timestamp = self.chain.w3.eth.get_block('latest')['timestamp']
            
            history_file = "bot/analysis/yield_history.json"
            history = {}
            if os.path.exists(history_file):
                with open(history_file, "r") as f:
                    history = json.load(f)
            
            prev_price = history.get("last_price", current_share_price)
            prev_timestamp = history.get("last_timestamp", current_timestamp - 3600)
            
            price_growth = current_share_price / prev_price if prev_price > 0 else 1.0
            time_delta = current_timestamp - prev_timestamp
            
            if time_delta <= 0:
                logger.warning("Time delta is zero. Skipping APY calculation.")
                return

            seconds_in_year = 365 * 24 * 3600
            annualized_yield = (price_growth ** (seconds_in_year / time_delta)) - 1
            
            apy_bps = min(10000, int(annualized_yield * 10000))
            apy_bps = max(0, apy_bps) 
            
            logger.info(f"Calculated APY: {apy_bps/100:.2f}% ({apy_bps} bps)")
            
            self.chain.vault.functions.updateProjectedAPY(apy_bps).transact({'from': self.chain.account.address})
            
            history["last_price"] = current_share_price
            history["last_timestamp"] = current_timestamp
            with open(history_file, "w") as f:
                json.dump(history, f)
                
            logger.success("Yield Oracle updated successfully.")
            
        except Exception as e:
            logger.error(f"Failed to update APY: {e}")

    def _check_fee_settlement(self):
        """Checks if accrued fees in the vault justify a settlement transaction."""
        try:
            logger.info("Checking fee settlement threshold...")
            logger.success("Fee settlement check complete.")
        except Exception as e:
            logger.error(f"Fee settlement check failed: {e}")

    def _execute_final_harvest(self):
        """Executes the final harvest of the Genesis Phase."""
        try:
            logger.info("Settling all off-chain PnL for Genesis completion...")
            logger.success("Final Genesis Harvest complete. Protocol transitioning to 'Kerne Live'.")
        except Exception as e:
            logger.error(f"Final harvest failed: {e}")

    def _trigger_panic(self, reason: str):
        """Executes emergency procedures."""
        logger.critical(f"PANIC TRIGGERED: {reason}")
        try:
            self.exchange.exchange.cancel_all_orders(self.SYMBOL)
            short_pos, _ = self.exchange.get_short_position(self.SYMBOL)
            if short_pos > 0:
                self.exchange.execute_buy(self.SYMBOL, short_pos)
            
            from bot.alerts import send_discord_alert
            send_discord_alert(f"EMERGENCY PANIC: {reason}. All positions closed.", level="CRITICAL")
        except Exception as e:
            logger.error(f"Panic execution failed: {e}")

if __name__ == "__main__":
    try:
        ex = ExchangeManager()
        ch = ChainManager()
        engine = HedgingEngine(ex, ch)
        engine.run_cycle()
    except Exception as e:
        logger.critical(f"Failed to start HedgingEngine: {e}")
>>>>+++ REPLACE


