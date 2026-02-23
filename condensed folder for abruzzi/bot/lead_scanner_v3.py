# Created: 2026-01-06
import os
import csv
import time
from typing import List, Set, Dict
from web3 import Web3
from dotenv import load_dotenv
from loguru import logger
from bot.email_manager import EmailManager

# Load environment variables
load_dotenv(dotenv_path="bot/.env")

# Use public Base RPC for lead scanning
RPC_URL = "https://mainnet.base.org"
BASESCAN_API_KEY = os.getenv("BASESCAN_API_KEY")

# Institutional Constants
WETH_ADDRESS = "0x4200000000000000000000000000000000000006"
CBETH_ADDRESS = "0x2Ae3F1Ec7F1F5012CFEab0185bbe7aa990d4405E"
WSTETH_ADDRESS = "0x5981E5794098E1d9456345A29e9e00962B02d50C"
THRESHOLD_ETH = 50  # 50 ETH (~$125k+) for institutional focus
BLOCK_RANGE = 20_000

# Minimal ABI
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

def get_institutional_leads():
    if not RPC_URL:
        logger.error("RPC_URL not found")
        return

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        logger.error(f"Failed to connect to RPC at {RPC_URL}")
        return

    logger.info(f"Connected to Base. Current block: {w3.eth.block_number}")

    tokens = {
        "WETH": WETH_ADDRESS,
        "cbETH": CBETH_ADDRESS,
        "wstETH": WSTETH_ADDRESS
    }

    current_block = w3.eth.block_number
    from_block = current_block - BLOCK_RANGE
    
    all_leads_data = []
    seen_addresses = set()

    for name, addr in tokens.items():
        logger.info(f"Scanning {name} for institutional leads...")
        contract = w3.eth.contract(address=Web3.to_checksum_address(addr), abi=ABI)
        
        # Fetch Transfer events in smaller chunks to avoid RPC limits
        chunk_size = 1000 if name == "WETH" else 2000
        events = []
        try:
            for start in range(from_block, current_block, chunk_size):
                end = min(start + chunk_size, current_block)
                logger.info(f"Fetching {name} logs from {start} to {end}...")
                
                retries = 3
                while retries > 0:
                    try:
                        chunk_events = contract.events.Transfer.get_logs(
                            fromBlock=start,
                            toBlock=end
                        )
                        events.extend(chunk_events)
                        break
                    except Exception as e:
                        if "503" in str(e) or "rate limit" in str(e).lower():
                            logger.warning(f"Rate limited on {name}. Retrying in 5s... ({retries} left)")
                            time.sleep(5)
                            retries -= 1
                        else:
                            raise e
                
                time.sleep(1.0)  # Increased rate limit protection
            logger.info(f"Found {len(events)} transfers for {name}")
            
            recipient_totals: Dict[str, int] = {}
            for event in events:
                to_addr = event['args']['to']
                value = event['args']['value']
                recipient_totals[to_addr] = recipient_totals.get(to_addr, 0) + value

            # Filter recipients
            potential_leads = [addr for addr, total in recipient_totals.items() if total >= THRESHOLD_ETH * 10**18]
            
            for lead_addr in potential_leads:
                checksum_addr = Web3.to_checksum_address(lead_addr)
                if checksum_addr in seen_addresses:
                    continue
                
                # Check if contract
                try:
                    code = w3.eth.get_code(checksum_addr)
                    if code != b'' and len(code) > 0:
                        continue
                    
                    balance = contract.functions.balanceOf(checksum_addr).call()
                    time.sleep(0.1) # Small delay
                except Exception as e:
                    logger.warning(f"Error checking address {checksum_addr}: {e}")
                    continue
                if balance >= THRESHOLD_ETH * 10**18:
                    balance_eth = balance / 10**18
                    all_leads_data.append({
                        "Address": checksum_addr,
                        "Asset": name,
                        "Balance": balance_eth,
                        "Category": "Institutional/Whale",
                        "Basescan_Link": f"https://basescan.org/address/{checksum_addr}"
                    })
                    seen_addresses.add(checksum_addr)
                    logger.success(f"Institutional Lead found: {checksum_addr} - {balance_eth:.2f} {name}")
                    
        except Exception as e:
            logger.error(f"Error scanning {name}: {e}")

    # Sort by balance descending (approximate since assets differ)
    all_leads_data.sort(key=lambda x: x["Balance"], reverse=True)

    # Save to CSV
    os.makedirs("docs", exist_ok=True)
    csv_file = "docs/institutional_leads.csv"
    with open(csv_file, mode="w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["Address", "Asset", "Balance", "Category", "Basescan_Link"])
        writer.writeheader()
        writer.writerows(all_leads_data)

    logger.info(f"Saved {len(all_leads_data)} institutional leads to {csv_file}")

    # ── Autonomous Outreach Integration ──────────────────────────────
    if os.getenv("AUTONOMOUS_OUTREACH", "").lower() == "true":
        logger.info("AUTONOMOUS_OUTREACH enabled. Initiating email outreach...")
        try:
            email_mgr = EmailManager()
            if email_mgr.is_configured():
                # Build lead list for outreach (requires enriched data with emails)
                outreach_leads = []
                for lead in all_leads_data:
                    if lead.get("Email"):
                        outreach_leads.append({
                            "email": lead["Email"],
                            "address": lead["Address"],
                            "balance": lead["Balance"],
                            "asset": lead["Asset"],
                        })

                if outreach_leads:
                    stats = email_mgr.get_outreach_stats()
                    logger.info(f"Outreach stats before send: {stats}")
                    results = email_mgr.send_batch_outreach(outreach_leads)
                    logger.info(f"Outreach results: {results}")
                else:
                    logger.info(
                        "No leads with email addresses. Add 'Email' column to "
                        "institutional_leads.csv to enable autonomous outreach."
                    )
            else:
                logger.warning(
                    "Email manager not configured. Set PROTON_PASSWORD in bot/.env"
                )
        except Exception as e:
            logger.error(f"Autonomous outreach failed: {e}")
    else:
        logger.info(
            "Autonomous outreach disabled. Set AUTONOMOUS_OUTREACH=true in bot/.env to enable."
        )


if __name__ == "__main__":
    get_institutional_leads()
