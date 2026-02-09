# Created: 2026-02-08
# Temporary script to check Hyperliquid status for telemetry verification
import json
import sys

try:
    from hyperliquid.info import Info
    from hyperliquid.utils import constants
except ImportError:
    print("ERROR: hyperliquid package not installed")
    sys.exit(1)

try:
    from web3 import Web3
except ImportError:
    Web3 = None

DEPLOYER = "0x57D400cED462a01Ed51a5De038F204Df49690A99"
BASE_VAULT = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"

# === Hyperliquid Data ===
print("=" * 60)
print("HYPERLIQUID STATUS")
print("=" * 60)

info = Info(constants.MAINNET_API_URL, skip_ws=True)
state = info.user_state(DEPLOYER)
ms = state.get("marginSummary", {})
print(f"Account Value (USD): {ms.get('accountValue', 'N/A')}")
print(f"Total Margin Used:   {ms.get('totalMarginUsed', 'N/A')}")
print(f"Total NTL Position:  {ms.get('totalNtlPos', 'N/A')}")

positions = state.get("assetPositions", [])
if positions:
    for p in positions:
        pos = p["position"]
        coin = pos["coin"]
        szi = pos["szi"]
        upnl = pos["unrealizedPnl"]
        entry = pos.get("entryPx", "N/A")
        liq = pos.get("liquidationPx", "N/A")
        leverage = pos.get("leverage", {})
        print(f"\nPosition: {coin}")
        print(f"  Size: {szi}")
        print(f"  Entry: {entry}")
        print(f"  uPnL: {upnl}")
        print(f"  Liquidation: {liq}")
        print(f"  Leverage: {leverage}")
else:
    print("No open positions")

# Funding rate
meta = info.meta_and_asset_ctxs()
universe = meta[0]["universe"]
ctxs = meta[1]
for i, a in enumerate(universe):
    if a["name"] == "ETH":
        print(f"\nETH Funding Rate: {ctxs[i]['funding']}")
        print(f"ETH Mark Price:   {ctxs[i]['markPx']}")
        print(f"ETH Open Interest: {ctxs[i].get('openInterest', 'N/A')}")
        break

# === On-Chain Data ===
print("\n" + "=" * 60)
print("ON-CHAIN STATUS (Base)")
print("=" * 60)

if Web3:
    rpcs = [
        "https://base.llamarpc.com",
        "https://base.drpc.org",
        "https://1rpc.io/base",
        "https://mainnet.base.org",
    ]
    
    w3 = None
    for rpc in rpcs:
        try:
            _w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if _w3.is_connected():
                w3 = _w3
                print(f"Connected to: {rpc}")
                break
        except Exception:
            continue
    
    if w3:
        # ERC-4626 totalAssets
        vault_abi = [
            {"inputs": [], "name": "totalAssets", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
            {"inputs": [], "name": "totalSupply", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
        ]
        try:
            vault = w3.eth.contract(address=Web3.to_checksum_address(BASE_VAULT), abi=vault_abi)
            total_assets = vault.functions.totalAssets().call()
            total_supply = vault.functions.totalSupply().call()
            print(f"Vault totalAssets: {total_assets / 1e18:.6f} WETH")
            print(f"Vault totalSupply: {total_supply / 1e18:.6f} shares")
            if total_supply > 0:
                share_price = total_assets / total_supply
                print(f"Share Price: {share_price:.6f}")
        except Exception as e:
            print(f"Vault read error: {e}")
    else:
        print("Could not connect to any Base RPC")
else:
    print("web3 not available")

print("\n" + "=" * 60)
print("CHECK COMPLETE")
print("=" * 60)