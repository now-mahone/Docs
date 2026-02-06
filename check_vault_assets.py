# Created: 2026-02-06
import os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('bot/.env')

VAULT_ADDRESS = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"

# Multi-RPC fallback for reliability
RPC_URLS = [
    "https://mainnet.base.org",
    "https://base.drpc.org",
    "https://1rpc.io/base",
    "https://base-mainnet.public.blastapi.io",
    "https://base.llamarpc.com",
]

# Full ABI for vault state inspection
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
        "name": "totalSupply",
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
    },
    {
        "inputs": [],
        "name": "paused",
        "outputs": [{"internalType": "bool", "name": "", "type": "bool"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "offChainAssets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "l1Assets",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "hedgingReserve",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "projectedAPY",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "getSolvencyRatio",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
]

# ERC20 balanceOf for checking WETH held by vault
ERC20_ABI = [
    {
        "inputs": [{"internalType": "address", "name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
]


import time


def get_web3(preferred_index=0):
    """Connect using multi-RPC fallback, starting from preferred_index."""
    order = list(range(len(RPC_URLS)))
    # Rotate so preferred_index is tried first
    order = order[preferred_index:] + order[:preferred_index]
    for i in order:
        rpc = RPC_URLS[i]
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                return w3, i
        except Exception:
            continue
    return None, -1


def safe_call(w3, contract, fn_name, fallback=0):
    """Call a contract function with retry on different RPC if rate-limited."""
    try:
        return getattr(contract.functions, fn_name)().call()
    except Exception as e:
        err = str(e)
        if "429" in err or "Too Many" in err:
            # Try a different RPC
            time.sleep(0.5)
            for rpc in RPC_URLS[1:]:
                try:
                    w3_retry = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
                    if w3_retry.is_connected():
                        c = w3_retry.eth.contract(address=contract.address, abi=contract.abi)
                        return getattr(c.functions, fn_name)().call()
                except Exception:
                    continue
        print(f"  ⚠️  {fn_name}() failed: {err[:80]}")
        return fallback


def check_vault():
    w3, idx = get_web3(preferred_index=1)  # Skip mainnet.base.org (rate-limits)
    if not w3:
        print("ERROR: Failed to connect to any Base RPC")
        return

    print(f"Connected via: {RPC_URLS[idx]}")
    vault = w3.eth.contract(address=VAULT_ADDRESS, abi=ABI)

    # Core state with safe calls
    asset_address = safe_call(w3, vault, "asset", "0x0000000000000000000000000000000000000000")
    is_paused = safe_call(w3, vault, "paused", False)
    total_assets = safe_call(w3, vault, "totalAssets", 0)
    total_supply = safe_call(w3, vault, "totalSupply", 0)
    offchain = safe_call(w3, vault, "offChainAssets", 0)
    l1 = safe_call(w3, vault, "l1Assets", 0)
    reserve = safe_call(w3, vault, "hedgingReserve", 0)
    apy = safe_call(w3, vault, "projectedAPY", 0)
    solvency = safe_call(w3, vault, "getSolvencyRatio", 20000)

    # WETH balance held by vault contract
    weth_balance = 0
    try:
        weth = w3.eth.contract(address=asset_address, abi=ERC20_ABI)
        weth_balance = weth.functions.balanceOf(VAULT_ADDRESS).call()
    except Exception:
        pass

    # ETH balance of deployer (for gas checks)
    deployer = "0x57D400cED462a01Ed51a5De038F204Df49690A99"
    deployer_eth = 0
    try:
        deployer_eth = w3.eth.get_balance(deployer)
    except Exception:
        pass

    print("=" * 60)
    print(f"  KERNE VAULT STATUS")
    print("=" * 60)
    print(f"  Vault Address:     {VAULT_ADDRESS}")
    print(f"  Underlying Asset:  {asset_address} (WETH)")
    print(f"  Paused:            {is_paused}")
    print(f"  Solvency Ratio:    {solvency / 100:.2f}%")
    print(f"  Projected APY:     {apy / 100:.2f}%")
    print("-" * 60)
    print(f"  Total Assets:      {total_assets / 1e18:.6f} WETH")
    print(f"    On-Chain WETH:   {weth_balance / 1e18:.6f} WETH")
    print(f"    Off-Chain:       {offchain / 1e18:.6f} WETH")
    print(f"    L1 (Hyperliquid):{l1 / 1e18:.6f} WETH")
    print(f"    Hedging Reserve: {reserve / 1e18:.6f} WETH")
    print(f"  Total Supply:      {total_supply / 1e18:.6f} shares")
    print("-" * 60)
    print(f"  Deployer ETH:      {deployer_eth / 1e18:.6f} ETH (gas)")
    print("=" * 60)

    if total_assets == 0:
        print("\n  ⚠️  VAULT IS EMPTY — No deposits yet.")
        print("  Next: Swap USDC → WETH and deposit into vault to establish TVL.")


if __name__ == "__main__":
    check_vault()
