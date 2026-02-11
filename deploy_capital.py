# Deploy Capital — Optimal Allocation Script
# Created: 2026-02-07
# 
# Executes the following plan:
#   Step 1: Swap ~$119 USDC -> WETH on Base (via Li.Fi)
#   Step 2: Deposit WETH into KerneVault (establish TVL)
#   Step 3: Bridge ~$87 USDC from Base -> Arbitrum (via Li.Fi)
#   Step 4: Deposit USDC from Arbitrum to Hyperliquid
#
# This creates a balanced delta-neutral position:
#   Spot (Vault):  ~$119 in WETH
#   Short (HL):    ~$119 in USDC margin ($32.20 existing + $87 new)

import os
import sys
import time
import json
import requests
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

# Load environment
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", ".env"))

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    print("ERROR: PRIVATE_KEY not found in bot/.env")
    sys.exit(1)

from eth_account import Account
WALLET = Account.from_key(PRIVATE_KEY).address
print(f"Wallet: {WALLET}")

# ABIs
ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"decimals","outputs":[{"name":"","type":"uint8"}],"type":"function"},
    {"inputs":[{"name":"spender","type":"address"},{"name":"amount","type":"uint256"}],"name":"approve","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[{"name":"owner","type":"address"},{"name":"spender","type":"address"}],"name":"allowance","outputs":[{"name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
]

