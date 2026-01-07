import time
import traceback
import argparse
from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from engine import HedgingEngine
from liquidity_manager import LiquidityManager
from alerts import send_discord_alert

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
            # 1. Execute one hedging and reporting cycle
            engine.run_cycle(dry_run=DRY_RUN)
            
            # 2. Execute liquidity management cycle
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
