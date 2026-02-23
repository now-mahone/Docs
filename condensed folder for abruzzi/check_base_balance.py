from web3 import Web3
import sys

def check_balance():
    # Base RPC
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
    
    # Kerne Treasury
    addr = '0x57D400cED462a01Ed51a5De038F204Df49690A99'
    
    # USDC on Base
    usdc_address = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    
    abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    try:
        contract = w3.eth.contract(address=Web3.to_checksum_address(usdc_address), abi=abi)
        balance = contract.functions.balanceOf(Web3.to_checksum_address(addr)).call()
        print(f"Base USDC Balance: {balance / 1e6}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_balance()