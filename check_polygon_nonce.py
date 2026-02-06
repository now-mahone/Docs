from web3 import Web3
from web3.middleware import geth_poa_middleware

w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com', request_kwargs={'timeout': 10}))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)
addr = '0x57D400cED462a01Ed51a5De038F204Df49690A99'

confirmed = w3.eth.get_transaction_count(addr, 'latest')
pending = w3.eth.get_transaction_count(addr, 'pending')
print(f'Confirmed nonce: {confirmed}')
print(f'Pending nonce: {pending}')
print(f'Stuck txs: {pending - confirmed}')

# Check MATIC balance
matic = w3.eth.get_balance(addr)
matic_eth = float(w3.from_wei(matic, 'ether'))
print(f'MATIC balance: {matic_eth:.4f}')

# Check USDC balance
ERC20_ABI = [
    {'constant': True, 'inputs': [{'name': '_owner', 'type': 'address'}], 'name': 'balanceOf', 'outputs': [{'name': 'balance', 'type': 'uint256'}], 'type': 'function'},
    {'inputs': [{'name': 'owner', 'type': 'address'}, {'name': 'spender', 'type': 'address'}], 'name': 'allowance', 'outputs': [{'name': '', 'type': 'uint256'}], 'stateMutability': 'view', 'type': 'function'},
]
usdc = w3.eth.contract(address=Web3.to_checksum_address('0x3c499c542cEF5E3811e1192ce70d8cC03d5c3359'), abi=ERC20_ABI)
bal = usdc.functions.balanceOf(Web3.to_checksum_address(addr)).call()
print(f'USDC balance: {bal / 1e6:.2f}')

# Check allowance for Li.Fi Diamond
try:
    allowance = usdc.functions.allowance(
        Web3.to_checksum_address(addr),
        Web3.to_checksum_address('0x1231DEB6f5749EF6cE6943a275A1D3E7486F4EaE')
    ).call()
    print(f'USDC allowance for Li.Fi Diamond: {allowance / 1e6:.2f}')
except Exception as e:
    print(f'Could not check Li.Fi allowance: {e}')