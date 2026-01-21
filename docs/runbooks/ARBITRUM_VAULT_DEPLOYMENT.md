# Arbitrum Vault Deployment Runbook
**Created:** 2026-01-20
**Priority:** #6 Strategic Priority
**Status:** READY_FOR_EXECUTION

## Objective
Deploy a KerneVault on Arbitrum One to unlock native Arbitrum deposits and expand TVL capture beyond Base.

---

## Current State
- **Base Vault Deployed:** `0xDF9a2f5152c533F7fcc3bAdEd41e157C9563C695`
- **Arbitrum Vault:** Not deployed
- **Deployment Script:** `script/DeployArbitrumVault.s.sol`
- **Target Asset:** wstETH (Arbitrum)

---

## Prerequisites

### 1. Environment Variables
```bash
export PRIVATE_KEY="your_private_key"
export ARBITRUM_RPC_URL="https://arb1.arbitrum.io/rpc"
export ARBISCAN_API_KEY="your_arbiscan_api_key"
```

### 2. Wallet Funding
- **Deployer:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Required ETH on Arbitrum:** ~0.002 ETH ($6-8)

---

## Deployment Steps

### Step 1: Verify RPC and Balance
```bash
cast chain-id --rpc-url $ARBITRUM_RPC_URL
cast balance 0x57D400cED462a01Ed51a5De038F204Df49690A99 --rpc-url $ARBITRUM_RPC_URL
```
Expected chain ID: **42161**

### Step 2: Deploy Vault
```bash
forge script script/DeployArbitrumVault.s.sol:DeployArbitrumVault \
  --rpc-url $ARBITRUM_RPC_URL \
  --broadcast \
  --verify \
  -vvvv
```

Expected output:
```
Arbitrum KerneVault deployed at: 0x...
```

---

## Post-Deployment Actions

### 1. Update Treasury Ledger
Add to `docs/TREASURY_LEDGER.md` under Arbitrum contracts:
```markdown
| KerneVault | `<address>` | Arbitrum main vault |
```

### 2. Update bot/.env
```bash
ARBITRUM_VAULT_ADDRESS=<address>
```

### 3. Verify Vault Configuration
Ensure:
- Asset = wstETH (`0x5979D7b546E38E414F7E9822514be443A4800529`)
- Admin & Strategist = deployer wallet
- Exchange deposit address set (currently `0x57D4...0A99`)

### 4. Optional: Enable ZIN Integration
If desired, wire the vault to ZIN pool liquidity or flash loan usage after deployment.

---

## Addresses
- **wstETH (Arbitrum):** `0x5979D7b546E38E414F7E9822514be443A4800529`
- **USDC (Arbitrum):** `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`

---

## Success Criteria
- [ ] Vault deployed on Arbitrum
- [ ] Address logged in Treasury Ledger
- [ ] bot/.env updated
- [ ] Project state log updated

---

## Notes
The current deployment script uses wstETH as the vault asset. If we need USDC or multi-asset vaults, create additional deployment scripts or upgrade to the VaultFactory for permissionless instantiation.
