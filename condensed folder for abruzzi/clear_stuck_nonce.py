"""Clear stuck nonce 2 on Polygon by sending a 0-value self-transfer with very high gas."""
import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
from dotenv import load_dotenv

load_dotenv("bot/.env")

w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com', request_kwargs={'timeout': 15}))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)

private_key = os.getenv("PRIVATE_KEY")
from eth_account import Account
account = Account.from_key(private_key)
addr = account.address

print(f"Wallet: {addr}")
confirmed_nonce = w3.eth.get_transaction_count(addr, 'latest')
pending_nonce = w3.eth.get_transaction_count(addr, 'pending')
print(f"Confirmed nonce: {confirmed_nonce}, Pending nonce: {pending_nonce}")

if confirmed_nonce == pending_nonce:
    print("No stuck transactions! Nonce is clean.")
else:
    stuck_nonce = confirmed_nonce  # This is the nonce that needs replacing
    print(f"Replacing stuck nonce {stuck_nonce} with high-gas self-transfer...")

    tx = {
        'from': addr,
        'to': addr,  # Self-transfer
        'value': 0,
        'nonce': stuck_nonce,
        'chainId': 137,
        'gas': 21000,
        'maxPriorityFeePerGas': w3.to_wei(500, 'gwei'),  # Very high priority
        'maxFeePerGas': w3.to_wei(1000, 'gwei'),          # Very high max
    }

    signed = w3.eth.account.sign_transaction(tx, private_key)
    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
    print(f"Replacement TX sent: {tx_hash.hex()}")
    print(f"Explorer: https://polygonscan.com/tx/{tx_hash.hex()}")
    print("Waiting for confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    print(f"Status: {'SUCCESS' if receipt['status'] == 1 else 'FAILED'}")
    print(f"Gas used: {receipt['gasUsed']}")
    print(f"Block: {receipt['blockNumber']}")

    # Verify nonce is now clean
    new_confirmed = w3.eth.get_transaction_count(addr, 'latest')
    new_pending = w3.eth.get_transaction_count(addr, 'pending')
    print(f"New confirmed nonce: {new_confirmed}, New pending nonce: {new_pending}")