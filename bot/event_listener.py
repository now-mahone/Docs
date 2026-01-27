import asyncio
import os
from web3 import AsyncWeb3, WebsocketProvider
from web3.middleware import async_geth_poa_middleware
from loguru import logger
from dotenv import load_dotenv

load_dotenv()

class VaultEventListener:
    """
    Asynchronous event listener for the KerneVault contract.
    Monitors on-chain activity to trigger immediate rebalancing.
    """
    def __init__(self, vault_address, abi, queue: asyncio.Queue, wss_url: str = None):
        self.vault_address = vault_address
        self.abi = abi
        self.queue = queue
        self.wss_url = wss_url or os.getenv("WSS_URL")
        
        if not self.wss_url:
            # Fallback to a derived WSS URL if possible, though usually provided by user
            rpc_url = os.getenv("RPC_URL", "")
            if "https://" in rpc_url:
                self.wss_url = rpc_url.replace("https://", "wss://")
                logger.warning(f"WSS_URL not found, attempting fallback: {self.wss_url}")
        
        self.w3 = None
        self.contract = None

    async def _connect(self):
        """Robust connection logic with retries."""
        while True:
            try:
                if not self.wss_url:
                    raise ValueError("WSS_URL is missing. Cannot start event listener.")
                
                self.w3 = AsyncWeb3(WebsocketProvider(self.wss_url))
                self.w3.middleware_onion.inject(async_geth_poa_middleware, layer=0)
                
                if await self.w3.is_connected():
                    logger.info(f"✅ VaultEventListener connected to {self.wss_url}")
                    self.contract = self.w3.eth.contract(address=self.vault_address, abi=self.abi)
                    return
            except Exception as e:
                logger.error(f"❌ WebSocket connection failed: {e}. Retrying in 5s...")
                await asyncio.sleep(5)

    async def listen(self):
        """
        Subscribes to logs for the vault contract and pushes events to the queue.
        """
        while True:
            await self._connect()
            try:
                # We use polling for new entries as it's more stable across various RPC providers
                # than raw subscriptions in some web3.py versions.
                deposit_filter = await self.contract.events.Deposit.create_filter(fromBlock='latest')
                withdraw_filter = await self.contract.events.Withdraw.create_filter(fromBlock='latest')
                
                logger.info(f"📡 Listening for Deposit/Withdraw events on {self.vault_address}")
                
                while True:
                    try:
                        # Check Deposit events
                        for event in await deposit_filter.get_new_entries():
                            logger.info(f"🔔 Event Detected: Deposit | {event['args']['assets']} assets")
                            await self.queue.put(("Deposit", event))
                        
                        # Check Withdraw events
                        for event in await withdraw_filter.get_new_entries():
                            logger.info(f"🔔 Event Detected: Withdraw | {event['args']['assets']} assets")
                            await self.queue.put(("Withdraw", event))
                            
                        await asyncio.sleep(2) # Prevent CPU pegging
                    except Exception as e:
                        if "filter not found" in str(e).lower():
                            logger.warning("Filter expired, recreating...")
                            break # Inner loop break to recreate filters
                        logger.error(f"Error polling events: {e}")
                        await asyncio.sleep(5)
                        
            except Exception as e:
                logger.error(f"Listener error: {e}. Reconnecting...")
                await asyncio.sleep(5)
