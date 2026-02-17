# Created: 2026-02-12
"""Check all balances to find funds for transfer."""
from web3 import Web3
import requests

print("=" * 60)
print("COMPREHENSIVE BALANCE CHECK")
print("=" * 60)

# RPC endpoints
w3_base = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
w3_arb = Web3(Web3.HTTPProvider('https://arb1.arbitrum.io/rpc'))

# Addresses
bot = '0x57D400cED462a01Ed51a5De038F204Df49690A99'
trezor = '0x14f0fd37A6c42bFe4afDD9DEe6C4Eb7d25073946'
vault_base = '0xDA9765F84208F8E94225889B2C9331DCe940fB20'
zin_base = '0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7'

# Token addresses
usdc_base = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
weth_base = '0x4200000000000000000000000000000000000006'

erc20_abi = [{'inputs': [{'name': 'account', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'}]

def get_balance(w3, token, addr):
    if token == 'native':
        return w3.eth.get_balance(Web3.to_checksum_address(addr)) / 1e18
    contract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=erc20_abi)
    return contract.functions.balanceOf(Web3.to_checksum_address(addr)).call() / 1e6

print("\n--- BASE ---")
print(f"Bot ETH: {get_balance(w3_base, 'native', bot):.6f}")
print(f"Bot USDC: {get_balance(w3_base, usdc_base, bot):.2f}")
print(f"Trezor ETH: {get_balance(w3_base, 'native', trezor):.6f}")
print(f"Trezor USDC: {get_balance(w3_base, usdc_base, trezor):.2f}")

print("\n--- ZIN Pool (Base) ---")
print(f"USDC: {get_balance(w3_base, usdc_base, zin_base):.2f}")
print(f"WETH: {get_balance(w3_base, weth_base, zin_base) / 1e12:.6f}")  # WETH is 18 decimals

print("\n--- ARBITRUM ---")
print(f"Bot ETH: {get_balance(w3_arb, 'native', bot):.6f}")

print("\n--- HYPERLIQUID ---")
try:
    resp = requests.post('https://api.hyperliquid.xyz/info', 
        json={'type': 'clearinghouseState', 'user': bot}, timeout=15)
    data = resp.json()
    print(f"Account Value: ${float(data.get('marginSummary', {}).get('accountValue', 0)):.4f}")
    print(f"Withdrawable: ${float(data.get('withdrawable', 0)):.4f}")
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)