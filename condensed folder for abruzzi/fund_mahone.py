# Created: 2026-02-12
"""
Withdraw USDC from ZIN Pool, swap to ETH, bridge to Arbitrum, and send $10 to Mahone.
"""
import os
import sys
import json
import requests
from web3 import Web3
from dotenv import load_dotenv

load_dotenv("bot/.env")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
BOT_ADDRESS = "0x57D400cED462a01Ed51a5De038F204Df49690A99"
MAHONE_ADDR = "0x8b54AA4fc3aaDCD101084BBF2a875c47537090E5"

# Contracts
ZIN_POOL_BASE = "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7"
USDC_BASE = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
WETH_BASE = "0x4200000000000000000000000000000000000006"

# RPCs
BASE_RPC = "https://mainnet.base.org"
ARB_RPC = os.getenv("ARB_RPC_URL", "https://arb1.arbitrum.io/rpc")

# ABIs
ERC20_ABI = [
    {"inputs": [{"name": "account", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "decimals", "outputs": [{"name": "", "type": "uint8"}], "stateMutability": "view", "type": "function"}
]

ZIN_ABI = [
    {"inputs": [{"name": "token", "type": "address"}], "name": "withdrawProfit", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "role", "type": "bytes32"}, {"name": "account", "type": "address"}], "name": "hasRole", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "view", "type": "function"}
]

