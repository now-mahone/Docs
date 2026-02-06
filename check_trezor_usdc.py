import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("bot/.env")

TREZOR_ADDR = "0x14f0fd37A6c42bFe4afDD9DEe6C4Eb7d25073946"
HOT_WALLET_ADDR = "0x57D400cED462a01Ed51a5De038F204Df49690A99"

# USDC Addresses
POLYGON_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
POLYGON_USDC_E = "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"constant": True, "inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "type": "function"},
]

def check_balance(rpc, token_addr, wallet_addr, label):
    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        if not w3.is_connected():
            return
        
        if token_addr:
            contract = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
            balance = contract.functions.balanceOf(Web3.to_checksum_address(wallet_addr)).call()
            decimals = contract.functions.decimals().call()
            print(f"{label}: {balance / (10**decimals):.2f}")
        else:
            balance = w3.eth.get_balance(Web3.to_checksum_address(wallet_addr))
            print(f"{label} (Native): {w3.from_wei(balance, 'ether'):.6f}")
    except Exception as e:
        print(f"Error checking {label}: {e}")

print("--- POLYGON ---")
poly_rpcs = [
    os.getenv("POLYGON_RPC_URL", ""),
    "https://polygon-rpc.com",
    "https://rpc-mainnet.maticvigil.com",
    "https://1rpc.io/matic"
]
poly_rpcs = [r for r in poly_rpcs if r]
success = False
for rpc in poly_rpcs:
    try:
        w3 = Web3(Web3.HTTPProvider(rpc))
        if w3.is_connected():
            check_balance(rpc, POLYGON_USDC, TREZOR_ADDR, "Trezor USDC (Native)")
            check_balance(rpc, POLYGON_USDC_E, TREZOR_ADDR, "Trezor USDC.e (Bridged)")
            check_balance(rpc, None, TREZOR_ADDR, "Trezor MATIC")
            check_balance(rpc, POLYGON_USDC, HOT_WALLET_ADDR, "Hot Wallet USDC (Native)")
            check_balance(rpc, POLYGON_USDC_E, HOT_WALLET_ADDR, "Hot Wallet USDC.e (Bridged)")
            check_balance(rpc, None, HOT_WALLET_ADDR, "Hot Wallet MATIC")
            success = True
            break
    except:
        continue
if not success:
    print("Failed to connect to any Polygon RPC")

print("\n--- BASE ---")
base_rpc = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
check_balance(base_rpc, BASE_USDC, TREZOR_ADDR, "Trezor USDC")
check_balance(base_rpc, BASE_USDC, HOT_WALLET_ADDR, "Hot Wallet USDC")
check_balance(base_rpc, None, HOT_WALLET_ADDR, "Hot Wallet ETH")