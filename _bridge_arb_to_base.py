# Created: 2026-02-10
# Bridge USDC from Arbitrum to Base and receive ETH
# Uses Relay Protocol API for gasless cross-chain execution
import os
import sys
import json
import time
import urllib.request

from dotenv import load_dotenv
load_dotenv("bot/.env")

from eth_account import Account
from eth_account.messages import encode_typed_data

DEPLOYER_KEY = os.getenv("PRIVATE_KEY")
if not DEPLOYER_KEY:
    print("ERROR: No PRIVATE_KEY in bot/.env")
    sys.exit(1)

account = Account.from_key(DEPLOYER_KEY)
ADDRESS = account.address
print(f"Address: {ADDRESS}")

# Chain IDs
ARBITRUM_CHAIN_ID = 42161
BASE_CHAIN_ID = 8453

# USDC on Arbitrum (native)
USDC_ARB = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"

def check_usdc_balance():
    """Check USDC balance on Arbitrum using cast"""
    import subprocess
    result = subprocess.run(
        ["cast", "call", USDC_ARB, "balanceOf(address)(uint256)", ADDRESS, 
         "--rpc-url", "https://arb1.arbitrum.io/rpc"],
        capture_output=True, text=True
    )
    balance = int(result.stdout.strip()) if result.stdout.strip() else 0
    return balance

def check_eth_balance_base():
    """Check ETH balance on Base"""
    import subprocess
    result = subprocess.run(
        ["cast", "balance", ADDRESS, "--rpc-url", "https://base.drpc.org", "-e"],
        capture_output=True, text=True
    )
    return result.stdout.strip()

def get_relay_quote(amount_usdc):
    """Get a quote from Relay Protocol for USDC (Arb) -> ETH (Base)"""
    url = "https://api.relay.link/quote"
    payload = {
        "user": ADDRESS,
        "originChainId": ARBITRUM_CHAIN_ID,
        "destinationChainId": BASE_CHAIN_ID,
        "originCurrency": USDC_ARB,
        "destinationCurrency": "0x0000000000000000000000000000000000000000",  # Native ETH
        "amount": str(amount_usdc),
        "recipient": ADDRESS,
        "tradeType": "EXACT_INPUT"
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    
    try:
        response = urllib.request.urlopen(req)
        return json.loads(response.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"Relay API error {e.code}: {error_body}")
        return None

def main():
    print("=" * 60)
    print("BRIDGE: USDC (Arbitrum) -> ETH (Base)")
    print("=" * 60)
    
    # Step 1: Wait for USDC to arrive on Arbitrum
    print("\nStep 1: Checking USDC balance on Arbitrum...")
    max_wait = 600  # 10 minutes
    start = time.time()
    
    while time.time() - start < max_wait:
        balance = check_usdc_balance()
        if balance > 0:
            print(f"  USDC arrived! Balance: {balance / 1e6:.2f} USDC")
            break
        elapsed = int(time.time() - start)
        print(f"  Waiting for USDC... ({elapsed}s elapsed)")
        time.sleep(15)
    else:
        print("  TIMEOUT: USDC did not arrive within 10 minutes.")
        print("  The HL withdrawal may still be processing. Try again later.")
        sys.exit(1)
    
    # Step 2: Get Relay quote
    print("\nStep 2: Getting Relay Protocol quote...")
    quote = get_relay_quote(balance)
    
    if quote:
        print(f"  Quote received: {json.dumps(quote, indent=2)[:500]}")
        # TODO: Execute the bridge using the quote
        # This would involve signing a permit and submitting to Relay
    else:
        print("  Relay quote failed. Trying alternative approach...")
        print("\n  Alternative: You have USDC on Arbitrum but need gas.")
        print("  Options:")
        print("  1. Use https://relay.link manually (gasless bridge)")
        print("  2. Use https://app.across.to (bridge with permit)")
        print("  3. Send 0.001 ETH from any funded wallet to the deployer on Arbitrum")
    
    # Step 3: Check if ETH arrived on Base
    print(f"\nBase ETH balance: {check_eth_balance_base()}")

if __name__ == "__main__":
    main()