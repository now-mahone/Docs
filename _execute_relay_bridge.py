# Created: 2026-02-10
# Execute Relay Protocol bridge: USDC (Arbitrum) -> ETH (Base)
import os, sys, json, urllib.request, subprocess
from dotenv import load_dotenv
load_dotenv("bot/.env")

PRIVATE_KEY = os.getenv("PRIVATE_KEY")
ADDRESS = "0x57D400cED462a01Ed51a5De038F204Df49690A99"
ARB_RPC = "https://arb1.arbitrum.io/rpc"

def get_relay_quote():
    payload = {
        "user": ADDRESS,
        "originChainId": 42161,
        "destinationChainId": 8453,
        "originCurrency": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
        "destinationCurrency": "0x0000000000000000000000000000000000000000",
        "amount": "9009000",
        "recipient": ADDRESS,
        "tradeType": "EXACT_INPUT"
    }
    req = urllib.request.Request(
        "https://api.relay.link/quote",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"}
    )
    resp = urllib.request.urlopen(req)
    return json.loads(resp.read())

def cast_send(to, data, value="0"):
    cmd = [
        "cast", "send", to,
        "--private-key", PRIVATE_KEY,
        "--rpc-url", ARB_RPC,
        "--value", value,
        data
    ]
    print(f"  Sending tx to {to}...")
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    print(f"  stdout: {result.stdout[:200]}")
    if result.stderr:
        print(f"  stderr: {result.stderr[:200]}")
    return result.returncode == 0

def main():
    print("=" * 60)
    print("RELAY BRIDGE: USDC (Arbitrum) -> ETH (Base)")
    print("=" * 60)

    # Get fresh quote
    print("\n1. Getting Relay quote...")
    quote = get_relay_quote()
    steps = quote.get("steps", [])
    print(f"   Got {len(steps)} steps")

    for i, step in enumerate(steps):
        step_id = step["id"]
        desc = step["description"]
        tx_data = step["items"][0]["data"]
        to = tx_data["to"]
        data = tx_data["data"]
        value = tx_data.get("value", "0")

        print(f"\n2.{i+1}. Step: {step_id} - {desc}")
        print(f"     To: {to}")
        print(f"     Value: {value}")
        print(f"     Data: {data[:66]}...")

        # Execute with cast send using raw calldata (positional arg after address)
        cmd = [
            "cast", "send",
            "--private-key", PRIVATE_KEY,
            "--rpc-url", ARB_RPC,
            to,
            data
        ]
        if value and value != "0":
            cmd.extend(["--value", value])

        print(f"     Executing...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        output = result.stdout + result.stderr
        print(f"     Result: {output[:300]}")

        if result.returncode != 0:
            print(f"     FAILED! Aborting.")
            sys.exit(1)
        print(f"     SUCCESS!")

    print("\n3. Bridge initiated! ETH should arrive on Base in ~30-60 seconds.")
    print("   Check: cast balance 0x57D400cED462a01Ed51a5De038F204Df49690A99 --rpc-url https://base.drpc.org -e")

if __name__ == "__main__":
    main()