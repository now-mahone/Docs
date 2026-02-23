import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("bot/.env")

TREZOR_ADDR = "0x14f0fd37A6c42bFe4afDD9DEe6C4Eb7d25073946"
PRIVATE_KEY = os.getenv("PRIVATE_KEY")

# Polygon RPC
rpc = "https://polygon-rpc.com"
w3 = Web3(Web3.HTTPProvider(rpc))

if not w3.is_connected():
    print("Failed to connect to Polygon")
    exit(1)

account = w3.eth.account.from_key(PRIVATE_KEY)
print(f"Sending from: {account.address}")

nonce = w3.eth.get_transaction_count(account.address)
tx = {
    'nonce': nonce,
    'to': Web3.to_checksum_address(TREZOR_ADDR),
    'value': w3.to_wei(1, 'ether'), # 1 MATIC
    'gas': 21000,
    'gasPrice': w3.eth.gas_price,
    'chainId': 137
}

signed_tx = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)

print(f"Transaction sent! Hash: {tx_hash.hex()}")
print(f"Explorer: https://polygonscan.com/tx/{tx_hash.hex()}")