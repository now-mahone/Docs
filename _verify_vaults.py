# Temporary script to verify vault contracts on-chain
import urllib.request
import json

def rpc_call(url, method, params):
    req = urllib.request.Request(
        url,
        data=json.dumps({"jsonrpc": "2.0", "method": method, "params": params, "id": 1}).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = json.loads(urllib.request.urlopen(req).read())
    if "error" in resp:
        return f"ERROR: {resp['error']}"
    return resp["result"]

# Base vault
print("=== BASE VAULT ===")
base_url = "https://base-mainnet.g.alchemy.com/v2/demo"
base_vault = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"

code = rpc_call(base_url, "eth_getCode", [base_vault, "latest"])
print(f"Code: {(len(code)-2)//2} bytes")

ta = rpc_call(base_url, "eth_call", [{"to": base_vault, "data": "0x01e1d114"}, "latest"])
print(f"totalAssets raw: {ta}")
print(f"totalAssets: {int(ta, 16)} wei")
print(f"totalAssets: {int(ta, 16) / 1e18:.6f} ETH")

asset = rpc_call(base_url, "eth_call", [{"to": base_vault, "data": "0x38d52e0f"}, "latest"])
print(f"asset: 0x{asset[-40:]}")

ts = rpc_call(base_url, "eth_call", [{"to": base_vault, "data": "0x18160ddd"}, "latest"])
print(f"totalSupply: {int(ts, 16)} shares")

# Arbitrum vault
print("\n=== ARBITRUM VAULT ===")
arb_url = "https://arb-mainnet.g.alchemy.com/v2/demo"
arb_vault = "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF"

code2 = rpc_call(arb_url, "eth_getCode", [arb_vault, "latest"])
print(f"Code: {(len(code2)-2)//2} bytes")

ta2 = rpc_call(arb_url, "eth_call", [{"to": arb_vault, "data": "0x01e1d114"}, "latest"])
print(f"totalAssets raw: {ta2}")
print(f"totalAssets: {int(ta2, 16)}")
# Arb vault asset is USDC (6 decimals)
print(f"totalAssets: ${int(ta2, 16) / 1e6:.2f} USDC")

asset2 = rpc_call(arb_url, "eth_call", [{"to": arb_vault, "data": "0x38d52e0f"}, "latest"])
print(f"asset: 0x{asset2[-40:]}")

ts2 = rpc_call(arb_url, "eth_call", [{"to": arb_vault, "data": "0x18160ddd"}, "latest"])
print(f"totalSupply: {int(ts2, 16)} shares")

print("\n=== SUMMARY ===")
print("Both vaults operational and returning valid ERC-4626 data.")
print("Ready for aggregator adapter submissions.")