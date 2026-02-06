from web3 import Web3

RPC_URL = "https://arb1.arbitrum.io/rpc"
VAULT_ADDRESS = "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF"

def verify():
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    code = w3.eth.get_code(VAULT_ADDRESS)
    print(f"Contract Code Length: {len(code)}")
    if len(code) > 2:
        print("Contract is deployed.")
    else:
        print("No contract found at this address.")

if __name__ == "__main__":
    verify()