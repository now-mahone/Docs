import os
import json
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
from alerts import send_discord_alert

# Created: 2025-12-28

def panic_pause():
    """
    Standalone script to immediately pause the KerneVault contract.
    """
    load_dotenv()
    
    rpc_url = os.getenv("RPC_URL")
    private_key = os.getenv("PRIVATE_KEY")
    vault_address = os.getenv("VAULT_ADDRESS")
    
    if not all([rpc_url, private_key, vault_address]):
        logger.error("Missing environment variables for Panic script.")
        return

    try:
        w3 = Web3(Web3.HTTPProvider(rpc_url))
        account = w3.eth.account.from_key(private_key)
        
        # Load ABI
        abi_path = os.path.join(os.path.dirname(__file__), "..", "out", "KerneVault.sol", "KerneVault.json")
        with open(abi_path, "r") as f:
            artifact = json.load(f)
            abi = artifact["abi"]

        vault = w3.eth.contract(address=vault_address, abi=abi)
        
        logger.warning(f"🚨 PANIC: Attempting to pause vault at {vault_address}...")
        
        nonce = w3.eth.get_transaction_count(account.address)
        
        tx = vault.functions.pause().build_transaction({
            'from': account.address,
            'nonce': nonce,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.info(f"Panic transaction sent: {tx_hash.hex()}. Waiting for confirmation...")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        
        if receipt.status == 1:
            logger.success("✅ VAULT PAUSED SUCCESSFULLY.")
            send_discord_alert("🚨 **PANIC BUTTON PRESSED. VAULT PAUSED.**", level="CRITICAL")
        else:
            logger.error("❌ PANIC TRANSACTION FAILED.")
            send_discord_alert("❌ **PANIC BUTTON FAILED TO PAUSE VAULT.**", level="CRITICAL")
            
    except Exception as e:
        logger.critical(f"Panic script failed: {e}")
        send_discord_alert(f"❌ **PANIC SCRIPT CRASHED: {e}**", level="CRITICAL")

if __name__ == "__main__":
    panic_pause()