def main():
    w3_base = Web3(Web3.HTTPProvider(BASE_RPC))
    w3_arb = Web3(Web3.HTTPProvider(ARB_RPC))
    
    account = w3_base.eth.account.from_key(PRIVATE_KEY)
    print(f"Bot Address: {account.address}")
    
    # Check ZIN Pool USDC balance
    usdc_contract = w3_base.eth.contract(address=Web3.to_checksum_address(USDC_BASE), abi=ERC20_ABI)
    zin_contract = w3_base.eth.contract(address=Web3.to_checksum_address(ZIN_POOL_BASE), abi=ZIN_ABI)
    
    zin_usdc_balance = usdc_contract.functions.balanceOf(Web3.to_checksum_address(ZIN_POOL_BASE)).call()
    print(f"ZIN Pool USDC Balance: {zin_usdc_balance / 1e6:.2f}")
    
    if zin_usdc_balance < 10e6:  # Less than $10
        print("ERROR: Not enough USDC in ZIN Pool")
        sys.exit(1)
    
    # Check MANAGER_ROLE
    MANAGER_ROLE = Web3.keccak(text="MANAGER_ROLE")
    has_role = zin_contract.functions.hasRole(MANAGER_ROLE, account.address).call()
    print(f"Has MANAGER_ROLE: {has_role}")
    
    if not has_role:
        print("ERROR: Bot does not have MANAGER_ROLE on ZIN Pool")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 1: Withdraw USDC from ZIN Pool")
    print("=" * 60)
    
    # Withdraw profit
    nonce = w3_base.eth.get_transaction_count(account.address)
    tx = zin_contract.functions.withdrawProfit(Web3.to_checksum_address(USDC_BASE)).build_transaction({
        'from': account.address,
        'nonce': nonce,
        'gas': 100000,
        'gasPrice': w3_base.eth.gas_price,
        'chainId': w3_base.eth.chain_id
    })
    
    signed_tx = w3_base.eth.account.sign_transaction(tx, PRIVATE_KEY)
    tx_hash = w3_base.eth.send_raw_transaction(signed_tx.rawTransaction)
    print(f"Withdraw TX: {tx_hash.hex()}")
    receipt = w3_base.eth.wait_for_transaction_receipt(tx_hash)
    
    if receipt.status != 1:
        print("ERROR: Withdraw failed")
        sys.exit(1)
    
    print("SUCCESS: USDC withdrawn from ZIN Pool")
    
    # Check new balance
    bot_usdc = usdc_contract.functions.balanceOf(account.address).call()
    print(f"Bot USDC Balance: {bot_usdc / 1e6:.2f}")
    
    print("\n" + "=" * 60)
    print("STEP 2: Swap USDC to ETH via Li.Fi")
    print("=" * 60)
    
    # Get ETH price
    try:
        resp = requests.get("https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd", timeout=10)
        eth_price = resp.json()["ethereum"]["usd"]
        print(f"ETH Price: ${eth_price}")
    except:
        eth_price = 2700
        print(f"ETH Price: ${eth_price} (fallback)")
    
    # We need $10 + gas for bridge (~$2) = $12 worth
    usdc_to_swap = min(12.0, bot_usdc / 1e6)
    print(f"Swapping ${usdc_to_swap} USDC to ETH...")
    
    # Get Li.Fi quote for USDC -> ETH on Base
    params = {
        "fromChain": 8453,
        "toChain": 8453,
        "fromToken": USDC_BASE,
        "toToken": "0x0000000000000000000000000000000000000000",  # native ETH
        "fromAmount": str(int(usdc_to_swap * 1e6)),
        "fromAddress": account.address,
        "slippage": 0.01
    }
    
    try:
        resp = requests.get("https://li.quest/v1/quote", params=params, timeout=30)
        quote = resp.json()
        estimate = quote.get("estimate", {})
        to_amount = int(estimate.get("toAmount", 0)) / 1e18
        print(f"Expected ETH: {to_amount:.6f}")
        
        # Execute swap
        tx_req = quote["transactionRequest"]
        swap_tx = {
            'from': account.address,
            'to': Web3.to_checksum_address(tx_req["to"]),
            'data': tx_req["data"],
            'value': int(tx_req.get("value", 0), 16) if isinstance(tx_req.get("value", 0), str) else int(tx_req.get("value", 0)),
            'nonce': w3_base.eth.get_transaction_count(account.address),
            'gas': int(tx_req.get("gasLimit", 300000), 16) if isinstance(tx_req.get("gasLimit", 300000), str) else int(tx_req.get("gasLimit", 300000)),
            'chainId': w3_base.eth.chain_id
        }
        
        # Set gas price
        try:
            fee_history = w3_base.eth.fee_history(1, "latest")
            base_fee = fee_history["baseFeePerGas"][-1]
            swap_tx["maxPriorityFeePerGas"] = w3_base.to_wei(0.001, "gwei")
            swap_tx["maxFeePerGas"] = int(base_fee * 1.5) + swap_tx["maxPriorityFeePerGas"]
        except:
            swap_tx["gasPrice"] = w3_base.eth.gas_price
        
        # Approve USDC first
        usdc_abi_full = [
            {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"}
        ]
        usdc_full = w3_base.eth.contract(address=Web3.to_checksum_address(USDC_BASE), abi=usdc_abi_full)
        
        approve_tx = usdc_full.functions.approve(
            Web3.to_checksum_address(tx_req["to"]),
            int(usdc_to_swap * 1e6)
        ).build_transaction({
            'from': account.address,
            'nonce': w3_base.eth.get_transaction_count(account.address),
            'gas': 50000,
            'gasPrice': w3_base.eth.gas_price,
            'chainId': w3_base.eth.chain_id
        })
        
        signed_approve = w3_base.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
        approve_hash = w3_base.eth.send_raw_transaction(signed_approve.rawTransaction)
        print(f"Approve TX: {approve_hash.hex()}")
        w3_base.eth.wait_for_transaction_receipt(approve_hash)
        
        # Execute swap
        signed_swap = w3_base.eth.account.sign_transaction(swap_tx, PRIVATE_KEY)
        swap_hash = w3_base.eth.send_raw_transaction(signed_swap.rawTransaction)
        print(f"Swap TX: {swap_hash.hex()}")
        swap_receipt = w3_base.eth.wait_for_transaction_receipt(swap_hash)
        
        if swap_receipt.status != 1:
            print("ERROR: Swap failed")
            sys.exit(1)
        
        print("SUCCESS: USDC swapped to ETH")
        
    except Exception as e:
        print(f"Li.Fi swap failed: {e}")
        print("Trying alternative approach...")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 3: Bridge ETH from Base to Arbitrum")
    print("=" * 60)
    
    # Check ETH balance
    eth_balance = w3_base.eth.get_balance(account.address)
    print(f"Bot ETH Balance: {eth_balance / 1e18:.6f}")
    
    if eth_balance < w3_base.to_wei(0.005, 'ether'):
        print("ERROR: Not enough ETH to bridge")
        sys.exit(1)
    
    # Bridge using Li.Fi
    bridge_amount_eth = min(eth_balance / 1e18 - 0.001, 0.006)  # Leave some for gas
    bridge_amount_wei = int(bridge_amount_eth * 1e18)
    
    print(f"Bridging {bridge_amount_eth:.6f} ETH to Arbitrum...")
    
    bridge_params = {
        "fromChain": 8453,
        "toChain": 42161,
        "fromToken": "0x0000000000000000000000000000000000000000",
        "toToken": "0x0000000000000000000000000000000000000000",
        "fromAmount": str(bridge_amount_wei),
        "fromAddress": account.address,
        "slippage": 0.01
    }
    
    try:
        resp = requests.get("https://li.quest/v1/quote", params=bridge_params, timeout=30)
        bridge_quote = resp.json()
        
        bridge_tx_req = bridge_quote["transactionRequest"]
        bridge_tx = {
            'from': account.address,
            'to': Web3.to_checksum_address(bridge_tx_req["to"]),
            'data': bridge_tx_req["data"],
            'value': int(bridge_tx_req.get("value", 0), 16) if isinstance(bridge_tx_req.get("value", 0), str) else int(bridge_tx_req.get("value", 0)),
            'nonce': w3_base.eth.get_transaction_count(account.address),
            'gas': int(bridge_tx_req.get("gasLimit", 500000), 16) if isinstance(bridge_tx_req.get("gasLimit", 500000), str) else int(bridge_tx_req.get("gasLimit", 500000)),
            'chainId': w3_base.eth.chain_id
        }
        
        try:
            fee_history = w3_base.eth.fee_history(1, "latest")
            base_fee = fee_history["baseFeePerGas"][-1]
            bridge_tx["maxPriorityFeePerGas"] = w3_base.to_wei(0.001, "gwei")
            bridge_tx["maxFeePerGas"] = int(base_fee * 1.5) + bridge_tx["maxPriorityFeePerGas"]
        except:
            bridge_tx["gasPrice"] = w3_base.eth.gas_price
        
        signed_bridge = w3_base.eth.account.sign_transaction(bridge_tx, PRIVATE_KEY)
        bridge_hash = w3_base.eth.send_raw_transaction(signed_bridge.rawTransaction)
        print(f"Bridge TX: {bridge_hash.hex()}")
        bridge_receipt = w3_base.eth.wait_for_transaction_receipt(bridge_hash)
        
        if bridge_receipt.status != 1:
            print("ERROR: Bridge failed")
            sys.exit(1)
        
        print("SUCCESS: ETH bridged to Arbitrum")
        print("Waiting 60 seconds for bridge to settle...")
        
    except Exception as e:
        print(f"Bridge failed: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 60)
    print("STEP 4: Send ETH to Mahone on Arbitrum")
    print("=" * 60)
    
    # Wait for bridge
    import time
    time.sleep(60)
    
    # Check Arbitrum balance
    arb_balance = w3_arb.eth.get_balance(account.address)
    print(f"Arbitrum ETH Balance: {arb_balance / 1e18:.6f}")
    
    if arb_balance < w3_arb.to_wei(0.004, 'ether'):
        print("ERROR: Not enough ETH on Arbitrum yet. Bridge may take longer.")
        print(f"Check balance at: https://arbiscan.io/address/{account.address}")
        sys.exit(1)
    
    # Send $10 worth to Mahone
    send_amount = min(arb_balance - w3_arb.to_wei(0.0005, 'ether'), w3_arb.to_wei(0.006, 'ether'))  # $10 + buffer
    
    send_tx = {
        'nonce': w3_arb.eth.get_transaction_count(account.address),
        'to': Web3.to_checksum_address(MAHONE_ADDR),
        'value': send_amount,
        'gas': 21000,
        'gasPrice': w3_arb.eth.gas_price,
        'chainId': w3_arb.eth.chain_id
    }
    
    signed_send = w3_arb.eth.account.sign_transaction(send_tx, PRIVATE_KEY)
    send_hash = w3_arb.eth.send_raw_transaction(signed_send.rawTransaction)
    print(f"Send TX: {send_hash.hex()}")
    print(f"Explorer: https://arbiscan.io/tx/{send_hash.hex()}")
    
    send_receipt = w3_arb.eth.wait_for_transaction_receipt(send_hash)
    
    if send_receipt.status == 1:
        print(f"\n{'=' * 60}")
        print(f"SUCCESS! Sent ${send_amount * eth_price / 1e18:.2f} ETH to Mahone!")
        print(f"Address: {MAHONE_ADDR}")
        print(f"TX: https://arbiscan.io/tx/{send_hash.hex()}")
        print(f"{'=' * 60}")
    else:
        print("ERROR: Send failed")

if __name__ == "__main__":
    main()