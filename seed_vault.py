# Created: 2026-02-06
# Purpose: Seed KerneVault with WETH by swapping USDC → WETH on Uniswap V3 (Base)
# Usage:
#   python seed_vault.py                  # Dry run (shows plan, no txns)
#   python seed_vault.py --execute        # Execute the seeding transactions
#   python seed_vault.py --amount 100     # Swap $100 USDC (default: $150)

import os
import sys
import time
from web3 import Web3
from dotenv import load_dotenv

load_dotenv('bot/.env')

# =============================================================================
# CONFIGURATION
# =============================================================================

# Addresses (Base Mainnet)
USDC = Web3.to_checksum_address("0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913")
WETH = Web3.to_checksum_address("0x4200000000000000000000000000000000000006")
VAULT = Web3.to_checksum_address("0xDA9765F84208F8E94225889B2C9331DCe940fB20")
DEPLOYER = Web3.to_checksum_address("0x57D400cED462a01Ed51a5De038F204Df49690A99")

# Uniswap V3 SwapRouter02 on Base
UNISWAP_ROUTER = Web3.to_checksum_address("0x2626664c2603336E57B271c5C0b26F421741e481")

# Default: swap $150 USDC → WETH
DEFAULT_USDC_AMOUNT = 150  # dollars

# Slippage tolerance: 1% (conservative for small amounts on major pair)
SLIPPAGE_BPS = 100  # 1%

# USDC/WETH pool fee tier on Base Uniswap V3
POOL_FEE = 500  # 0.05% fee tier (most liquid for USDC/WETH)

# Multi-RPC
RPC_URLS = [
    "https://base.drpc.org",
    "https://1rpc.io/base",
    "https://base-mainnet.public.blastapi.io",
    "https://base.llamarpc.com",
    "https://mainnet.base.org",
]

# =============================================================================
# ABIs (minimal)
# =============================================================================

ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf",
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}],
     "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}],
     "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}],
     "stateMutability": "view", "type": "function"},
]

# Uniswap V3 SwapRouter02 - exactInputSingle
SWAP_ROUTER_ABI = [
    {
        "inputs": [{
            "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "fee", "type": "uint24"},
                {"name": "recipient", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "amountOutMinimum", "type": "uint256"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"},
            ],
            "name": "params",
            "type": "tuple",
        }],
        "name": "exactInputSingle",
        "outputs": [{"name": "amountOut", "type": "uint256"}],
        "stateMutability": "payable",
        "type": "function",
    },
]

# ERC-4626 Vault deposit
VAULT_ABI = [
    {"inputs": [{"name": "assets", "type": "uint256"}, {"name": "receiver", "type": "address"}],
     "name": "deposit", "outputs": [{"name": "shares", "type": "uint256"}],
     "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "assets", "type": "uint256"}], "name": "previewDeposit",
     "outputs": [{"name": "shares", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalAssets",
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "totalSupply",
     "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "paused",
     "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"},
]

# Uniswap V3 Quoter for price estimation
QUOTER_ADDRESS = Web3.to_checksum_address("0x3d4e44Eb1374240CE5F1B871ab261CD16335B76a")
QUOTER_ABI = [
    {
        "inputs": [{
            "components": [
                {"name": "tokenIn", "type": "address"},
                {"name": "tokenOut", "type": "address"},
                {"name": "amountIn", "type": "uint256"},
                {"name": "fee", "type": "uint24"},
                {"name": "sqrtPriceLimitX96", "type": "uint160"},
            ],
            "name": "params",
            "type": "tuple",
        }],
        "name": "quoteExactInputSingle",
        "outputs": [
            {"name": "amountOut", "type": "uint256"},
            {"name": "sqrtPriceX96After", "type": "uint160"},
            {"name": "initializedTicksCrossed", "type": "uint32"},
            {"name": "gasEstimate", "type": "uint256"},
        ],
        "stateMutability": "nonpayable",
        "type": "function",
    },
]


# =============================================================================
# HELPERS
# =============================================================================

def connect():
    """Connect to Base with multi-RPC fallback."""
    for rpc in RPC_URLS:
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 15}))
            if w3.is_connected():
                print(f"Connected via: {rpc}")
                return w3
        except Exception:
            continue
    print("ERROR: Failed to connect to any Base RPC")
    sys.exit(1)


