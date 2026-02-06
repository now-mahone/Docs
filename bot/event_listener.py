import asyncio
import os
from web3 import Web3
from loguru import logger
from dotenv import load_dotenv

# Created: 2026-01-23
# Updated: 2026-02-05 (Switched to Sync Web3 + to_thread for stability)

load_dotenv()

class VaultEventListener:
    """
    Event listener for the KerneVault contract using sync Web3 in threads.
    Monitors on-chain activity to trigger immediate rebalancing.
    """
    def __init__(self, vault_address, abi, queue: asyncio.Queue, rpc_url: str = None):
        self.vault_address = vault_address
        self.abi = abi
        self.queue = queue
        self.rpc_url = rpc_url or os.getenv("RPC_URL")
        
        # Handle comma-separated RPCs
        if self.rpc_url and "," in self.rpc_url:
            self.rpc_url = self.rpc_url.split(",")[0]
            
        self.w3 = None
        self.last_block = None

    def _connect_sync(self):
        """Sync connection logic."""
        try:
            self.w3 = Web3(Web3.HTTPProvider(self.rpc_url))
            if self.w3.is_connected():
                logger.info(f"✅ VaultEventListener connected to {self.rpc_url}")
                self.last_block = self.w3.eth.block_number
                return True
        except Exception as e:
            logger.error(f"❌ Connection failed: {e}")
        return False

    async def listen(self):
        """
        Subscribes to logs for the vault contract and pushes events to the queue.
        Uses to_thread to avoid blocking the event loop.
        """
        while True:
            connected = await asyncio.to_thread(self._connect_sync)
            if not connected:
                await asyncio.sleep(5)
                continue
                
            try:
                logger.info(f"📡 Listening for events on {self.vault_address} via polling")
                
                while True:
                    try:
                        current_block = await asyncio.to_thread(lambda: self.w3.eth.block_number)
                        
                        if self.last_block and current_block > self.last_block:
                            # Poll for Deposit events
                            deposit_logs = await asyncio.to_thread(self.w3.eth.get_logs, {
                                'fromBlock': self.last_block + 1,
                                'toBlock': current_block,
                                'address': self.vault_address,
                                'topics': ['0xddf252ad1be2c89b69c2b068fc378daa952ba7f163c4a11628f55a4df523b3ef'] # Deposit topic
                            })
                            for log in deposit_logs:
                                logger.info(f"🔔 Event Detected: Deposit")
                                await self.queue.put(("Deposit", log))

                            # Poll for Withdraw events
                            withdraw_logs = await asyncio.to_thread(self.w3.eth.get_logs, {
                                'fromBlock': self.last_block + 1,
                                'toBlock': current_block,
                                'address': self.vault_address,
                                'topics': ['0xfbe9912c4310c28110314c0f7b2291e5b200ac8c7c3b925843392a3516001815'] # Withdraw topic
                            })
                            for log in withdraw_logs:
                                logger.info(f"🔔 Event Detected: Withdraw")
                                await self.queue.put(("Withdraw", log))

                            self.last_block = current_block
                            
                        await asyncio.sleep(10) # Poll every 10 seconds
                    except Exception as e:
                        logger.error(f"Error polling events: {e}")
                        await asyncio.sleep(5)
                        
            except Exception as e:
                logger.error(f"Listener error: {e}. Reconnecting...")
                await asyncio.sleep(5)