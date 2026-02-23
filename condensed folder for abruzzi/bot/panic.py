import os
import json
import asyncio
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
from alerts import send_discord_alert

# Created: 2025-12-28
# Updated: 2026-01-12 - Institutional Deep Hardening: Multi-stage deleveraging and concurrent exchange unwinding

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
        pause_abi = [{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"}]
        vault = w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=pause_abi)
        
        logger.warning(f"🚨 PANIC: Attempting to pause vault at {vault_address}...")
        
        tx = vault.functions.pause().build_transaction({
            'from': account.address,
            'nonce': w3.eth.get_transaction_count(account.address),
            'gas': 150000,
            'gasPrice': int(w3.eth.gas_price * 1.5), # 50% premium for emergency
            'chainId': w3.eth.chain_id
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Panic transaction sent: {tx_hash.hex()}")
        return True
    except Exception as e:
        logger.critical(f"Panic script failed: {e}")
        return False

async def emergency_unwind():
    """
    Institutional Emergency Unwind: Multi-stage deleveraging.
    Stage 1: Pause Vault (On-chain)
    Stage 2: Cancel all open orders (CEX)
    Stage 3: Close all positions (CEX)
    Stage 4: Withdraw to cold storage (Optional)
    """
    load_dotenv()
    logger.warning("🚨 INITIATING INSTITUTIONAL EMERGENCY UNWIND...")
    
    # Stage 1: Pause Vault
    pause_success = await panic_pause()
    
    # Stage 2 & 3: CEX Unwinding
    from exchange_manager import ExchangeManager
    exchanges = ["binance", "bybit", "okx"]
    symbol = os.getenv("HEDGE_SYMBOL", "ETH/USDT:USDT")

    async def unwind_venue(ex_id):
        try:
            manager = ExchangeManager(ex_id)
            logger.info(f"[{ex_id}] Stage 2: Cancelling open orders...")
            manager.exchange.cancel_all_orders(symbol)
            
            logger.info(f"[{ex_id}] Stage 3: Closing positions...")
            contracts, pnl = manager.get_short_position(symbol)
            if contracts > 0:
                success = manager.execute_buy(symbol, contracts)
                if success: logger.success(f"[{ex_id}] Position closed.")
            return True
        except Exception as e:
            logger.error(f"[{ex_id}] Unwind failed: {e}")
            return False

    unwind_tasks = [unwind_venue(ex_id) for ex_id in exchanges]
    results = await asyncio.gather(*unwind_tasks)
    
    if all(results) and pause_success:
        send_discord_alert("🚨 **INSTITUTIONAL UNWIND COMPLETE. ALL SYSTEMS SECURED.**", level="CRITICAL")
    else:
        send_discord_alert("⚠️ **UNWIND PARTIALLY FAILED. MANUAL INTERVENTION REQUIRED.**", level="CRITICAL")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--unwind":
        asyncio.run(emergency_unwind())
    else:
        asyncio.run(panic_pause())
