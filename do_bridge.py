"""Bridge 362.3 USDC from Polygon to Base via capital_router."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv("bot/.env")

from bot.capital_router import BridgeEngine

private_key = os.getenv("PRIVATE_KEY")
from eth_account import Account
wallet_address = Account.from_key(private_key).address

print(f"Wallet: {wallet_address}")
print(f"Bridging 362.3 USDC from POLYGON -> BASE...")

bridge = BridgeEngine(private_key, wallet_address)
tx_hash = bridge.bridge(
    amount=362.3,
    from_token="USDC",
    from_chain="POLYGON",
    to_token="USDC",
    to_chain="BASE",
    dry_run=False,
)

if tx_hash:
    print(f"\nBridge TX sent: {tx_hash}")
    print(f"Track: https://polygonscan.com/tx/{tx_hash}")
    print("Funds should arrive on Base in 2-5 minutes.")
else:
    print("Bridge failed or dry run.")