def send_tx(w3, tx, label=""):
    """Sign and send a transaction, wait for receipt."""
    pk = os.getenv("PRIVATE_KEY") or os.getenv("STRATEGIST_PRIVATE_KEY")
    if not pk:
        print("ERROR: No PRIVATE_KEY in bot/.env")
        sys.exit(1)

    # Ensure basics
    tx["from"] = DEPLOYER
    tx["nonce"] = w3.eth.get_transaction_count(DEPLOYER)
    tx["chainId"] = 8453

    # Remove legacy gasPrice if EIP-1559 fields present (Base is EIP-1559)
    if "gasPrice" in tx:
        del tx["gasPrice"]

    # Set EIP-1559 gas if not already set by build_transaction
    if "maxFeePerGas" not in tx:
        base_fee = w3.eth.get_block("latest").baseFeePerGas or 100000000
        tx["maxFeePerGas"] = int(base_fee * 2)
        tx["maxPriorityFeePerGas"] = int(base_fee * 0.1) or 1000000

    # Estimate gas
    try:
        gas_est = w3.eth.estimate_gas(tx)
        tx["gas"] = int(gas_est * 1.3)  # 30% buffer
    except Exception as e:
        print(f"  ⚠️  Gas estimation failed for {label}: {e}")
        tx["gas"] = 300000  # fallback

    # Sign and send
    signed = w3.eth.account.sign_transaction(tx, pk)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"  📤 {label} TX sent: {tx_hash.hex()}")

    # Wait for receipt
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt.status == 1:
        print(f"  ✅ {label} confirmed in block {receipt.blockNumber} (gas used: {receipt.gasUsed})")
    else:
        print(f"  ❌ {label} REVERTED in block {receipt.blockNumber}")
        sys.exit(1)

    return receipt


def get_weth_quote(w3, usdc_amount_raw):
    """Get expected WETH output from Uniswap V3 Quoter."""
    try:
        quoter = w3.eth.contract(address=QUOTER_ADDRESS, abi=QUOTER_ABI)
        # Use eth_call to simulate (quoter reverts with the result)
        result = quoter.functions.quoteExactInputSingle({
            "tokenIn": USDC,
            "tokenOut": WETH,
            "amountIn": usdc_amount_raw,
            "fee": POOL_FEE,
            "sqrtPriceLimitX96": 0,
        }).call()
        return result[0]  # amountOut
    except Exception as e:
        print(f"  ⚠️  Quoter call failed: {str(e)[:100]}")
        # Fallback: estimate at $2,800/ETH
        usdc_dollars = usdc_amount_raw / 1e6
        return int((usdc_dollars / 2800) * 1e18)


# =============================================================================
# MAIN
# =============================================================================

