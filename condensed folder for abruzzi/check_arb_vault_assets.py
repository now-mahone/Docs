import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('bot/.env')

RPC_URL = "https://arb1.arbitrum.io/rpc"
VAULT_ADDRESS = "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF"

# Minimal ABI for totalAssets
ABI = [
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

def check_vault():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        print("Failed to connect to Arbitrum")
        return

    vault = w3.eth.contract(address=VAULT_ADDRESS, abi=ABI)
    total_assets = vault.functions.totalAssets().call()
    
    print(f"Arbitrum Vault Address: {VAULT_ADDRESS}")
    print(f"Total Assets: {total_assets / 1e18} wstETH")

if __name__ == "__main__":
    check_vault()