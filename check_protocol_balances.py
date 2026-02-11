from web3 import Web3

def check_balances():
    w3 = Web3(Web3.HTTPProvider('https://mainnet.base.org'))
    usdc_address = '0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913'
    weth_address = '0x4200000000000000000000000000000000000006'
    
    addresses = {
        "Treasury": "0x57D400cED462a01Ed51a5De038F204Df49690A99",
        "ZIN Pool": "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7",
        "Vault": "0xDA9765F84208F8E94225889B2C9331DCe940fB20",
        "PSM": "0x7286200Ba4C6Ed5041df55965c484a106F4716FD"
    }
    
    abi = [
        {
            "constant": True,
            "inputs": [{"name": "_owner", "type": "address"}],
            "name": "balanceOf",
            "outputs": [{"name": "balance", "type": "uint256"}],
            "type": "function"
        }
    ]
    
    usdc_contract = w3.eth.contract(address=Web3.to_checksum_address(usdc_address), abi=abi)
    weth_contract = w3.eth.contract(address=Web3.to_checksum_address(weth_address), abi=abi)
    
    print("--- Protocol Balances on Base ---")
    for name, addr in addresses.items():
        try:
            usdc_bal = usdc_contract.functions.balanceOf(Web3.to_checksum_address(addr)).call()
            weth_bal = weth_contract.functions.balanceOf(Web3.to_checksum_address(addr)).call()
            eth_bal = w3.eth.get_balance(Web3.to_checksum_address(addr))
            
            print(f"{name} ({addr}):")
            print(f"  USDC: {usdc_bal / 1e6}")
            print(f"  WETH: {weth_bal / 1e18}")
            print(f"  ETH:  {eth_bal / 1e18}")
        except Exception as e:
            print(f"Error checking {name}: {e}")

if __name__ == "__main__":
    check_balances()