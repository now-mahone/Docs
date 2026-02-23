# Created: 2025-12-29
import os
import csv
import time
from typing import List, Set, Dict
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger

# Load environment variables
load_dotenv(dotenv_path="bot/.env")

# Use public Base RPC for lead scanning
RPC_URL = "https://mainnet.base.org"
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")

# Constants
AUSDC_ADDRESS = "0x4e65fE4DbA92790696d040ac24Aa414708F5c0AB"
AAVE_POOL_ADDRESS = "0xA238Dd80C259a72e81d7e4664a98015D33062AAA"
THRESHOLD = 10_000 * 10**6  # $10k
BLOCK_RANGE = 10_000        # Reduced to 10k blocks for speed

# Minimal ABI for Transfer event and balanceOf
ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "from", "type": "address"},
            {"indexed": True, "name": "to", "type": "address"},
            {"indexed": False, "name": "value", "type": "uint256"},
        ],
        "name": "Transfer",
        "type": "event",
    },
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function",
    },
]

def get_leads():
    if not RPC_URL:
        logger.error("RPC_URL not found")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        logger.error(f"Failed to connect to RPC at {RPC_URL}")
        return

    logger.info(f"Connected to Base. Current block: {w3.eth.block_number}")

    contract = w3.eth.contract(address=Web3.to_checksum_address(AUSDC_ADDRESS), abi=ABI)

    current_block = w3.eth.block_number
    from_block = current_block - BLOCK_RANGE

    logger.info(f"Fetching Transfer events from block {from_block} to {current_block}...")
    
    # Fetch Transfer events in small chunks
    chunk_size = 2000
    events = []
    for start in range(from_block, current_block, chunk_size):
        end = min(start + chunk_size, current_block)
        try:
            logger.info(f"Fetching chunk {start} to {end}...")
            chunk_events = contract.events.Transfer.get_logs(
                from_block=start,
                to_block=end
            )
            events.extend(chunk_events)
            time.sleep(0.2)
        except Exception as e:
            logger.warning(f"Failed to fetch chunk {start} to {end}: {e}")

    logger.info(f"Found {len(events)} total transfer events.")

    # Aggregate transfers
    recipient_totals: Dict[str, int] = {}
    for event in events:
        to_addr = event['args']['to']
        value = event['args']['value']
        recipient_totals[to_addr] = recipient_totals.get(to_addr, 0) + value

    # Filter recipients who received at least $10k
    potential_leads = [addr for addr, total in recipient_totals.items() if total >= 10_000 * 10**6]
    
    logger.info(f"Filtered to {len(potential_leads)} potential leads based on recent transfers.")

    leads_data = []
    exclude_addresses = {Web3.to_checksum_address(AAVE_POOL_ADDRESS), Web3.to_checksum_address(AUSDC_ADDRESS)}

    for addr in potential_leads:
        checksum_addr = Web3.to_checksum_address(addr)
        
        if checksum_addr in exclude_addresses:
            continue

        # Check if it's a contract
        try:
            code = w3.eth.get_code(checksum_addr)
            if code != b'' and len(code) > 0:
                continue
        except:
            pass

        try:
            # Exponential backoff for 429s
            max_retries = 3
            balance = 0
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        time.sleep(1 * attempt)
                    balance = contract.functions.balanceOf(checksum_addr).call()
                    break
                except Exception as e:
                    if "429" in str(e) and attempt < max_retries - 1:
                        continue
                    raise e

            if balance > THRESHOLD:
                balance_usdc = balance / 10**6
                leads_data.append({
                    "Address": checksum_addr,
                    "Balance_USDC": balance_usdc,
                    "Basescan_Link": f"https://basescan.org/address/{checksum_addr}"
                })
                logger.success(f"Lead found: {checksum_addr} - ${balance_usdc:,.2f}")
        except Exception as e:
            pass

    # Sort by balance descending
    leads_data.sort(key=lambda x: x["Balance_USDC"], reverse=True)

    # Save to CSV
    os.makedirs("docs", exist_ok=True)
    csv_file = "docs/leads_v2.csv"
    with open(csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Address", "Balance_USDC", "Basescan_Link"])
        writer.writeheader()
        writer.writerows(leads_data[:50])

    logger.info(f"Saved {min(len(leads_data), 50)} leads to {csv_file}")
    
    # Print top 10
    print("\nTOP 10 LEADS:")
    for i, lead in enumerate(leads_data[:10]):
        print(f"{i+1}. {lead['Address']} - ${lead['Balance_USDC']:,.2f}")

if __name__ == "__main__":
    get_leads()
