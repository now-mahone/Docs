"""
Full bridge: Clear stuck nonce, approve USDC, get Li.Fi quote, execute bridge.
All with 500 Gwei priority fee on Polygon.
"""
import os, sys, time, requests
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dotenv import load_dotenv
load_dotenv("bot/.env")

from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account import Account

# Config
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
account = Account.from_key(PRIVATE_KEY)
WALLET = account.address
POLYGON_USDC = "0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359"
BASE_USDC = "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
LIFI_API = "https://li.quest/v1"
PRIORITY_FEE = Web3.to_wei(500, 'gwei')
MAX_FEE = Web3.to_wei(1000, 'gwei')

ERC20_ABI = [
    {"constant": True, "inputs": [{"name": "_owner", "type": "address"}], "name": "balanceOf", "outputs": [{"name": "balance", "type": "uint256"}], "type": "function"},
    {"inputs": [{"name": "spender", "type": "address"}, {"name": "amount", "type": "uint256"}], "name": "approve", "outputs": [{"name": "", "type": "bool"}], "stateMutability": "nonpayable", "type": "function"},
    {"inputs": [{"name": "owner", "type": "address"}, {"name": "spender", "type": "address"}], "name": "allowance", "outputs": [{"name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
]

# Connect
w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com', request_kwargs={'timeout': 15}))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
print(f"Wallet: {WALLET}")

# ---- STEP 1: Clear any stuck nonces ----
def clear_stuck_nonces():
    while True:
        confirmed = w3.eth.get_transaction_count(WALLET, 'latest')
        pending = w3.eth.get_transaction_count(WALLET, 'pending')
        if confirmed == pending:
            print(f"Nonce clean: {confirmed}")
            return confirmed
        print(f"Stuck nonce {confirmed} (pending: {pending}). Clearing...")
        tx = {
            'from': WALLET, 'to': WALLET, 'value': 0,
            'nonce': confirmed, 'chainId': 137, 'gas': 21000,
            'maxPriorityFeePerGas': PRIORITY_FEE, 'maxFeePerGas': MAX_FEE,
        }
        signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
        tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
        print(f"  Clear TX: {tx_hash.hex()}")
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
        print(f"  Confirmed in block {receipt['blockNumber']}")

nonce = clear_stuck_nonces()

# ---- STEP 2: Get Li.Fi quote ----
print(f"\nFetching Li.Fi quote for 362.3 USDC POLYGON -> BASE...")
amount_raw = str(362300000)  # 362.3 * 1e6

resp = requests.get(f"{LIFI_API}/quote", params={
    "fromChain": 137,
    "toChain": 8453,
    "fromToken": POLYGON_USDC,
    "toToken": BASE_USDC,
    "fromAmount": amount_raw,
    "fromAddress": WALLET,
    "slippage": 0.005,
}, timeout=30)

if resp.status_code != 200:
    print(f"Quote failed: {resp.status_code} - {resp.text[:500]}")
    sys.exit(1)

quote = resp.json()
estimate = quote.get("estimate", {})
to_amount = int(estimate.get("toAmount", "0")) / 1e6
tool = quote.get("tool", "?")
print(f"Route: {tool} | Output: {to_amount:.2f} USDC | Slippage: 0.5%")

tx_request = quote["transactionRequest"]
spender = tx_request["to"]

# ---- STEP 3: Approve USDC for the Li.Fi spender ----
usdc = w3.eth.contract(address=Web3.to_checksum_address(POLYGON_USDC), abi=ERC20_ABI)
allowance = usdc.functions.allowance(Web3.to_checksum_address(WALLET), Web3.to_checksum_address(spender)).call()
print(f"\nCurrent allowance for {spender}: {allowance / 1e6:.2f} USDC")

if allowance < int(amount_raw):
    print("Sending approval with 500 Gwei priority...")
    approve_tx = usdc.functions.approve(
        Web3.to_checksum_address(spender), 2**256 - 1
    ).build_transaction({
        'from': WALLET, 'nonce': nonce, 'chainId': 137,
        'maxPriorityFeePerGas': PRIORITY_FEE, 'maxFeePerGas': MAX_FEE,
    })
    signed = w3.eth.account.sign_transaction(approve_tx, PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Approval TX: {tx_hash.hex()}")
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=120)
    if receipt['status'] != 1:
        print("APPROVAL FAILED!")
        sys.exit(1)
    print(f"Approval confirmed in block {receipt['blockNumber']}")
    nonce += 1
    # Verify allowance
    new_allowance = usdc.functions.allowance(Web3.to_checksum_address(WALLET), Web3.to_checksum_address(spender)).call()
    print(f"New allowance: {new_allowance / 1e6:.2f} USDC")
else:
    print("Allowance sufficient, skipping approval.")

# ---- STEP 4: Execute the bridge transaction ----
print(f"\nExecuting bridge transaction...")

def to_int(val):
    if isinstance(val, str) and val.startswith("0x"):
        return int(val, 16)
    return int(val)

gas_limit = to_int(tx_request.get("gasLimit", 500000))

tx = {
    'from': WALLET,
    'to': Web3.to_checksum_address(tx_request["to"]),
    'data': tx_request["data"],
    'value': to_int(tx_request.get("value", 0)),
    'nonce': nonce,
    'chainId': 137,
    'gas': int(gas_limit * 1.3),
    'maxPriorityFeePerGas': PRIORITY_FEE,
    'maxFeePerGas': MAX_FEE,
}

signed = w3.eth.account.sign_transaction(tx, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
hash_hex = tx_hash.hex()
print(f"Bridge TX sent: {hash_hex}")
print(f"Explorer: https://polygonscan.com/tx/{hash_hex}")
print("Waiting for confirmation (up to 3 min)...")

receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
if receipt['status'] == 1:
    print(f"\nBRIDGE SUCCESS! Block: {receipt['blockNumber']}, Gas: {receipt['gasUsed']}")
    print(f"~{to_amount:.2f} USDC should arrive on Base in 2-5 minutes.")
    print(f"Track: https://scan.li.fi/tx/{hash_hex}")
else:
    print(f"\nBRIDGE FAILED! Receipt status: {receipt['status']}")
    print(f"Check: https://polygonscan.com/tx/{hash_hex}")