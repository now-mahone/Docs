import os
import time
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
from bot.alerts import send_discord_alert

# Created: 2025-12-28

def monitor_canary():
    """
    Monitors a 'Honey Pot' address for any balance changes.
    If a change is detected, it signals a potential server compromise.
    """
    load_dotenv()
    
    rpc_url = os.getenv("RPC_URL")
    canary_address = os.getenv("CANARY_ADDRESS")
    
    if not rpc_url or not canary_address:
        logger.error("Missing RPC_URL or CANARY_ADDRESS for Canary monitor.")
        return

    w3 = Web3(Web3.HTTPProvider(rpc_url))
    
    if not w3.is_connected():
        logger.error("Canary monitor failed to connect to RPC.")
        return

    logger.info(f"Canary monitor started. Watching address: {canary_address}")
    
    try:
        # Initial balance
        last_balance = w3.eth.get_balance(canary_address)
        
        while True:
            current_balance = w3.eth.get_balance(canary_address)
            
            if current_balance != last_balance:
                msg = f"TRIPWIRE ACTIVATED: Canary address {canary_address} balance changed! Server compromise suspected. PAUSE THE VAULT NOW."
                logger.critical(msg)
                send_discord_alert(msg, level="CRITICAL")
                last_balance = current_balance
            
            time.sleep(30) # Check every 30 seconds
            
    except Exception as e:
        logger.error(f"Canary monitor encountered an error: {e}")
        send_discord_alert(f"Canary monitor crashed: {e}", level="WARNING")

if __name__ == "__main__":
    monitor_canary()
