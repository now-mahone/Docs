from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from credits_manager import CreditsManager
import json
import os
import random
import math
import time
from datetime import datetime, timedelta

# Created: 2025-12-28
# Updated: 2026-01-21 (Added KERNE Buyback Flywheel)

class HedgingEngine:
    """
    The core logic for maintaining delta-neutrality and protocol solvency.
    Aggregates equity across multiple CEXs and reports to the on-chain vault.
    Now includes the KERNE Buyback Flywheel for token value accrual.
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
        
        # ═══════════════════════════════════════════════════════════════════════════════
        # BUYBACK FLYWHEEL CONFIGURATION
        # ═══════════════════════════════════════════════════════════════════════════════
        
        # Minimum token balance to trigger buyback (prevents tiny gas-wasting txs)
        self.MIN_BUYBACK_THRESHOLD_WETH = float(os.getenv("BUYBACK_MIN_WETH", "0.01"))  # 0.01 ETH
        self.MIN_BUYBACK_THRESHOLD_USDC = float(os.getenv("BUYBACK_MIN_USDC", "25"))    # $25 USDC
        
        # Buyback frequency control
        self.BUYBACK_COOLDOWN_HOURS = int(os.getenv("BUYBACK_COOLDOWN_HOURS", "24"))
        self.last_buyback_time = None
        
        # Token addresses for buyback (Base Mainnet)
        self.WETH_ADDRESS = os.getenv("WETH_ADDRESS", "0x4200000000000000000000000000000000000006")
        self.USDC_ADDRESS = os.getenv("USDC_ADDRESS", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        
        # Buyback tracking
        self.buyback_log_path = os.path.join(os.path.dirname(__file__), "data", "buyback_log.json")
        self._ensure_buyback_log()
        
        logger.info(f"HedgingEngine initialized with Solvency Bridge + Buyback Flywheel. Symbol: {self.SYMBOL}")

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

    # ═══════════════════════════════════════════════════════════════════════════════
    # KERNE BUYBACK FLYWHEEL
    # ═══════════════════════════════════════════════════════════════════════════════
    
    def _ensure_buyback_log(self):
        """Ensure buyback log directory and file exist."""
        try:
            data_dir = os.path.dirname(self.buyback_log_path)
            if not os.path.exists(data_dir):
                os.makedirs(data_dir, exist_ok=True)
            if not os.path.exists(self.buyback_log_path):
                with open(self.buyback_log_path, 'w') as f:
                    json.dump({"buybacks": [], "total_kerne_bought": 0, "total_spent_usd": 0}, f)
        except Exception as e:
            logger.warning(f"Could not create buyback log: {e}")

    def _log_buyback(self, token: str, amount_in: float, kerne_out: float, tx_hash: str):
        """Log a buyback execution to the persistent log file."""
        try:
            with open(self.buyback_log_path, 'r') as f:
                log = json.load(f)
            
            log["buybacks"].append({
                "timestamp": datetime.utcnow().isoformat(),
                "token": token,
                "amount_in": amount_in,
                "kerne_out": kerne_out,
                "tx_hash": tx_hash
            })
            log["total_kerne_bought"] += kerne_out
            
            # Estimate USD value (rough)
            if token.lower() == "weth":
                log["total_spent_usd"] += amount_in * 3300  # Rough ETH price
            else:
                log["total_spent_usd"] += amount_in
            
            with open(self.buyback_log_path, 'w') as f:
                json.dump(log, f, indent=2)
                
            logger.info(f"Buyback logged: {amount_in} {token} → {kerne_out} KERNE")
        except Exception as e:
            logger.error(f"Error logging buyback: {e}")

    def check_and_execute_buyback(self, dry_run: bool = False) -> dict:
        """
        Checks treasury balances and executes buybacks if thresholds are met.
        This is the core Buyback Flywheel mechanism.
        
        Returns:
            dict: Summary of buyback activity
        """
        result = {
            "checked": True,
            "buybacks_executed": 0,
            "total_kerne_bought": 0,
            "skipped_reason": None
        }
        
        try:
            # Check cooldown
            if self.last_buyback_time:
                time_since_last = datetime.utcnow() - self.last_buyback_time
                if time_since_last < timedelta(hours=self.BUYBACK_COOLDOWN_HOURS):
                    remaining = timedelta(hours=self.BUYBACK_COOLDOWN_HOURS) - time_since_last
                    result["skipped_reason"] = f"Cooldown active ({remaining.total_seconds()/3600:.1f}h remaining)"
                    logger.info(f"Buyback skipped: {result['skipped_reason']}")
                    return result
            
            # Check WETH balance in Treasury
            weth_balance = self.chain.get_treasury_balance(self.WETH_ADDRESS)
            logger.info(f"Treasury WETH balance: {weth_balance:.6f}")
            
            # Check USDC balance in Treasury
            usdc_balance = self.chain.get_treasury_balance(self.USDC_ADDRESS)
            logger.info(f"Treasury USDC balance: {usdc_balance:.2f}")
            
            # Execute WETH buyback if threshold met
            if weth_balance >= self.MIN_BUYBACK_THRESHOLD_WETH:
                if not self.chain.is_buyback_token_approved(self.WETH_ADDRESS):
                    logger.warning("WETH not approved for buyback - approve it first")
                else:
                    logger.info(f"🔥 Executing WETH buyback: {weth_balance:.6f} WETH")
                    
                    if not dry_run:
                        # Preview first
                        preview = self.chain.preview_buyback(self.WETH_ADDRESS, weth_balance)
                        if preview["expected"] > 0:
                            tx_hash = self.chain.execute_buyback(self.WETH_ADDRESS, weth_balance)
                            if tx_hash:
                                self._log_buyback("WETH", weth_balance, preview["expected"], tx_hash)
                                result["buybacks_executed"] += 1
                                result["total_kerne_bought"] += preview["expected"]
                        else:
                            logger.warning("WETH buyback preview returned 0 - check pool liquidity")
                    else:
                        logger.info(f"[DRY RUN] Would buyback {weth_balance:.6f} WETH")
            
            # Execute USDC buyback if threshold met
            if usdc_balance >= self.MIN_BUYBACK_THRESHOLD_USDC:
                if not self.chain.is_buyback_token_approved(self.USDC_ADDRESS):
                    logger.warning("USDC not approved for buyback - approve it first")
                else:
                    logger.info(f"🔥 Executing USDC buyback: {usdc_balance:.2f} USDC")
                    
                    if not dry_run:
                        # Preview first
                        preview = self.chain.preview_buyback(self.USDC_ADDRESS, usdc_balance)
                        if preview["expected"] > 0:
                            tx_hash = self.chain.execute_buyback(self.USDC_ADDRESS, usdc_balance)
                            if tx_hash:
                                self._log_buyback("USDC", usdc_balance, preview["expected"], tx_hash)
                                result["buybacks_executed"] += 1
                                result["total_kerne_bought"] += preview["expected"]
                        else:
                            logger.warning("USDC buyback preview returned 0 - check pool liquidity")
                    else:
                        logger.info(f"[DRY RUN] Would buyback {usdc_balance:.2f} USDC")
            
            # Update cooldown if we executed any buybacks
            if result["buybacks_executed"] > 0:
                self.last_buyback_time = datetime.utcnow()
                logger.success(f"🔥 Buyback Flywheel: Executed {result['buybacks_executed']} buybacks, acquired ~{result['total_kerne_bought']:.4f} KERNE")
            else:
                if weth_balance < self.MIN_BUYBACK_THRESHOLD_WETH and usdc_balance < self.MIN_BUYBACK_THRESHOLD_USDC:
                    result["skipped_reason"] = f"Balances below threshold (WETH: {weth_balance:.6f}/{self.MIN_BUYBACK_THRESHOLD_WETH}, USDC: {usdc_balance:.2f}/{self.MIN_BUYBACK_THRESHOLD_USDC})"
                    logger.info(f"Buyback skipped: {result['skipped_reason']}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in buyback check: {e}")
            result["skipped_reason"] = f"Error: {str(e)}"
            return result

    def get_buyback_stats(self) -> dict:
        """
        Returns comprehensive buyback statistics.
        """
        try:
            # On-chain stats from Treasury contract
            chain_stats = self.chain.get_buyback_stats()
            
            # Local log stats
            local_stats = {"buybacks": [], "total_kerne_bought": 0, "total_spent_usd": 0}
            if os.path.exists(self.buyback_log_path):
                with open(self.buyback_log_path, 'r') as f:
                    local_stats = json.load(f)
            
            return {
                "on_chain": chain_stats,
                "local_log": {
                    "total_buybacks": len(local_stats.get("buybacks", [])),
                    "total_kerne_bought": local_stats.get("total_kerne_bought", 0),
                    "total_spent_usd": local_stats.get("total_spent_usd", 0),
                    "recent_buybacks": local_stats.get("buybacks", [])[-5:]  # Last 5
                },
                "treasury_balances": {
                    "weth": self.chain.get_treasury_balance(self.WETH_ADDRESS),
                    "usdc": self.chain.get_treasury_balance(self.USDC_ADDRESS)
                }
            }
        except Exception as e:
            logger.error(f"Error getting buyback stats: {e}")
            return {"error": str(e)}

    def run_buyback_cycle(self, dry_run: bool = False):
        """
        Dedicated buyback cycle that can be run independently or alongside hedging.
        """
        logger.info("=" * 60)
        logger.info("🔥 KERNE BUYBACK FLYWHEEL CYCLE")
        logger.info("=" * 60)
        
        # Get pre-buyback stats
        stats = self.get_buyback_stats()
        logger.info(f"Pre-buyback stats: {stats['on_chain']['total_kerne_bought']:.4f} KERNE bought lifetime")
        
        # Execute buybacks
        result = self.check_and_execute_buyback(dry_run=dry_run)
        
        if result["buybacks_executed"] > 0:
            # Get post-buyback stats
            post_stats = self.get_buyback_stats()
            logger.success(f"Post-buyback stats: {post_stats['on_chain']['total_kerne_bought']:.4f} KERNE bought lifetime")
        
        return result

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
