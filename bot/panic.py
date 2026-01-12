import os
import json
import asyncio
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
from alerts import send_discord_alert

# Created: 2025-12-28
# Updated: 2026-01-12 - Refined with asynchronous execution and comprehensive unwind logic

async def panic_pause():
    """
    Standalone script to immediately pause the KerneVault contract.
    """
    load_dotenv()
    
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    vault_address = os.getenv("VAULT_ADDRESS")
    
    if not all([rpc_url, private_key, vault_address]):
        logger.error("Missing environment variables for Panic script.")
        return False

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)
        
        # Minimal ABI for pausing
        pause_abi = [{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"}]
        vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=pause_abi)
        
        logger.warning(f"🚨 PANIC: Attempting to pause vault at {vault_address}...")
        
        tx = vault.functions.pause().build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 100000,
            'gasPrice': w3.eth.gas_price,
            'chainId': w3.eth.chain_id
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Panic transaction sent: {tx_hash.hex()}. Waiting for confirmation...")
        
        # Wait for confirmation asynchronously
        loop = asyncio.get_event_loop()
        receipt = await loop.run_in_executor(None, w3.eth.wait_for_transaction_receipt, tx_hash)
        
        if receipt.status == 1:
            logger.success("✅ VAULT PAUSED SUCCESSFULLY.")
            send_discord_alert("🚨 **PANIC BUTTON PRESSED. VAULT PAUSED.**", level="CRITICAL")
            return True
        else:
            logger.error("❌ PANIC TRANSACTION FAILED.")
            send_discord_alert("❌ **PANIC BUTTON FAILED TO PAUSE VAULT.**", level="CRITICAL")
            return False
            
    except Exception as e:
        logger.critical(f"Panic script failed: {e}")
        send_discord_alert(f"❌ **PANIC SCRIPT CRASHED: {e}**", level="CRITICAL")
        return False

async def emergency_unwind():
    """
    Emergency Unwind: Pauses the vault and closes all CEX short positions concurrently.
    """
    load_dotenv()
    
    # 1. Pause the Vault
    pause_task = asyncio.create_task(panic_pause())
    
    # 2. Close CEX Positions
    from exchange_manager import ExchangeManager
    
    exchanges = ["binance", "bybit", "okx"]
    symbol = os.getenv("HEDGE_SYMBOL", "ETH/USDT:USDT")
    
    logger.warning(f"🚨 EMERGENCY UNWIND: Closing all short positions for {symbol}...")

    async def close_exchange_position(ex_id):
        try:
            manager = ExchangeManager(ex_id)
            contracts, pnl = manager.get_short_position(symbol)
            
            if contracts > 0:
                logger.info(f"Closing {contracts} contracts on {ex_id}...")
                success = manager.execute_buy(symbol, contracts)
                if success:
                    logger.success(f"✅ Closed position on {ex_id}.")
                    return True
            else:
                logger.info(f"No open position on {ex_id}.")
                return True
        except Exception as e:
            logger.error(f"Error during unwind on {ex_id}: {e}")
            return False

    unwind_tasks = [close_exchange_position(ex_id) for ex_id in exchanges]
    
    # Run all tasks concurrently
    results = await asyncio.gather(pause_task, *unwind_tasks)
    
    if all(results):
        send_discord_alert("🚨 **EMERGENCY UNWIND COMPLETE. VAULT PAUSED & POSITIONS CLOSED.**", level="CRITICAL")
    else:
        send_discord_alert("⚠️ **EMERGENCY UNWIND PARTIALLY FAILED. CHECK LOGS.**", level="CRITICAL")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--unwind":
        asyncio.run(emergency_unwind())
    else:
        asyncio.run(panic_pause())
