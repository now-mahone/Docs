# Created: 2026-02-10
# Withdraw USDC from Hyperliquid to Arbitrum for gas funding
import os
import sys
import time

# Load env
from dotenv import load_dotenv
load_dotenv("bot/.env")

from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import eth_account

def main():
    private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY") or os.getenv("STRATEGIST_PRIVATE_KEY")
    if not private_key:
        print("ERROR: No private key found in bot/.env")
        sys.exit(1)
    
    account = eth_account.Account.from_key(private_key)
    address = account.address
    print(f"Account: {address}")
    
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    exchange = Exchange(account, constants.MAINNET_API_URL)
    
    # Check current state
    user_state = info.user_state(address)
    margin_summary = user_state.get("marginSummary", {})
    withdrawable = float(user_state.get("withdrawable", 0))
    account_value = float(margin_summary.get("accountValue", 0))
    total_margin = float(margin_summary.get("totalMarginUsed", 0))
    
    print(f"Account Value: ${account_value:.2f}")
    print(f"Margin Used: ${total_margin:.2f}")
    print(f"Withdrawable: ${withdrawable:.2f}")
    
    # We need ~$10 for gas (will swap to ETH on Base)
    withdraw_amount = 10.0
    
    if withdrawable < withdraw_amount:
        print(f"ERROR: Only ${withdrawable:.2f} withdrawable, need ${withdraw_amount}")
        # Try smaller amount
        withdraw_amount = min(5.0, withdrawable - 1.0)
        if withdraw_amount < 2.0:
            print("ERROR: Not enough withdrawable balance")
            sys.exit(1)
        print(f"Adjusted withdrawal to ${withdraw_amount:.2f}")
    
    print(f"\nWithdrawing ${withdraw_amount} USDC from Hyperliquid to {address} on Arbitrum...")
    
    try:
        # HL withdraw_from_bridge expects amount in raw USDC (but the SDK handles conversion)
        response = exchange.withdraw_from_bridge(
            amount=withdraw_amount,
            destination=address
        )
        print(f"Response: {response}")
        
        if response.get("status") == "ok":
            print(f"\nSUCCESS: Withdrawal of ${withdraw_amount} USDC initiated!")
            print(f"Funds will arrive on Arbitrum at {address} in ~5-10 minutes.")
            print(f"Next step: Bridge USDC from Arbitrum to Base and swap for ETH.")
        else:
            print(f"FAILED: {response}")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()