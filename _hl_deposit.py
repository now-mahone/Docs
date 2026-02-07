# Quick HL deposit - just step 4
# Created: 2026-02-07
import os, sys, time
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv
from eth_account import Account

load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bot", ".env"))
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
WALLET = Account.from_key(PRIVATE_KEY).address

ARB_USDC = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
HL_BRIDGE = "0x2Df1c51E09a42Ad01097321978c7035100396630"

ERC20_ABI = [
    {"constant":True,"inputs":[{"name":"_owner","type":"address"}],"name":"balanceOf","outputs":[{"name":"balance","type":"uint256"}],"type":"function"},
    {"inputs":[{"name":"to","type":"address"},{"name":"amount","type":"uint256"}],"name":"transfer","outputs":[{"name":"","type":"bool"}],"stateMutability":"nonpayable","type":"function"},
]

arb_rpc = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
if "," in arb_rpc:
    arb_rpc = arb_rpc.split(",")[0].strip()

w3 = Web3(Web3.HTTPProvider(arb_rpc, request_kwargs={"timeout": 15}))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
print(f"Connected to Arbitrum (chain {w3.eth.chain_id})")

usdc = w3.eth.contract(address=Web3.to_checksum_address(ARB_USDC), abi=ERC20_ABI)
bal = usdc.functions.balanceOf(Web3.to_checksum_address(WALLET)).call()
amt = bal / 1e6
print(f"USDC on Arbitrum: {amt:.2f}")

if amt < 1.0:
    print("Not enough USDC on Arbitrum")
    sys.exit(1)

# Build transfer TX with proper gas
nonce = w3.eth.get_transaction_count(Web3.to_checksum_address(WALLET), "pending")

# Use EIP-1559 gas pricing for Arbitrum
fee_history = w3.eth.fee_history(1, "latest")
base_fee = fee_history["baseFeePerGas"][-1]
priority_fee = w3.to_wei(0.1, "gwei")
max_fee = int(base_fee * 2.5) + priority_fee

tx = usdc.functions.transfer(
    Web3.to_checksum_address(HL_BRIDGE), bal
).build_transaction({
    "from": WALLET,
    "nonce": nonce,
    "chainId": 42161,
    "maxPriorityFeePerGas": priority_fee,
    "maxFeePerGas": max_fee,
    "gas": 100000,
})

print(f"Sending {amt:.2f} USDC to Hyperliquid bridge...")
print(f"  Base fee: {base_fee} | Max fee: {max_fee} | Priority: {priority_fee}")

signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
print(f"TX sent: {tx_hash.hex()}")
print(f"Explorer: https://arbiscan.io/tx/{tx_hash.hex()}")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
if receipt.status == 1:
    print(f"CONFIRMED! Gas used: {receipt.gasUsed}")
    print(f"Hyperliquid deposit of ${amt:.2f} is processing (1-5 min)")
else:
    print("TX FAILED!")