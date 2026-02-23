# OFT Omnichain Deployment Runbook
**Created:** 2026-01-20
**Status:** READY_FOR_EXECUTION
**Priority:** #3 Strategic Priority

## Overview

This runbook covers the deployment of KerneOFTV2 (kUSD and KERNE tokens) to Arbitrum One and the bidirectional peer wiring with Base Mainnet to enable omnichain token bridging via LayerZero V2.

## Current State

### Base Mainnet (DEPLOYED)
| Token | Address | Status |
|-------|---------|--------|
| kUSD OFT | `0xb50bFec5FF426744b9d195a8C262da376637Cb6A` | ✅ Deployed |
| KERNE OFT | `0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255` | ✅ Deployed |

### Arbitrum One (PENDING)
| Token | Address | Status |
|-------|---------|--------|
| kUSD OFT | TBD | ⏳ Pending Deployment |
| KERNE OFT | TBD | ⏳ Pending Deployment |

### Peer Wiring Status
| Direction | Status |
|-----------|--------|
| Base → Arbitrum | ⏳ Pending |
| Arbitrum → Base | ⏳ Pending |

---

## Prerequisites

### 1. Environment Variables
Ensure these are set in your shell or `.env` file:

```bash
# Required for all operations
export PRIVATE_KEY="your_deployer_private_key"

# RPC Endpoints
export BASE_RPC_URL="https://mainnet.base.org"
export ARBITRUM_RPC_URL="https://arb1.arbitrum.io/rpc"

# API Keys for verification
export BASESCAN_API_KEY="your_basescan_api_key"
export ARBISCAN_API_KEY="your_arbiscan_api_key"

# Base OFT addresses (already deployed)
export BASE_KUSD_OFT_ADDRESS="0xb50bFec5FF426744b9d195a8C262da376637Cb6A"
export BASE_KERNE_OFT_ADDRESS="0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255"

# Arbitrum OFT addresses (set after deployment)
export ARBITRUM_KUSD_OFT_ADDRESS=""
export ARBITRUM_KERNE_OFT_ADDRESS=""
```

### 2. Wallet Requirements
- **Deployer Wallet:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Required ETH on Arbitrum:** ~0.005 ETH (~$15) for deployment + wiring
- **Required ETH on Base:** ~0.0001 ETH (~$0.30) for peer wiring

### 3. Verify Build
```bash
forge build
```

---

## Execution Steps

### PHASE 1: Deploy OFTs to Arbitrum

**Estimated Gas:** ~0.003 ETH (~$10)
**Time:** ~2 minutes

```bash
# Step 1.1: Verify Arbitrum RPC connectivity
cast chain-id --rpc-url $ARBITRUM_RPC_URL
# Expected output: 42161

# Step 1.2: Check deployer balance on Arbitrum
cast balance $DEPLOYER_ADDRESS --rpc-url $ARBITRUM_RPC_URL
# Ensure > 0.005 ETH

# Step 1.3: Deploy OFTs to Arbitrum
forge script script/DeployOFTArbitrum.s.sol:DeployOFTArbitrum \
  --rpc-url $ARBITRUM_RPC_URL \
  --broadcast \
  --verify \
  -vvvv
```

**Expected Output:**
```
kUSD OFT deployed at: 0x...
KERNE OFT deployed at: 0x...
```

**Post-Deployment:**
1. Record the deployed addresses
2. Update environment variables:
```bash
export ARBITRUM_KUSD_OFT_ADDRESS="<deployed_kusd_address>"
export ARBITRUM_KERNE_OFT_ADDRESS="<deployed_kerne_address>"
```

---

### PHASE 2: Wire Peers on Base (Base → Arbitrum)

**Estimated Gas:** ~0.0001 ETH (~$0.30)
**Time:** ~1 minute

```bash
# Step 2.1: Verify Base RPC connectivity
cast chain-id --rpc-url $BASE_RPC_URL
# Expected output: 8453

# Step 2.2: Execute peer wiring on Base
forge script script/WireOFTPeers.s.sol:WireOFTPeers \
  --rpc-url $BASE_RPC_URL \
  --broadcast \
  -vvvv
```

**Expected Output:**
```
Wiring Base OFTs -> Arbitrum peers...
kUSD peer set: Base -> Arbitrum (EID: 30110)
KERNE peer set: Base -> Arbitrum (EID: 30110)
PEER WIRING COMPLETE
```

---

### PHASE 3: Wire Peers on Arbitrum (Arbitrum → Base)

**Estimated Gas:** ~0.0001 ETH (~$0.30)
**Time:** ~1 minute

