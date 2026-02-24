from web3 import Web3
import json

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
addr = "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"
addr = Web3.to_checksum_address(addr)

# Try to call requestWithdrawal (view-like check or just check selector)
# requestWithdrawal(uint256) -> selector 0x7dc7a0d9
# claimWithdrawal(uint256) -> selector 0x3fa733bb

code = w3.eth.get_code(addr).hex()
print(f"Contract at {addr} has code length: {len(code)//2} bytes")

if "7dc7a0d9" in code:
    print("Found requestWithdrawal selector!")
else:
    print("requestWithdrawal selector NOT found.")

if "ba087652" in code: # redeem(uint256,address,address)
    print("Found redeem selector!")