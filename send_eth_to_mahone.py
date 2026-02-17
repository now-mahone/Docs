# Created: 2026-02-12
"""
Send $10 worth of ETH on Arbitrum to Mahone's wallet.
"""
import os
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("bot/.env")

MAHONE_ADDR = "0x8b54AA4fc3aaDCD101084BBF2a875c47537090E5"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ARB_RPC_URL = os.getenv("ARB_RPC_URL")

if not PRIVATE_KEY:
    print("ERROR: PRIVATE_KEY not found in environment")
    exit(1)

if not ARB_RPC_URL:
    print("ERROR: ARB_RPC_URL not found in environment")
    exit(1)

# Connect to Arbitrum
w3 = Web3(Web3.HTTPProvider(ARB_RPC_URL))

if not w3.is_connected():
    print("Failed to connect to Arbitrum")
    exit(1)

print(f"Connected to Arbitrum. Chain ID: {w3.eth.chain_id}")

# Get ETH price from CoinGecko
try:
    response = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10)
    eth_price = response.json()["ethereum"]["usd"]
    print(f"Current ETH price: ${eth_price}")
except Exception as e:
    print(f"Failed to get ETH price: {e}")
    exit(1)

# Calculate $10 worth of ETH
amount_usd = 10.0
amount_eth = amount_usd / eth_price
amount_wei = w3.to_wei(amount_eth, 'ether')

print(f"Sending ${amount_usd} = {amount_eth:.6f} ETH to Mahone")

# Get account
account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Sending from: {account.address}")

# Check balance
balance_wei = w3.eth.get_balance(account.address)
balance_eth = float(w3.from_wei(balance_wei, 'ether'))
print(f"Sender balance: {balance_eth:.6f} ETH")

if balance_eth < amount_eth + 0.001:  # Leave some for gas
    print(f"ERROR: Insufficient balance. Need ~{amount_eth + 0.001:.6f} ETH")
    exit(1)

# Build transaction
nonce = w3.eth.get_transaction_count(account.address)
gas_price = w3.eth.gas_price

tx = {
    'nonce': nonce,
    'to': Web3.to_checksum_address(MAHONE_ADDR),
    'value': amount_wei,
    'gas': 21000,
    'gasPrice': gas_price,
    'chainId': w3.eth.chain_id
}

print(f"\nTransaction details:")
print(f"  To: {MAHONE_ADDR}")
print(f"  Value: {amount_eth:.6f} ETH (${amount_usd})")
print(f"  Gas Price: {w3.from_wei(gas_price, 'gwei'):.2f} Gwei")
print(f"  Estimated Gas Cost: {w3.from_wei(21000 * gas_price, 'ether'):.6f} ETH")

# Sign and send
signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

print(f"\nTransaction sent!")
print(f"Hash: {tx_hash.hex()}")
print(f"Explorer: https://arbiscan.io/tx/{tx_hash.hex()}")

# Wait for confirmation
print("\nWaiting for confirmation...")
receipt = w3.eth.wait_for_transaction_receipt(tx_hash)

if receipt.status == 1:
    print(f"SUCCESS! Transaction confirmed.")
    print(f"Block: {receipt.blockNumber}")
else:
    print("FAILED! Transaction reverted.")