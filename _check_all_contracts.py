from web3 import Web3

w3 = Web3(Web3.HTTPProvider("https://mainnet.base.org"))
print(f"Connected: {w3.is_connected()}")

contracts = {
    "KerneVault": "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC",
    "KerneIntentExecutor (ZIN)": "0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995",
    "KerneZINPool": "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7",
    "KerneTreasury": "0x0067F4957dea17CF76665F6A6585F6a904362106",
    "KerneFlashArbBot": "0xaED581A60db89fEe5f1D8f04538c953Cc78A1687",
    "KerneInsuranceFund": "0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9",
    "KUSDPSM": "0x7286200Ba4C6Ed5041df55965c484a106F4716FD",
    "KERNE Token": "0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340",
    "KerneStaking": "0x032Af1631671126A689614c0c957De774b45D582",
    "kUSD OFT V2": "0x257579db2702BAeeBFAC5c19d354f2FF39831299",
    "KERNE OFT V2": "0x4E1ce62F571893eCfD7062937781A766ff64F14e",
}

for name, addr in contracts.items():
    code = w3.eth.get_code(Web3.to_checksum_address(addr))
    has_code = len(code) > 0
    print(f"{'✅' if has_code else '❌'} {name}: {addr} ({'DEPLOYED' if has_code else 'NO CODE'}) [{len(code)} bytes]")

# Also check Arbitrum
print("\n--- Arbitrum ---")
w3_arb = Web3(Web3.HTTPProvider("https://arb1.arbitrum.io/rpc"))
arb_contracts = {
    "KerneVault (Arb)": "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF",
    "KerneIntentExecutor (Arb)": "0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb",
    "KerneZINPool (Arb)": "0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD",
    "kUSD OFT (Arb)": "0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222",
    "KERNE OFT (Arb)": "0x087365f83caF2E2504c399330F5D15f62Ae7dAC3",
}
for name, addr in arb_contracts.items():
    code = w3_arb.eth.get_code(Web3.to_checksum_address(addr))
    has_code = len(code) > 0
    print(f"{'✅' if has_code else '❌'} {name}: {addr} ({'DEPLOYED' if has_code else 'NO CODE'}) [{len(code)} bytes]")