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
from por_attestation import PoRAttestationBot
from reporting_service import ReportingService

# Created: 2025-12-28
# Updated: 2026-01-16 (Institutional Solvency Reporting)

DRY_RUN = False

def main():
    parser = argparse.ArgumentParser(description="Kerne Bot")
    parser.add_argument("--seed-only", action="store_true", help="Execute initial seed TVL update and exit")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()

    global DRY_RUN
    if args.dry_run:
        DRY_RUN = True

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
        
        # Initialize Solvency Reporting
        por_bot = PoRAttestationBot()
        reporting = ReportingService(chain)
        
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

    last_solvency_pulse = 0

    while True:
        try:
            for v_config in chain.vaults:
                vault_address = v_config["address"]
                chain_name = v_config["chain"]
                
                logger.info(f"--- Processing Vault: {vault_address} ({chain_name}) ---")
                chain.set_active_vault(vault_address, chain_name)
                
                # 1. Risk Analysis & Sentinel Defense
                vault_tvl = chain.get_vault_assets(vault_address, chain_name)
                
                # We assume for now that each vault hedges ETH
                symbol = "ETH"
                agg_pos = exchange.get_aggregate_position(symbol)
                short_pos = agg_pos["size"]
                collateral_usdt = exchange.get_total_equity()
                liq_price_cex = exchange.get_liquidation_price(symbol)
                current_price = exchange.get_market_price(symbol)

                hf = 2.0 # Default
                if chain.minter and chain_name == "Base":
                    try:
                        hf = chain.minter.functions.getHealthFactor(vault_address).call() / 1e18
                    except Exception as e:
                        logger.error(f"Failed to check health factor for {vault_address}: {e}")
                
                vault_data = {
                    "address": vault_address,
                    "onchain_collateral": vault_tvl,
                    "cex_short_position": short_pos,
                    "available_margin_usd": collateral_usdt,
                    "current_price": current_price,
                    "liq_price_cex": liq_price_cex,
                    "health_factor": hf,
                    "symbol": f"{symbol}/USDT"
                }
                
                import asyncio
                try:
                    asyncio.run(risk_engine.analyze_vault(vault_data))
                except Exception as e:
                    logger.error(f"Risk analysis failed for {vault_address}: {e}")

                # Auto-deleverage check
                if hf < 1.1: # Critical threshold
                    risk_engine.auto_deleverage(vault_address, hf)

                # 2. Execute one hedging and reporting cycle
                # Note: engine.run_cycle currently uses global vault_address from ChainManager
                # We might need to update HedgingEngine to support per-vault cycles
                engine.run_cycle(dry_run=DRY_RUN)
                
                # 3. Execute liquidity management cycle (Base only for now)
                if not args.seed_only and chain_name == "Base":
                    liquidity.check_peg()
                    liquidity.manage_lp_positions()
                    liquidity.rebalance_pools()

                # 4. Institutional Solvency Reporting (Every 1 hour)
                if time.time() - last_solvency_pulse > 3600:
                    logger.info(f"Running Institutional Solvency Pulse for {vault_address}...")
                    por_bot.run_cycle()
                    reporting.generate_solvency_certificate(vault_address)
                    last_solvency_pulse = time.time()

            if DRY_RUN:
                logger.info("Dry run cycle complete. Exiting.")
                break
            
            # Sleep for 5 minutes
            logger.info("All vaults processed. Sleeping for 300 seconds...")
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
