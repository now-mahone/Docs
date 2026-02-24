from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
addr = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"
addr = Web3.to_checksum_address(addr)

code = w3.eth.get_code(addr).hex()
print(f"Contract at {addr} has code length: {len(code)//2} bytes")

if "7dc7a0d9" in code:
    print("Found requestWithdrawal selector!")
if "ba087652" in code:
    print("Found redeem selector!")