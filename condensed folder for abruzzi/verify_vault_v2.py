#!/usr/bin/env python3
"""Submit KerneVault verification to Etherscan V2 API for Base (chainid=8453)"""
import json
import requests
import time

CONTRACT_ADDRESS = "0xDA9765F84208F8E94225889B2C9331DCe940fB20"
API_KEY = "C1A3D6JCSMCZFTSE75WFEVABUZM8VWVVN7"
CHAIN_ID = 8453
CONSTRUCTOR_ARGS = "000000000000000000000000420000000000000000000000000000000000000600000000000000000000000000000000000000000000000000000000000000c0000000000000000000000000000000000000000000000000000000000000010000000000000000000000000057d400ced462a01ed51a5de038f204df49690a9900000000000000000000000057d400ced462a01ed51a5de038f204df49690a9900000000000000000000000057d400ced462a01ed51a5de038f204df49690a9900000000000000000000000000000000000000000000000000000000000000104b65726e652057455448205661756c740000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000056b57455448000000000000000000000000000000000000000000000000000000"

V2_API_URL = f"https://api.etherscan.io/v2/api?chainid={CHAIN_ID}"

def main():
    # Read and clean the standard JSON input
    print("[1/4] Reading standard JSON input...")
    with open("verify_input.json", "rb") as f:
        raw = f.read()
    
    # Remove BOM if present - use utf-8-sig which auto-strips UTF-8 BOM
    if raw.startswith(b'\xff\xfe'):
        text = raw.decode('utf-16-le').lstrip('\ufeff')
    else:
        text = raw.decode('utf-8-sig')
    
    # Validate it's valid JSON
    source_json = json.loads(text)
    clean_json = json.dumps(source_json)
    print(f"   Source JSON size: {len(clean_json)} bytes")
    print(f"   Language: {source_json.get('language')}")
    print(f"   Sources: {len(source_json.get('sources', {}))} files")
    
    # Get compiler version from settings
    evm_version = source_json.get("settings", {}).get("evmVersion", "unknown")
    via_ir = source_json.get("settings", {}).get("viaIR", False)
    print(f"   EVM Version: {evm_version}, via_ir: {via_ir}")
    
    # Submit verification
    print(f"\n[2/4] Submitting verification to Etherscan V2 API (chainid={CHAIN_ID})...")
    
    payload = {
        "apikey": API_KEY,
        "module": "contract",
        "action": "verifysourcecode",
        "contractaddress": CONTRACT_ADDRESS,
        "sourceCode": clean_json,
        "codeformat": "solidity-standard-json-input",
        "contractname": "src/KerneVault.sol:KerneVault",
        "compilerversion": "v0.8.24+commit.e11b9ed9",
        "constructorArguements": CONSTRUCTOR_ARGS,
    }
    
    resp = requests.post(V2_API_URL, data=payload)
    print(f"   HTTP Status: {resp.status_code}")
    result = resp.json()
    print(f"   Response: {json.dumps(result, indent=2)}")
    
    if result.get("status") != "1":
        print(f"\n[FAIL] Verification submission failed: {result.get('result', 'unknown error')}")
        return
    
    guid = result["result"]
    print(f"   GUID: {guid}")
    
    # Poll for result
    print(f"\n[3/4] Polling for verification result...")
    for i in range(20):
        time.sleep(10)
        check_payload = {
            "apikey": API_KEY,
            "module": "contract",
            "action": "checkverifystatus",
            "guid": guid,
        }
        check_resp = requests.get(V2_API_URL, params=check_payload)
        check_result = check_resp.json()
        status = check_result.get("result", "")
        print(f"   Poll {i+1}: {status}")
        
        if "Pending" not in status:
            break
    
    if "Pass" in status or "success" in status.lower():
        print(f"\n[4/4] ✅ CONTRACT VERIFIED SUCCESSFULLY!")
        print(f"   View: https://basescan.org/address/{CONTRACT_ADDRESS}#code")
    else:
        print(f"\n[4/4] ❌ Verification result: {status}")
        print(f"   Check manually: https://basescan.org/address/{CONTRACT_ADDRESS}")

if __name__ == "__main__":
    main()