def main():
    execute = "--execute" in sys.argv
    
    # Parse amount
    usdc_amount = DEFAULT_USDC_AMOUNT
    for i, arg in enumerate(sys.argv):
        if arg == "--amount" and i + 1 < len(sys.argv):
            usdc_amount = float(sys.argv[i + 1])

    usdc_raw = int(usdc_amount * 1e6)  # USDC has 6 decimals

    print("=" * 60)
    print("  KERNE VAULT SEEDING SCRIPT")
    print(f"  Mode: {'🔴 LIVE EXECUTION' if execute else '🟡 DRY RUN (add --execute to run)'}")
    print("=" * 60)

    w3 = connect()

    # --- Pre-flight checks ---
    usdc_contract = w3.eth.contract(address=USDC, abi=ERC20_ABI)
    weth_contract = w3.eth.contract(address=WETH, abi=ERC20_ABI)
    vault_contract = w3.eth.contract(address=VAULT, abi=VAULT_ABI)

    usdc_balance = usdc_contract.functions.balanceOf(DEPLOYER).call()
    weth_balance = weth_contract.functions.balanceOf(DEPLOYER).call()
    eth_balance = w3.eth.get_balance(DEPLOYER)
    is_paused = vault_contract.functions.paused().call()

    print(f"\n  Deployer: {DEPLOYER}")
    print(f"  USDC Balance:  {usdc_balance / 1e6:.2f} USDC")
    print(f"  WETH Balance:  {weth_balance / 1e18:.6f} WETH")
    print(f"  ETH Balance:   {eth_balance / 1e18:.6f} ETH (gas)")
    print(f"  Vault Paused:  {is_paused}")

    if is_paused:
        print("\n  ❌ ABORT: Vault is paused!")
        sys.exit(1)

    if usdc_balance < usdc_raw:
        print(f"\n  ❌ ABORT: Insufficient USDC. Have {usdc_balance / 1e6:.2f}, need {usdc_amount:.2f}")
        sys.exit(1)

    if eth_balance < 0.0005 * 1e18:
        print(f"\n  ❌ ABORT: Insufficient ETH for gas. Have {eth_balance / 1e18:.6f}, need ~0.001")
        sys.exit(1)

    # --- Get quote ---
    print(f"\n  Swap Plan: {usdc_amount:.2f} USDC → WETH via Uniswap V3 (fee: {POOL_FEE/10000:.2f}%)")
    expected_weth = get_weth_quote(w3, usdc_raw)
    min_weth = int(expected_weth * (10000 - SLIPPAGE_BPS) / 10000)

    print(f"  Expected WETH: {expected_weth / 1e18:.6f} WETH")
    print(f"  Min WETH (1% slippage): {min_weth / 1e18:.6f} WETH")
    eth_price = usdc_amount / (expected_weth / 1e18) if expected_weth > 0 else 0
    print(f"  Implied ETH Price: ${eth_price:,.2f}")

    # Preview vault deposit
    preview_shares = vault_contract.functions.previewDeposit(expected_weth).call()
    print(f"\n  Vault Deposit: {expected_weth / 1e18:.6f} WETH → {preview_shares / 1e18:.6f} shares")

    remaining_usdc = (usdc_balance - usdc_raw) / 1e6
    print(f"  Remaining USDC after swap: {remaining_usdc:.2f} USDC")
    print(f"  (Available for HL bridging to open matching short)")

    if not execute:
        print("\n" + "=" * 60)
        print("  🟡 DRY RUN COMPLETE — No transactions executed.")
        print("  Run with --execute to perform the seeding.")
        print("=" * 60)
        return

    # =========================================================================
    # EXECUTION
    # =========================================================================
    print("\n" + "=" * 60)
    print("  🔴 EXECUTING LIVE TRANSACTIONS...")
    print("=" * 60)

    # Step 1: Approve USDC for Uniswap Router
    print("\n  [1/4] Approving USDC for Uniswap Router...")
    allowance = usdc_contract.functions.allowance(DEPLOYER, UNISWAP_ROUTER).call()
    if allowance < usdc_raw:
        approve_tx = usdc_contract.functions.approve(UNISWAP_ROUTER, usdc_raw).build_transaction({"from": DEPLOYER})
        send_tx(w3, approve_tx, "USDC Approve")
    else:
        print(f"  ✅ Already approved ({allowance / 1e6:.2f} USDC)")

    time.sleep(1)

    # Step 2: Swap USDC → WETH
    print(f"\n  [2/4] Swapping {usdc_amount:.2f} USDC → WETH...")
    router = w3.eth.contract(address=UNISWAP_ROUTER, abi=SWAP_ROUTER_ABI)
    swap_tx = router.functions.exactInputSingle({
        "tokenIn": USDC,
        "tokenOut": WETH,
        "fee": POOL_FEE,
        "recipient": DEPLOYER,
        "amountIn": usdc_raw,
        "amountOutMinimum": min_weth,
        "sqrtPriceLimitX96": 0,
    }).build_transaction({"from": DEPLOYER, "value": 0})
    swap_receipt = send_tx(w3, swap_tx, "USDC→WETH Swap")

    time.sleep(1)

    # Check new WETH balance
    new_weth = weth_contract.functions.balanceOf(DEPLOYER).call()
    weth_received = new_weth - weth_balance
    print(f"  WETH received: {weth_received / 1e18:.6f} WETH")

    # Step 3: Approve WETH for Vault
    print(f"\n  [3/4] Approving WETH for Vault...")
    weth_allowance = weth_contract.functions.allowance(DEPLOYER, VAULT).call()
    if weth_allowance < new_weth:
        approve_weth_tx = weth_contract.functions.approve(VAULT, new_weth).build_transaction({"from": DEPLOYER})
        send_tx(w3, approve_weth_tx, "WETH Approve")
    else:
        print(f"  ✅ Already approved")

    time.sleep(1)

    # Step 4: Deposit WETH into Vault
    print(f"\n  [4/4] Depositing {new_weth / 1e18:.6f} WETH into KerneVault...")
    deposit_tx = vault_contract.functions.deposit(new_weth, DEPLOYER).build_transaction({"from": DEPLOYER})
    deposit_receipt = send_tx(w3, deposit_tx, "Vault Deposit")

    # --- Post-seeding verification ---
    time.sleep(2)
    final_total_assets = vault_contract.functions.totalAssets().call()
    final_total_supply = vault_contract.functions.totalSupply().call()
    final_usdc = usdc_contract.functions.balanceOf(DEPLOYER).call()
    final_eth = w3.eth.get_balance(DEPLOYER)

    print("\n" + "=" * 60)
    print("  ✅ VAULT SEEDING COMPLETE")
    print("=" * 60)
    print(f"  Vault Total Assets: {final_total_assets / 1e18:.6f} WETH")
    print(f"  Vault Total Supply: {final_total_supply / 1e18:.6f} shares")
    print(f"  Remaining USDC:     {final_usdc / 1e6:.2f} USDC")
    print(f"  Remaining ETH:      {final_eth / 1e18:.6f} ETH (gas)")
    print(f"\n  TVL established! Ready for aggregator submissions.")
    print(f"  Next: Bridge ${final_usdc / 1e6:.0f} USDC to Hyperliquid for matching short.")
    print("=" * 60)


if __name__ == "__main__":
    main()