VAULT_ABI = [
    {"inputs":[{"name":"assets","type":"uint256"},{"name":"receiver","type":"address"}],"name":"deposit","outputs":[{"name":"shares","type":"uint256"}],"stateMutability":"nonpayable","type":"function"},
    {"constant":True,"inputs":[],"name":"totalAssets","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"totalSupply","outputs":[{"name":"","type":"uint256"}],"type":"function"},
    {"constant":True,"inputs":[],"name":"asset","outputs":[{"name":"","type":"address"}],"type":"function"},
]

# Addresses
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
BASE_WETH = "0x4200000000000000000000000000000000000006"
ARB_USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
VAULT_ADDR = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"
HL_BRIDGE = "0x2Df1c51E09a42Ad01097321978c7035100396630"

LIFI_API = "https://li.quest/v1"

# ============================================================

DRY_RUN = "--dry-run" in sys.argv
if DRY_RUN:
    print("\n*** DRY RUN MODE — No transactions will be executed ***\n")

def get_w3(rpc_url):
    w3 = Web3(Web3.HTTPProvider(rpc_url, request_kwargs={"timeout": 15}))
    w3.middleware_onion.inject(geth_poa_middleware, layer=0)
    return w3

def get_eth_price():
    try:
        r = requests.get("https://api.coingecko.com/api/v3/simple/price",
                         params={"ids":"ethereum","vs_currencies":"usd"}, timeout=5)
        return r.json()["ethereum"]["usd"]
    except:
        return 2700.0

def send_tx(w3, tx_dict, label="TX"):
    """Sign and send a transaction."""
    if DRY_RUN:
        print(f"  [DRY RUN] Would send {label}")
        return "0x_dry_run"
    
    signed = w3.eth.account.sign_transaction(tx_dict, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    hash_hex = tx_hash.hex()
    print(f"  {label} sent: {hash_hex}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 1:
        print(f"  {label} CONFIRMED (gas used: {receipt.gasUsed})")
    else:
        print(f"  {label} FAILED!")
        raise Exception(f"{label} reverted")
    return hash_hex

def approve_if_needed(w3, token_addr, spender, amount_raw, chain_id, label="Token"):
    """Approve token spending if allowance insufficient."""
    token = w3.eth.contract(address=Web3.to_checksum_address(token_addr), abi=ERC20_ABI)
    allowance = token.functions.allowance(
        Web3.to_checksum_address(WALLET),
        Web3.to_checksum_address(spender)
    ).call()
    
    if allowance >= amount_raw:
        print(f"  {label} already approved (allowance: {allowance})")
        return
    
    print(f"  Approving {label} for {spender}...")
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(WALLET))
    
    tx = token.functions.approve(
        Web3.to_checksum_address(spender), 2**256 - 1
    ).build_transaction({
        "from": WALLET,
        "nonce": nonce,
        "chainId": chain_id,
    })
    
    # Gas pricing
    try:
        fee_history = w3.eth.fee_history(1, "latest")
        base_fee = fee_history["baseFeePerGas"][-1]
        tx["maxPriorityFeePerGas"] = w3.to_wei(0.001, "gwei")
        tx["maxFeePerGas"] = int(base_fee * 1.5) + tx["maxPriorityFeePerGas"]
    except:
        tx["gasPrice"] = w3.eth.gas_price
    
    send_tx(w3, tx, f"{label} Approve")
    time.sleep(2)  # Wait for nonce to update

def lifi_swap(from_chain_id, to_chain_id, from_token, to_token, amount_raw, slippage=0.005):
    """Get Li.Fi quote and return the transaction data."""
    params = {
        "fromChain": from_chain_id,
        "toChain": to_chain_id,
        "fromToken": from_token,
        "toToken": to_token,
        "fromAmount": str(amount_raw),
        "fromAddress": WALLET,
        "slippage": slippage,
    }
    
    print(f"  Fetching Li.Fi quote...")
    resp = requests.get(f"{LIFI_API}/quote", params=params, timeout=30)
    if resp.status_code != 200:
        print(f"  Li.Fi error ({resp.status_code}): {resp.text[:300]}")
        raise Exception(f"Li.Fi quote failed: {resp.status_code}")
    
    quote = resp.json()
    
    # Parse estimate
    estimate = quote.get("estimate", {})
    to_amount_raw = estimate.get("toAmount", "0")
    to_token_data = quote.get("action", {}).get("toToken", {})
    to_decimals = to_token_data.get("decimals", 18)
    to_amount = float(to_amount_raw) / (10 ** to_decimals)
    to_symbol = to_token_data.get("symbol", "?")
    
    gas_costs = estimate.get("gasCosts", [])
    gas_usd = float(gas_costs[0].get("amountUSD", "0")) if gas_costs else 0
    
    tool = quote.get("toolDetails", {}).get("name", quote.get("tool", "?"))
    print(f"  Route: {tool} | Output: {to_amount:.6f} {to_symbol} | Gas: ${gas_usd:.4f}")
    
    return quote

def execute_lifi_quote(w3, quote, chain_id):
    """Execute a Li.Fi quote transaction."""
    tx_req = quote["transactionRequest"]
    
    # Handle approval first
    from_token = quote.get("action", {}).get("fromToken", {}).get("address", "")
    if from_token and from_token.lower() != "0x0000000000000000000000000000000000000000":
        amount_raw = int(quote["action"]["fromAmount"])
        approve_if_needed(w3, from_token, tx_req["to"], amount_raw, chain_id, "Swap Token")
    
    def to_int(val):
        if isinstance(val, str) and val.startswith("0x"):
            return int(val, 16)
        return int(val)
    
    # Use 'pending' to avoid nonce conflicts with just-confirmed approvals
    nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(WALLET), "pending")
    
    tx = {
        "from": WALLET,
        "to": Web3.to_checksum_address(tx_req["to"]),
        "data": tx_req["data"],
        "value": to_int(tx_req.get("value", 0)),
        "nonce": nonce,
        "chainId": chain_id,
    }
    
    gas_limit = to_int(tx_req.get("gasLimit", 500000))
    tx["gas"] = int(gas_limit * 1.3)
    
    try:
        fee_history = w3.eth.fee_history(1, "latest")
        base_fee = fee_history["baseFeePerGas"][-1]
        tx["maxPriorityFeePerGas"] = w3.to_wei(0.1, "gwei")
        tx["maxFeePerGas"] = int(base_fee * 2.0) + tx["maxPriorityFeePerGas"]
    except:
        tx["gasPrice"] = int(w3.eth.gas_price * 1.5)
    
    return send_tx(w3, tx, "Li.Fi Swap/Bridge")


# ============================================================
# MAIN EXECUTION
# ============================================================

def main():
    eth_price = get_eth_price()
    print(f"\nETH Price: ${eth_price:,.2f}")
    
    # Connect to Base
    base_rpc = os.getenv("BASE_RPC_URL", os.getenv("RPC_URL", "https://base.drpc.org"))
    # Handle comma-separated RPCs
    if "," in base_rpc:
        base_rpc = base_rpc.split(",")[0].strip()
    w3_base = get_w3(base_rpc)
    print(f"Connected to Base (chain {w3_base.eth.chain_id})")
    
    # Check USDC balance
    usdc = w3_base.eth.contract(address=Web3.to_checksum_address(BASE_USDC), abi=ERC20_ABI)
    usdc_bal = usdc.functions.balanceOf(Web3.to_checksum_address(WALLET)).call()
    usdc_amt = usdc_bal / 1e6
    print(f"USDC on Base: {usdc_amt:.2f}")
    
    eth_bal = w3_base.eth.get_balance(Web3.to_checksum_address(WALLET))
    eth_amt = float(Web3.from_wei(eth_bal, "ether"))
    print(f"ETH on Base: {eth_amt:.6f} (${eth_amt * eth_price:.2f})")
    
    # Check Hyperliquid balance
    try:
        hl_resp = requests.post("https://api.hyperliquid.xyz/info",
                                json={"type":"clearinghouseState","user":WALLET}, timeout=10)
        hl_data = hl_resp.json()
        hl_equity = float(hl_data.get("marginSummary", {}).get("accountValue", 0))
    except:
        hl_equity = 32.20  # fallback from last scan
    print(f"Hyperliquid equity: ${hl_equity:.2f}")
    
    # Calculate total and optimal allocation
    total = usdc_amt + (eth_amt * eth_price) + hl_equity
    print(f"\nTotal deployable capital: ${total:,.2f}")
    
    # Dynamic allocation decision:
    # For basis trading, we want equal $ on each side.
    # Reserve $5 for gas, split the rest equally between vault and HL.
    gas_reserve = 5.0
    deployable = usdc_amt - gas_reserve  # Only USDC is moveable
    
    # Target: vault and HL should be equal
    # HL already has $hl_equity, so:
    # vault_target = (deployable + hl_equity) / 2
    # hl_additional = vault_target - hl_equity
    vault_target = (deployable + hl_equity) / 2
    hl_additional = vault_target - hl_equity
    
    # Ensure non-negative and within bounds
    if hl_additional < 0:
        hl_additional = 0
        vault_target = deployable
    
    swap_amount = round(vault_target, 2)
    bridge_amount = round(hl_additional, 2)
    
    print(f"\n{'='*60}")
    print(f"  OPTIMAL ALLOCATION PLAN")
    print(f"{'='*60}")
    print(f"  Gas reserve:        ${gas_reserve:.2f} USDC (kept on Base)")
    print(f"  Step 1: Swap        ${swap_amount:.2f} USDC -> WETH on Base")
    print(f"  Step 2: Deposit     WETH into KerneVault (TVL: ~${swap_amount:.0f})")
    print(f"  Step 3: Bridge      ${bridge_amount:.2f} USDC Base -> Arbitrum")
    print(f"  Step 4: Deposit     ${bridge_amount:.2f} USDC Arbitrum -> Hyperliquid")
    print(f"  Result: Vault ~${swap_amount:.0f} | HL ~${hl_equity + bridge_amount:.0f}")
    print(f"{'='*60}")
    
    if usdc_amt < 10:
        print("\nERROR: Insufficient USDC to proceed.")
        return
    
    # Sanity check
    if swap_amount + bridge_amount + gas_reserve > usdc_amt + 0.5:
        print(f"\nERROR: Plan exceeds available USDC ({usdc_amt:.2f})")
        return
    
    if DRY_RUN:
        print("\n*** DRY RUN COMPLETE — No transactions executed ***")
        return
    
    input("\nPress ENTER to execute (or Ctrl+C to abort)...")
    
    # ============================================================
    # STEP 1: Swap USDC -> WETH on Base via Li.Fi
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  STEP 1: Swap {swap_amount:.2f} USDC -> WETH on Base")
    print(f"{'='*60}")
    
    swap_raw = int(swap_amount * 1e6)
    quote = lifi_swap(
        from_chain_id=8453,
        to_chain_id=8453,
        from_token=BASE_USDC,
        to_token=BASE_WETH,
        amount_raw=swap_raw,
    )
    tx_hash_1 = execute_lifi_quote(w3_base, quote, 8453)
    print(f"  Explorer: https://basescan.org/tx/{tx_hash_1}")
    time.sleep(3)
    
    # Check new WETH balance
    weth = w3_base.eth.contract(address=Web3.to_checksum_address(BASE_WETH), abi=ERC20_ABI)
    weth_bal = weth.functions.balanceOf(Web3.to_checksum_address(WALLET)).call()
    weth_amt = weth_bal / 1e18
    print(f"  WETH received: {weth_amt:.6f} (${weth_amt * eth_price:.2f})")
    
    # ============================================================
    # STEP 2: Deposit WETH into KerneVault
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  STEP 2: Deposit {weth_amt:.6f} WETH into KerneVault")
    print(f"{'='*60}")
    
    vault = w3_base.eth.contract(address=Web3.to_checksum_address(VAULT_ADDR), abi=VAULT_ABI)
    
    # Approve WETH for vault
    approve_if_needed(w3_base, BASE_WETH, VAULT_ADDR, weth_bal, 8453, "WETH")
    
    # Deposit
    nonce = w3_base.eth.get_transaction_count(Web3.to_checksum_address(WALLET), "pending")
    deposit_tx = vault.functions.deposit(
        weth_bal,
        Web3.to_checksum_address(WALLET)
    ).build_transaction({
        "from": WALLET,
        "nonce": nonce,
        "chainId": 8453,
    })
    
    try:
        fee_history = w3_base.eth.fee_history(1, "latest")
        base_fee = fee_history["baseFeePerGas"][-1]
        deposit_tx["maxPriorityFeePerGas"] = w3_base.to_wei(0.001, "gwei")
        deposit_tx["maxFeePerGas"] = int(base_fee * 1.5) + deposit_tx["maxPriorityFeePerGas"]
    except:
        deposit_tx["gasPrice"] = w3_base.eth.gas_price
    
    tx_hash_2 = send_tx(w3_base, deposit_tx, "Vault Deposit")
    print(f"  Explorer: https://basescan.org/tx/{tx_hash_2}")
    
    # Verify vault state
    time.sleep(3)
    ta = vault.functions.totalAssets().call()
    ts = vault.functions.totalSupply().call()
    print(f"  Vault totalAssets: {ta/1e18:.6f} WETH (${ta/1e18 * eth_price:.2f})")
    print(f"  Vault totalSupply: {ts/1e18:.6f} shares")
    
    # ============================================================
    # STEP 3: Bridge USDC from Base to Arbitrum
    # ============================================================
    if bridge_amount > 1.0:
        print(f"\n{'='*60}")
        print(f"  STEP 3: Bridge {bridge_amount:.2f} USDC Base -> Arbitrum")
        print(f"{'='*60}")
        
        bridge_raw = int(bridge_amount * 1e6)
        quote_bridge = lifi_swap(
            from_chain_id=8453,
            to_chain_id=42161,
            from_token=BASE_USDC,
            to_token=ARB_USDC,
            amount_raw=bridge_raw,
        )
        tx_hash_3 = execute_lifi_quote(w3_base, quote_bridge, 8453)
        print(f"  Explorer: https://basescan.org/tx/{tx_hash_3}")
        
        print("  Waiting 45s for bridge to settle on Arbitrum...")
        time.sleep(45)
        
        # ============================================================
        # STEP 4: Deposit USDC from Arbitrum to Hyperliquid
        # ============================================================
        print(f"\n{'='*60}")
        print(f"  STEP 4: Deposit USDC to Hyperliquid via Arbitrum bridge")
        print(f"{'='*60}")
        
        arb_rpc = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
        if "," in arb_rpc:
            arb_rpc = arb_rpc.split(",")[0].strip()
        w3_arb = get_w3(arb_rpc)
        
        arb_usdc = w3_arb.eth.contract(address=Web3.to_checksum_address(ARB_USDC), abi=ERC20_ABI)
        arb_usdc_bal = arb_usdc.functions.balanceOf(Web3.to_checksum_address(WALLET)).call()
        arb_usdc_amt = arb_usdc_bal / 1e6
        print(f"  USDC on Arbitrum: {arb_usdc_amt:.2f}")
        
        if arb_usdc_amt < 1.0:
            print("  WARNING: Bridge may still be processing. Check Arbitrum balance manually.")
        else:
            # Approve USDC for HL bridge
            approve_if_needed(w3_arb, ARB_USDC, HL_BRIDGE, arb_usdc_bal, 42161, "USDC (Arb)")
            
            # Transfer USDC to HL bridge address
            nonce_arb = w3_arb.eth.get_transaction_count(Web3.to_checksum_address(WALLET))
            hl_deposit_tx = arb_usdc.functions.transfer(
                Web3.to_checksum_address(HL_BRIDGE), arb_usdc_bal
            ).build_transaction({
                "from": WALLET,
                "nonce": nonce_arb,
                "chainId": 42161,
                "gasPrice": w3_arb.eth.gas_price,
            })
            
            tx_hash_4 = send_tx(w3_arb, hl_deposit_tx, "HL Deposit")
            print(f"  Explorer: https://arbiscan.io/tx/{tx_hash_4}")
            print(f"  Hyperliquid deposit processing... (may take 1-5 minutes)")
    else:
        print(f"\n  Skipping bridge/HL deposit (amount too small: ${bridge_amount:.2f})")
    
    # ============================================================
    # SUMMARY
    # ============================================================
    print(f"\n{'='*60}")
    print(f"  DEPLOYMENT COMPLETE")
    print(f"{'='*60}")
    print(f"  Vault TVL:     ~${swap_amount:.0f} in WETH")
    print(f"  Hyperliquid:   ~${hl_equity + bridge_amount:.0f} margin")
    print(f"  Gas Reserve:   ~${gas_reserve:.0f} USDC on Base")
    print(f"  Next Step:     Run basis trade: python bot/main.py --seed-only")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()