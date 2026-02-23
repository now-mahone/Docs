import asyncio
import argparse
import time
from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from engine import HedgingEngine
from event_listener import VaultEventListener
from alerts import send_discord_alert
from sentinel.risk_engine import RiskEngine
from api_connector import APIRefreshLoop

# Created: 2025-12-28
# Updated: 2026-02-06 (Integrated APIRefreshLoop for live data aggregation)

async def periodic_tasks(engine: HedgingEngine, chain: ChainManager, risk_engine: RiskEngine, dry_run: bool):
    """
    Handles tasks that still require periodic polling (Risk, Solvency Reporting, Buybacks).
    """
    last_solvency_report = 0
    while True:
        try:
            for v_config in chain.vaults:
                vault_address = v_config["address"]
                chain_name = v_config["chain"]
                
                # Risk Analysis
                vault_tvl = await asyncio.to_thread(chain.get_vault_assets, vault_address, chain_name)
                current_price = await asyncio.to_thread(engine.exchange.get_market_price, engine.SYMBOL)
                
                vault_data = {
                    "address": vault_address,
                    "onchain_collateral": vault_tvl,
                    "current_price": current_price,
                    "symbol": f"{engine.SYMBOL}/USDT"
                }
                await risk_engine.analyze_vault(vault_data)
                
            # Periodic Solvency Update (every 30 mins)
            if time.time() - last_solvency_report > 1800:
                await engine.run_cycle(dry_run=dry_run)
                last_solvency_report = time.time()
                
            await asyncio.sleep(300) # Poll every 5 minutes
        except Exception as e:
            logger.error(f"Error in periodic tasks: {e}")
            await asyncio.sleep(60)

async def main():
    parser = argparse.ArgumentParser(description="Kerne Bot V2 (Async)")
    parser.add_argument("--dry-run", action="store_true", help="Run in dry-run mode")
    args = parser.parse_args()

    logger.info("🚀 Kerne Bot V2 starting up (Event-Driven)...")
    
    try:
        # Initialize Managers
        exchange = ExchangeManager()
        chain = ChainManager()
        
        # Initialize Engine & Risk
        engine = HedgingEngine(exchange, chain)
        risk_engine = RiskEngine(w3=chain.w3, private_key=chain.private_key)
        
        # Event Queue for Vault Events
        event_queue = asyncio.Queue()
        
        # Initialize Event Listener (Base Vault)
        # We focus on the primary vault for event-driven rebalancing
        listener = VaultEventListener(
            vault_address=chain.vault_address,
            abi=chain.abi,
            queue=event_queue
        )
        
        # Start API refresh loop (background thread — aggregates free API data + serves stats on :8787)
        api_loop = APIRefreshLoop(refresh_interval=30.0, serve_stats=True, stats_port=8787)
        api_loop.start()
        logger.info("📊 API connector started — stats available at http://localhost:8787/stats")

        if not args.dry_run:
            send_discord_alert("🚀 Kerne Bot V2 (Async) Started", level="INFO")

        # Run all components concurrently
        logger.success("Initialization complete. Launching async tasks.")
        await asyncio.gather(
            listener.listen(),
            engine.run_rebalance_loop(event_queue),
            periodic_tasks(engine, chain, risk_engine, args.dry_run)
        )

    except Exception as e:
        logger.critical(f"Failed to start bot: {e}")
        send_discord_alert(f"CRITICAL: Bot failed to start: {e}", level="CRITICAL")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user.")