```bash
# Step 3.1: Execute peer wiring on Arbitrum
forge script script/WireOFTPeers.s.sol:WireOFTPeers \
  --rpc-url $ARBITRUM_RPC_URL \
  --broadcast \
  -vvvv
```

**Expected Output:**
```
Wiring Arbitrum OFTs -> Base peers...
kUSD peer set: Arbitrum -> Base (EID: 30184)
KERNE peer set: Arbitrum -> Base (EID: 30184)
PEER WIRING COMPLETE
```

---

### PHASE 4: Verification

#### 4.1 Verify Peers on Base
```bash
# Check kUSD peer on Base
cast call $BASE_KUSD_OFT_ADDRESS "peers(uint32)(bytes32)" 30110 --rpc-url $BASE_RPC_URL

# Check KERNE peer on Base
cast call $BASE_KERNE_OFT_ADDRESS "peers(uint32)(bytes32)" 30110 --rpc-url $BASE_RPC_URL
```

#### 4.2 Verify Peers on Arbitrum
```bash
# Check kUSD peer on Arbitrum
cast call $ARBITRUM_KUSD_OFT_ADDRESS "peers(uint32)(bytes32)" 30184 --rpc-url $ARBITRUM_RPC_URL

# Check KERNE peer on Arbitrum
cast call $ARBITRUM_KERNE_OFT_ADDRESS "peers(uint32)(bytes32)" 30184 --rpc-url $ARBITRUM_RPC_URL
```

**Expected:** Non-zero bytes32 values matching the peer addresses.

---

## Post-Deployment Tasks

### 1. Update Treasury Ledger
Add to `docs/TREASURY_LEDGER.md`:
```markdown
### Protocol Contracts (Arbitrum One) - OFT Tokens

| Contract | Address | Purpose |
|----------|---------|---------|
| kUSD OFT | `<address>` | Omnichain kUSD token |
| KERNE OFT | `<address>` | Omnichain KERNE token |
```

### 2. Update Bot Configuration
Add to `bot/.env`:
```bash
# Arbitrum OFT Addresses
ARBITRUM_KUSD_OFT_ADDRESS=<address>
ARBITRUM_KERNE_OFT_ADDRESS=<address>
```

### 3. Update project_state.md
Log the deployment with timestamp.

### 4. Test Bridge (Optional but Recommended)
Mint a small amount of kUSD on Base and bridge to Arbitrum:
```bash
# This requires kUSD balance and gas on both chains
# Detailed bridge test script TBD
```

---

## LayerZero V2 Reference

### Endpoint IDs
| Chain | EID |
|-------|-----|
| Base | 30184 |
| Arbitrum | 30110 |
| Optimism | 30111 |
| Ethereum | 30101 |

### LayerZero V2 Endpoint Address
All chains: `0x1a44076050125825900e736c501f859c50fE728c`

### OFT Standard
- Contract: `KerneOFTV2.sol`
- Inherits: `@layerzerolabs/oft-evm/v2/OFT.sol`
- Features: `mint()`, `burn()`, `send()` (cross-chain transfer)

---

## Rollback Procedure

If deployment fails or peers are misconfigured:

### Clear Peer (Emergency)
```solidity
// Call from owner wallet
oft.setPeer(peerEid, bytes32(0));
```

### Redeploy
Simply redeploy new OFT contracts and re-wire peers. Old contracts become orphaned but harmless.

---

## Success Criteria

- [ ] kUSD OFT deployed on Arbitrum
- [ ] KERNE OFT deployed on Arbitrum
- [ ] Base kUSD peer set to Arbitrum kUSD
- [ ] Base KERNE peer set to Arbitrum KERNE
- [ ] Arbitrum kUSD peer set to Base kUSD
- [ ] Arbitrum KERNE peer set to Base KERNE
- [ ] Verification calls return correct peer addresses
- [ ] Treasury Ledger updated
- [ ] Bot configuration updated
- [ ] project_state.md logged

---

## Estimated Total Cost

| Operation | Chain | Gas (ETH) | USD |
|-----------|-------|-----------|-----|
| Deploy kUSD OFT | Arbitrum | 0.0015 | ~$5 |
| Deploy KERNE OFT | Arbitrum | 0.0015 | ~$5 |
| Wire peers (2 txs) | Base | 0.0001 | ~$0.30 |
| Wire peers (2 txs) | Arbitrum | 0.0001 | ~$0.30 |
| **TOTAL** | | **~0.0032 ETH** | **~$11** |

---

## Contact

For issues during execution, check:
1. LayerZero Explorer: https://layerzeroscan.com/
2. Arbiscan: https://arbiscan.io/
3. BaseScan: https://basescan.org/
