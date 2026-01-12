import time
import traceback
import argparse
from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from engine import HedgingEngine
from liquidity_manager import LiquidityManager
from alerts import send_discord_alert
from sentinel.risk_engine import RiskEngine

# Created: 2025-12-28

DRY_RUN = True

def main():
    parser = argparse.ArgumentParser(description="Kerne Bot")
    parser.add_argument("--seed-only", action="store_true", help="Execute initial seed TVL update and exit")
    args = parser.parse_args()

    logger.info("🚀 Kerne Bot Starting Up...")
    if not DRY_RUN:
        send_discord_alert("🚀 Kerne Bot Starting Up...", level="INFO")

    try:
        # Initialize Managers
        exchange = ExchangeManager()
        chain = ChainManager()
        
        # Initialize Engine
        engine = HedgingEngine(exchange, chain)
        liquidity = LiquidityManager()
        risk_engine = RiskEngine(w3=chain.w3, private_key=chain.private_key)
        
        if args.seed_only:
            logger.info("GENESIS MODE: Executing seed TVL update...")
            # We call run_cycle with seed_only=True to bypass CEX API
            engine.run_cycle(dry_run=False, seed_only=True)
            logger.success("Genesis seeding complete. Exiting.")
            return

        if DRY_RUN:
            logger.warning("!!! DRY RUN MODE ENABLED !!!")

        logger.success("Initialization complete. Entering main loop.")
        
    except Exception as e:
        logger.critical(f"Failed to initialize bot: {e}")
        send_discord_alert(f"CRITICAL: Bot failed to initialize: {e}", level="CRITICAL")
        return

    while True:
        try:
            # 1. Risk Analysis & Sentinel Defense
            # Fetch latest vault data for risk analysis
            vault_tvl = chain.get_vault_tvl()
            short_pos, _ = exchange.get_short_position('ETH/USDT:USDT')
            collateral_usdt = exchange.get_collateral_balance('USDT')
            
            vault_data = {
                "address": chain.vault_address,
                "onchain_collateral": vault_tvl,
                "cex_short_position": short_pos,
                "available_margin_usd": collateral_usdt,
                "liq_onchain": 0.5, # Placeholder: 50% distance to liquidation
                "liq_cex": 0.3      # Placeholder: 30% distance to liquidation
            }
            risk_engine.analyze_vault(vault_data)
            
            # Check Health Factor for auto-deleverage
            if chain.minter:
                try:
                    hf = chain.minter.functions.getHealthFactor(chain.vault_address).call() / 1e18
                    risk_engine.auto_deleverage(chain.vault_address, hf)
                except Exception as e:
                    logger.error(f"Failed to check health factor: {e}")

            # 2. Execute one hedging and reporting cycle
            engine.run_cycle(dry_run=DRY_RUN)
            
            # 3. Execute liquidity management cycle
            if not args.seed_only:
                liquidity.check_peg()
                liquidity.manage_lp_positions()
                liquidity.rebalance_pools()

            if DRY_RUN:
                logger.info("Dry run cycle complete. Exiting.")
                break
            
            # Sleep for 5 minutes
            logger.info("Cycle complete. Sleeping for 300 seconds...")
            time.sleep(300)
            
        except Exception as e:
            error_msg = f"CRITICAL ERROR in main loop: {e}\n{traceback.format_exc()}"
            logger.error(error_msg)
            send_discord_alert(f"CRITICAL ERROR: {e}", level="CRITICAL")
            
            # Wait 1 minute before retrying after an error
            logger.info("Waiting 60 seconds before retry...")
            time.sleep(60)

if __name__ == "__main__":
    main()
