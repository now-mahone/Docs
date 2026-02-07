# Quick balance scan for capital deployment
# Created: 2026-02-07
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web3 import Web3
from web3.middleware import geth_poa_middleware
import requests

ERC20_ABI = [{"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},{"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"}]

def get_w3(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 10}))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def check_balance(w3, wallet, token_addr=None, label=""):
    wallet = Web3.to_checksum_address(wallet)
    if token_addr:
        token_addr = Web3.to_checksum_address(token_addr)
        c = w3.eth.contract(address=token_addr, abi=ERC20_ABI)
        bal = c.functions.balanceOf(wallet).call()
        dec = c.functions.decimals().call()
        val = bal / (10 ** dec)
        if val > 0.0001:
            print(f"  {label}: {val:.6f}")
        return val
    else:
        bal = w3.eth.get_balance(wallet)
        val = float(Web3.from_wei(bal, "ether"))
        if val > 0.000001:
            print(f"  {label}: {val:.6f}")
        return val

# Get ETH price
try:
    r = requests.get("https://api.coingecko.com/api/v3/simple/price", params={"ids":"ethereum","vs_currencies":"usd"}, timeout=5)
    eth_price = r.json()["ethereum"]["usd"]
except:
    eth_price = 2700
print(f"ETH Price: ${eth_price:,.2f}")
print("=" * 60)

# Key wallets
HOT = "0x57D400cED462a01Ed51a5De038F204Df49690A99"
BURNER = "0x14f0fd37A6c42bFe4afDD9DEe6C4Eb7d25073946"
VAULT = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"
ZIN_BASE = "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7"

total_usd = 0.0

# === BASE ===
print("\n--- BASE ---")
try:
    w3 = get_w3("https://mainnet.base.org")
    
    print("Hot Wallet (0x57D4...0A99):")
    eth_b = check_balance(w3, HOT, label="ETH")
    total_usd += eth_b * eth_price
    usdc_b = check_balance(w3, HOT, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USDC")
    total_usd += usdc_b
    weth_b = check_balance(w3, HOT, "0x4200000000000000000000000000000000000006", "WETH")
    total_usd += weth_b * eth_price

    print("KerneVault (0x8005...2AC):")
    weth_v = check_balance(w3, VAULT, "0x4200000000000000000000000000000000000006", "WETH")
    total_usd += weth_v * eth_price

    print("ZIN Pool Base (0xB9Bd...d0c7):")
    usdc_z = check_balance(w3, ZIN_BASE, "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "USDC")
    total_usd += usdc_z
    weth_z = check_balance(w3, ZIN_BASE, "0x4200000000000000000000000000000000000006", "WETH")
    total_usd += weth_z * eth_price
except Exception as e:
    print(f"  ERROR: {e}")

# === POLYGON ===
print("\n--- POLYGON ---")
try:
    w3p = get_w3("https://polygon-rpc.com")
    
    print("Trezor Burner (0x14f0...3946):")
    usdc_poly = check_balance(w3p, BURNER, "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "USDC (native)")
    total_usd += usdc_poly
    # Also check USDC.e (bridged)
    usdc_e = check_balance(w3p, BURNER, "0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174", "USDC.e (bridged)")
    total_usd += usdc_e
    matic = check_balance(w3p, BURNER, label="MATIC")
    
    print("Hot Wallet on Polygon:")
    usdc_hot_poly = check_balance(w3p, HOT, "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359", "USDC (native)")
    total_usd += usdc_hot_poly
except Exception as e:
    print(f"  ERROR: {e}")

# === HYPERLIQUID ===
print("\n--- HYPERLIQUID ---")
try:
    resp = requests.post("https://api.hyperliquid.xyz/info", json={"type":"clearinghouseState","user":HOT}, timeout=10)
    data = resp.json()
    if "marginSummary" in data:
        hl_val = float(data["marginSummary"]["accountValue"])
        print(f"  Account Equity: ${hl_val:.2f}")
        total_usd += hl_val
    else:
        print(f"  No margin data")
except Exception as e:
    print(f"  ERROR: {e}")

# === ARBITRUM (quick check) ===
print("\n--- ARBITRUM ---")
try:
    w3a = get_w3("https://arb1.arbitrum.io/rpc")
    print("Hot Wallet:")
    eth_arb = check_balance(w3a, HOT, label="ETH")
    total_usd += eth_arb * eth_price
    usdc_arb = check_balance(w3a, HOT, "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "USDC")
    total_usd += usdc_arb
except Exception as e:
    print(f"  ERROR: {e}")

print("\n" + "=" * 60)
print(f"TOTAL CAPITAL (approximate): ${total_usd:,.2f}")
print("=" * 60)