# Created: 2025-12-29
import os
import time
import csv
from loguru import logger
from web3 import Web3
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot/.env")

# Configuration
RPC_URL = os.getenv("RPC_URL", "https://mainnet.base.org")
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# High-Ticket Marketing Message
MESSAGE = "Kerne.ai: Institutional Delta-Neutral Yield. Enterprise White-Label Live. Demo: kerne.ai/partner"

def send_marketing_tx(target_address: str):
    if not PRIVATE_KEY:
        logger.error("PRIVATE_KEY not found in environment")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    account = w3.eth.account.from_key(PRIVATE_KEY)
    
    # We send a 0 ETH transaction to the target with the message in hex data
    data = Web3.to_hex(text=MESSAGE)
    
    try:
        tx = {
            'nonce': w3.eth.get_transaction_count(account.address),
            'to': Web3.to_checksum_address(target_address),
            'value': 0,
            'gas': 50000,
            'gasPrice': w3.eth.gas_price,
            'data': data,
            'chainId': w3.eth.chain_id
        }
        
        signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        
        logger.success(f"Marketing Message Sent to {target_address}! TX Hash: {tx_hash.hex()}")
        return tx_hash.hex()
    except Exception as e:
        logger.error(f"Failed to send to {target_address}: {e}")
        return None

def blast_top_leads(limit: int = 10):
    leads_file = "docs/leads_v2.csv"
    if not os.path.exists(leads_file):
        logger.error(f"Leads file {leads_file} not found")
        return

    with open(leads_file, mode="r") as f:
        reader = csv.DictReader(f)
        count = 0
        for row in reader:
            if count >= limit:
                break
            
            address = row["Address"]
            balance = row["Balance_USDC"]
            
            logger.info(f"Targeting Whale: {address} (${float(balance):,.2f})")
            send_marketing_tx(address)
            
            count += 1
            time.sleep(1) # Avoid nonce issues/rate limits

if __name__ == "__main__":
    # Only run if we have a private key
    if os.getenv("PRIVATE_KEY"):
        blast_top_leads(10)
    else:
        logger.warning("No PRIVATE_KEY found. Skipping outreach blast.")
