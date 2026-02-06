import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('bot/.env')

RPC_URL = "https://mainnet.base.org"
VAULT_ADDRESS = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"

# Minimal ABI for totalAssets
ABI = [
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "asset",
        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def check_vault():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Failed to connect to Base")
        return

    vault = w3.eth.contract(address=VAULT_ADDRESS, abi=ABI)
    total_assets = vault.functions.totalAssets().call()
    asset_address = vault.functions.asset().call()
    
    print(f"Vault Address: {VAULT_ADDRESS}")
    print(f"Underlying Asset: {asset_address}")
    print(f"Total Assets: {total_assets / 1e18} ETH")

if __name__ == "__main__":
    check_vault()