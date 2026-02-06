import json

with open('broadcast/DeployVaultShadow.s.sol/8453/run-latest.json') as f:
    data = json.load(f)

txs = data.get('transactions', [])
for t in txs:
    tt = t.get('transactionType', '?')
    ca = t.get('contractAddress', 'N/A')
    cn = t.get('contractName', '?')
    h = t.get('hash', '?')
    print(f"{tt} -> {ca} ({cn}) tx={h}")

# Also check receipts
receipts = data.get('receipts', [])
for r in receipts:
    status = r.get('status', '?')
    ca = r.get('contractAddress', 'N/A')
    h = r.get('transactionHash', '?')
    print(f"  receipt: status={status} contract={ca} tx={h}")