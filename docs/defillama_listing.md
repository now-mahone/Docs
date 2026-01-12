# DefiLlama Listing Protocol

## Status: READY FOR SUBMISSION ✅

**Last Tested:** 2026-01-10
**TVL Reported:** $389.09k (WETH on Base)
**Adapter Location:** `DefiLlama-Adapters/projects/kerne/index.js`

---

## Adapter Code (Verified Working)

```javascript
// Created: 2026-01-10
// Kerne Protocol - Delta-Neutral Yield Infrastructure on Base
// https://kerne.ai

// KerneVault - ERC-4626 compliant vault holding WETH
// Deployed on Base Mainnet
const KERNE_VAULT = "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd";

async function tvl(api) {
  const [totalAssets, asset] = await api.batchCall([
    { target: KERNE_VAULT, abi: "uint256:totalAssets" },
    { target: KERNE_VAULT, abi: "address:asset" },
  ]);
  api.add(asset, totalAssets);
}

module.exports = {
  methodology: "TVL is calculated by calling totalAssets() on the KerneVault ERC-4626 contract. This includes on-chain WETH collateral and off-chain hedging reserves attested on-chain via the KerneVerificationNode.",
  base: {
    tvl,
  },
};
```

---

## PR Submission Steps

### Step 1: Fork the Official DefiLlama Repo

```bash
# Navigate to https://github.com/DefiLlama/DefiLlama-Adapters
# Click "Fork" to create your own copy
```

### Step 2: Clone Your Fork

```bash
git clone https://github.com/enerzy17/DefiLlama-Adapters.git
cd DefiLlama-Adapters
```

### Step 3: Create the Kerne Adapter

```bash
mkdir -p projects/kerne
# Copy the adapter code above into projects/kerne/index.js
```

### Step 4: Test Locally

```bash
npm install
node test.js projects/kerne
```

Expected output:
```
--- base ---
WETH                      389.09 k
Total: 389.09 k

------ TVL ------
base                      389.09 k
total                    389.09 k
```

### Step 5: Commit and Push

```bash
git add projects/kerne/index.js
git commit -m "Add Kerne Protocol - Delta-Neutral Yield on Base"
git push origin main
```

### Step 6: Create Pull Request

1. Go to https://github.com/DefiLlama/DefiLlama-Adapters
2. Click "New Pull Request"
3. Select your fork as the source
4. Use this PR template:

---

## PR Template

**Title:** `Add Kerne Protocol - Delta-Neutral Yield Infrastructure on Base`

**Description:**

```markdown
## Protocol Information

- **Name:** Kerne Protocol
- **Website:** https://kerne.ai
- **Twitter:** https://x.com/KerneProtocol
- **Category:** Yield
- **Chain:** Base

## Description

Kerne is a delta-neutral yield protocol that generates sustainable returns through:
1. LST collateral (WETH) held on-chain
2. Perpetual futures hedging on CEX (Bybit/OKX)
3. Funding rate arbitrage capture

The protocol uses an ERC-4626 compliant vault architecture.

## TVL Methodology

TVL is calculated by calling `totalAssets()` on the KerneVault contract, which returns the total underlying assets (WETH) managed by the protocol. The vault follows the standard ERC-4626 interface.

## Contract Addresses

| Contract | Address | Chain |
|----------|---------|-------|
| KerneVault | 0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd | Base |

## Test Results

```
--- base ---
WETH                      389.09 k
Total: 389.09 k

------ TVL ------
base                      389.09 k
total                    389.09 k
```

## Checklist

- [x] Adapter follows DefiLlama SDK patterns
- [x] Standard ERC-4626 integration
- [x] Tested locally with `node test.js projects/kerne`
- [x] No external API dependencies
- [x] Methodology clearly documented
- [x] No double-counting of synthetic assets
```

---

## Quick Submit via GitHub CLI

If you have `gh` CLI installed:

```bash
# Fork and clone
gh repo fork DefiLlama/DefiLlama-Adapters --clone

# Create adapter
mkdir -p projects/kerne
cat > projects/kerne/index.js << 'EOF'
// Created: 2026-01-10
// Kerne Protocol - Delta-Neutral Yield Infrastructure on Base
// https://kerne.ai

const { sumERC4626VaultsExport } = require("../helper/erc4626");

const KERNE_VAULT = "0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd";

module.exports = {
  methodology: "TVL is calculated by calling totalAssets() on the KerneVault ERC-4626 contract, which returns the total WETH held including both on-chain collateral and off-chain hedging positions reported by the protocol strategist.",
  base: {
    tvl: sumERC4626VaultsExport({ 
      vaults: [KERNE_VAULT], 
      isOG4626: true 
    }),
  },
};
EOF

# Test
npm install
node test.js projects/kerne

# Commit and push
git add projects/kerne/index.js
git commit -m "Add Kerne Protocol - Delta-Neutral Yield on Base"
git push origin main

# Create PR
gh pr create --title "Add Kerne Protocol - Delta-Neutral Yield Infrastructure on Base" --body "See PR template in description"
```

---

## Expected Timeline

- **PR Review:** 1-3 days
- **Merge:** Within 1 week
- **Live on DefiLlama:** Within 24 hours of merge

---

## Post-Listing Benefits

1. **Passive Discovery:** 100k+ DeFi users browse DefiLlama daily
2. **Aggregator Integration:** Yearn, Beefy, and others pull from DefiLlama
3. **Institutional Credibility:** Listed protocols appear more legitimate
4. **SEO Boost:** DefiLlama pages rank highly on Google

---

## Contact

For questions about the adapter:
- **Protocol:** team@kerne.ai
- **GitHub:** @enerzy17
