# Quick script to verify if the approval went to the correct vault

EXPECTED_VAULT = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"

print("Expected Vault Address (from our config):")
print(EXPECTED_VAULT)
print()
print("Please paste the FULL spender address from MetaMask:")
print("(The address shown as 'Spender' in the approval transaction)")
print()
print("Then we can verify if they match.")