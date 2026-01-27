import asyncio
import json
import os
import math
from datetime import datetime, timedelta
from loguru import logger
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
from credits_manager import CreditsManager

class HedgingEngine:
    """
    Asynchronous Hedging Engine V2.
    Supports event-driven rebalancing and persistent buyback flywheel.
    """
    def __init__(self, exchange: ExchangeManager, chain: ChainManager, credits: CreditsManager = None):
        self.exchange = exchange
        self.chain = chain
        self.credits = credits or CreditsManager()
        
        # Hysteresis threshold
        self.THRESHOLD_ETH = 0.05 
        self.SYMBOL = 'ETH'
        
        # Risk Parameters
        self.MIN_LEVERAGE = 1.5
        self.MAX_LEVERAGE = 12.0
        self.RISK_AVERSION_FACTOR = 2.5 
        self.SETTLEMENT_THRESHOLD = 0.01 
        
        # Buyback Configuration
        self.MIN_BUYBACK_THRESHOLD_WETH = float(os.getenv("BUYBACK_MIN_WETH", "0.01"))
        self.MIN_BUYBACK_THRESHOLD_USDC = float(os.getenv("BUYBACK_MIN_USDC", "25"))
        self.BUYBACK_COOLDOWN_HOURS = int(os.getenv("BUYBACK_COOLDOWN_HOURS", "24"))
        self.last_buyback_time = None
        
        self.WETH_ADDRESS = os.getenv("WETH_ADDRESS", "0x4200000000000000000000000000000000000006")
        self.USDC_ADDRESS = os.getenv("USDC_ADDRESS", "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
        
        self.buyback_log_path = os.path.join(os.path.dirname(__file__), "data", "buyback_log.json")
        self._ensure_buyback_log()
        
        logger.info(f"🚀 HedgingEngine V2 (Async) initialized. Symbol: {self.SYMBOL}")

    async def run_rebalance_loop(self, queue: asyncio.Queue):
        """
        Main event-driven loop that waits for vault events and triggers rebalancing.
        """
        logger.info("🔄 Starting asynchronous rebalance loop...")
        while True:
            try:
                # Wait for an event from the queue
                event_type, event_data = await queue.get()
                logger.info(f"📩 Processing event: {event_type} from {event_data['address']}")
                
                # Trigger an immediate rebalance cycle
                await self.run_cycle()
                
                queue.task_done()
            except Exception as e:
                logger.error(f"Error in rebalance loop: {e}")
                await asyncio.sleep(1)

    async def run_cycle(self, dry_run: bool = False, **kwargs):
        """
        Executes one rebalancing, solvency verification, and reporting cycle.
        Now asynchronous to support event-driven architecture.
        """
        seed_only = kwargs.get('seed_only', False)
        try:
            logger.info(f"Executing cycle... {'(SEED ONLY)' if seed_only else ''}")
            
            # Use to_thread for blocking Web3 calls if ChainManager is not async
            if not dry_run and await asyncio.to_thread(self.chain.vault.functions.paused().call):
                logger.warning("VAULT IS PAUSED. Rebalancing suspended.")
                return

            # 1. Fetch Data (offloading to threads for now as ChainManager is sync)
            multi_chain_tvl = await asyncio.to_thread(self.chain.get_multi_chain_tvl)
            total_vault_tvl = sum(multi_chain_tvl.values())
            on_chain_assets = await asyncio.to_thread(self.chain.get_on_chain_assets)
            
            if dry_run:
                market_price = 2500.0
                agg_pos = {"size": 0.0, "upnl": 0.0}
                total_cex_equity_usd = 100000.0
            else:
                market_price = await asyncio.to_thread(self.exchange.get_market_price, self.SYMBOL)
                agg_pos = await asyncio.to_thread(self.exchange.get_aggregate_position, self.SYMBOL)
                total_cex_equity_usd = await asyncio.to_thread(self.exchange.get_total_equity)

            short_pos = agg_pos["size"]
            
            # 2. Solvency Analysis
            offchain_value_eth = total_cex_equity_usd / market_price if market_price > 0 else 0
            total_protocol_assets = on_chain_assets + offchain_value_eth
            
            solvency_ratio = (total_protocol_assets / total_vault_tvl) if total_vault_tvl > 0 else 1.0
            logger.info(f"Solvency: {solvency_ratio*100:.2f}% | Target: 100%+")

            # 3. Target Hedge Calculation (100% of TVL)
            target_short = total_vault_tvl 
            delta = target_short - short_pos
            logger.info(f"Hedge Delta: {delta:.4f} ETH")

            # 4. Rebalance
            if not dry_run and abs(delta) > self.THRESHOLD_ETH:
                if delta > 0:
                    await asyncio.to_thread(self.exchange.execute_short, self.SYMBOL, delta)
                else:
                    await asyncio.to_thread(self.exchange.execute_buy, self.SYMBOL, abs(delta))
            
            # 5. Reporting
            if not dry_run:
                await asyncio.to_thread(self.chain.update_offchain_value, offchain_value_eth)
                
                # Buyback Flywheel integration (Non-blocking)
                asyncio.create_task(self.run_buyback_cycle(dry_run=dry_run))

            logger.success("Cycle completed successfully.")
            
        except Exception as e:
            logger.error(f"Error in hedging cycle: {e}")

    async def run_buyback_cycle(self, dry_run: bool = False):
        """Asynchronous wrapper for the buyback flywheel."""
        try:
            # Check cooldown
            if self.last_buyback_time:
                time_since_last = datetime.utcnow() - self.last_buyback_time
                if time_since_last < timedelta(hours=self.BUYBACK_COOLDOWN_HOURS):
                    return

            await asyncio.to_thread(self.check_and_execute_buyback, dry_run=dry_run)
        except Exception as e:
            logger.error(f"Buyback cycle error: {e}")

    def _ensure_buyback_log(self):
        data_dir = os.path.dirname(self.buyback_log_path)
        if not os.path.exists(data_dir):
            os.makedirs(data_dir, exist_ok=True)
        if not os.path.exists(self.buyback_log_path):
            with open(self.buyback_log_path, 'w') as f:
                json.dump({"buybacks": [], "total_kerne_bought": 0, "total_spent_usd": 0}, f)

    def check_and_execute_buyback(self, dry_run: bool = False) -> dict:
        # Existing logic preserved, called via to_thread
        try:
            weth_balance = self.chain.get_treasury_balance(self.WETH_ADDRESS)
            usdc_balance = self.chain.get_treasury_balance(self.USDC_ADDRESS)
            
            executed = False
            if weth_balance >= self.MIN_BUYBACK_THRESHOLD_WETH:
                if not dry_run:
                    tx_hash = self.chain.execute_buyback(self.WETH_ADDRESS, weth_balance)
                    if tx_hash: executed = True
            
            if usdc_balance >= self.MIN_BUYBACK_THRESHOLD_USDC:
                if not dry_run:
                    tx_hash = self.chain.execute_buyback(self.USDC_ADDRESS, usdc_balance)
                    if tx_hash: executed = True
            
            if executed:
                self.last_buyback_time = datetime.utcnow()
        except Exception as e:
            logger.error(f"Buyback execution error: {e}")

    def _trigger_panic(self, reason: str):
        logger.critical(f"PANIC: {reason}")
        agg_pos = self.exchange.get_aggregate_position(self.SYMBOL)
        if agg_pos["size"] > 0:
            self.exchange.execute_buy(self.SYMBOL, agg_pos["size"])
