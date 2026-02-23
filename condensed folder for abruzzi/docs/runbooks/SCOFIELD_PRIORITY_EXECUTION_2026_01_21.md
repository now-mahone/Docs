# Scofield Priority Execution Runbook
## Date: 2026-01-21 | Status: READY_FOR_EXECUTION

---

## Executive Summary

This runbook covers the execution of 6 strategic priorities selected by Mr. Scofield:
1. **#1**: Execute Treasury Buyback Flywheel on Mainnet
2. **#3**: Deploy Recursive Leverage Infrastructure (kUSDMinter + DexAdapter)
3. **#5**: Prepare TGE (Token Generation Event)
4. **#7**: Activate Multi-Chain ZIN Solver
5. **#9**: Create KERNE/WETH Aerodrome Liquidity Pool
6. **#11**: Deploy Optimism Chain Expansion

**Estimated Total Gas Cost:** ~0.05-0.15 ETH (~$165-$500)
**Risk Level:** LOW-MEDIUM (all operations are reversible except pool creation)

---

## Pre-Flight Checklist

Before executing ANY commands, verify:

- [ ] Hot wallet `0x57D400cED462a01Ed51a5De038F204Df49690A99` has sufficient ETH on Base (~0.1 ETH recommended)
- [ ] Hot wallet has sufficient ETH on Arbitrum (~0.02 ETH for verification)
- [ ] Hot wallet has sufficient ETH on Optimism (~0.02 ETH for deployment)
- [ ] `PRIVATE_KEY` environment variable is set in terminal
- [ ] `BASE_RPC_URL` environment variable is set
- [ ] `BASESCAN_API_KEY` environment variable is set for verification

```bash
# Load environment (adjust path as needed)
cd z:\kerne-new
set PRIVATE_KEY=<your_private_key>
set BASE_RPC_URL=https://mainnet.base.org
set BASESCAN_API_KEY=<your_basescan_api_key>
set ARBISCAN_API_KEY=<your_arbiscan_api_key>
set OPTIMISM_RPC_URL=https://mainnet.optimism.io
```

---

# PRIORITY #1: Execute Treasury Buyback Flywheel on Mainnet

## Overview
The Treasury is deployed at `0xB656440287f8A1112558D3df915b23326e9b89ec` but was configured with WRONG addresses (both `kerneToken` and `stakingContract` pointing to deployer wallet instead of actual contracts).

## Key Addresses
| Contract | Address |
|----------|---------|
| KerneTreasury | `0xB656440287f8A1112558D3df915b23326e9b89ec` |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` |
| KERNE Staking | `0x032Af1631671126A689614c0c957De774b45D582` |
| Aerodrome Router | `0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43` |

## Step 1.1: Verify Current Treasury State (READ-ONLY)

```bash
# Check current KERNE token address in Treasury
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "kerneToken()(address)" --rpc-url %BASE_RPC_URL%

# Check current staking contract address in Treasury
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "stakingContract()(address)" --rpc-url %BASE_RPC_URL%
```

**Expected Output:** Both should currently return the deployer address `0x57D4...0A99` (WRONG).

## Step 1.2: Fix Treasury Configuration

**⚠️ MAINNET TRANSACTION - Requires Gas**

```bash
# Fix KERNE Token address
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec "setKerneToken(address)" 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%

# Fix Staking Contract address  
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec "setStakingContract(address)" 0x032Af1631671126A689614c0c957De774b45D582 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Step 1.3: Approve Buyback Tokens

```bash
# Approve WETH for buybacks
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec "setApprovedBuybackToken(address,bool)" 0x4200000000000000000000000000000000000006 true --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%

# Approve USDC for buybacks
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec "setApprovedBuybackToken(address,bool)" 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 true --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%

# Set USDC routing hop (USDC -> WETH -> KERNE for better liquidity)
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec "setRoutingHop(address,address)" 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 0x4200000000000000000000000000000000000006 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Step 1.4: Verify Configuration

```bash
# Verify KERNE token is now correct
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "kerneToken()(address)" --rpc-url %BASE_RPC_URL%
# Expected: 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340

# Verify Staking is now correct
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "stakingContract()(address)" --rpc-url %BASE_RPC_URL%
# Expected: 0x032Af1631671126A689614c0c957De774b45D582

# Verify WETH is approved
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "approvedBuybackTokens(address)(bool)" 0x4200000000000000000000000000000000000006 --rpc-url %BASE_RPC_URL%
# Expected: true
```

## Status: ✅ READY FOR EXECUTION

---

# PRIORITY #3: Deploy Recursive Leverage Infrastructure

## Overview
Deploy `KerneDexAdapter` and `kUSDMinter` to enable one-click recursive leverage (folding) for users.

## Step 3.1: Deploy Full Leverage Infrastructure

**⚠️ MAINNET DEPLOYMENT - Requires ~0.02 ETH Gas**

```bash
forge script script/DeployLeverageInfra.s.sol:FullLeverageSetup --rpc-url %BASE_RPC_URL% --broadcast --verify -vvvv
```

This deploys:
- `KerneDexAdapter` - Aerodrome routing adapter
- `kUSDMinter` - Leverage/minting engine
- Configures DEX adapter on minter
- Sets up kUSD/WETH hop routing

## Step 3.2: Grant MINTER_ROLE on kUSD

After deployment, note the `kUSDMinter` address from output, then:

```bash
# Get the MINTER_ROLE hash
cast call 0x257579db2702BAeeBFAC5c19d354f2FF39831299 "MINTER_ROLE()(bytes32)" --rpc-url %BASE_RPC_URL%

# Grant MINTER_ROLE to kUSDMinter (replace <KUSD_MINTER_ADDRESS>)
cast send 0x257579db2702BAeeBFAC5c19d354f2FF39831299 "grantRole(bytes32,address)" <MINTER_ROLE_HASH> <KUSD_MINTER_ADDRESS> --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Step 3.3: Update Treasury Ledger

After successful deployment, add to `docs/TREASURY_LEDGER.md`:
```markdown
| KerneDexAdapter | <DEPLOYED_ADDRESS> | DEX routing adapter |
| kUSDMinter | <DEPLOYED_ADDRESS> | Leverage engine |
```

## Status: ✅ READY FOR EXECUTION

---

# PRIORITY #5: Prepare TGE (Token Generation Event)

## Overview
The KERNE token is deployed at `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` with 100M initial supply minted to deployer. TGE preparation involves creating the airdrop infrastructure and liquidity allocation.

## Current Token State
- **Total Supply:** 100,000,000 KERNE
- **Current Holder:** Deployer wallet `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Has MINTER_ROLE:** No additional minters configured

## Step 5.1: Verify Token Supply

```bash
cast call 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 "totalSupply()(uint256)" --rpc-url %BASE_RPC_URL%
# Expected: 100000000000000000000000000 (100M * 10^18)

cast call 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 "balanceOf(address)(uint256)" 0x57D400cED462a01Ed51a5De038F204Df49690A99 --rpc-url %BASE_RPC_URL%
# Expected: Full supply in deployer wallet
```

## Step 5.2: Create Airdrop Contract (NEW CODE NEEDED)

**ACTION REQUIRED:** Create `src/KerneAirdrop.sol` implementing the "Prisoner's Dilemma" mechanism:
- 25% immediate claim with 75% penalty (penalty redistributed to Loyalists)
- 100% vesting over 12 months
- 100% + bonus for 12-month lock with LP

```solidity
// Key functions needed:
- claim(uint8 claimType) // 0=immediate, 1=vest, 2=lock
- calculateBonus(address user) // bonus from penalty pool
- setMerkleRoot(bytes32 root) // for eligibility
```

## Step 5.3: Token Allocation Plan

Based on Genesis Document recommendations:
| Allocation | Percentage | Amount | Status |
|------------|------------|--------|--------|
| Team (Vested) | 15% | 15M | Pending |
| Treasury | 20% | 20M | Pending |
| Airdrop Pool | 35% | 35M | Pending |
| Liquidity | 10% | 10M | Pending |
| Ecosystem Fund | 10% | 10M | Pending |
| CEX Launchpools | 5% | 5M | Pending |
| Grants/Advisors | 5% | 5M | Pending |

## Step 5.4: Transfer to Treasury/Vesting Contracts

Once allocation contracts are deployed:
```bash
# Transfer to Treasury (20M KERNE)
cast send 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 "transfer(address,uint256)" <TREASURY_ALLOCATION_ADDRESS> 20000000000000000000000000 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%

# Transfer to Airdrop Pool (35M KERNE)
cast send 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 "transfer(address,uint256)" <AIRDROP_CONTRACT_ADDRESS> 35000000000000000000000000 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Status: ⚠️ REQUIRES NEW CONTRACT (KerneAirdrop.sol)

---

# PRIORITY #7: Activate Multi-Chain ZIN Solver

## Overview
Enable the ZIN Solver to process intents on both Base and Arbitrum simultaneously.

## Current Configuration (From bot/.env.example)
- `ZIN_CHAINS=base,arbitrum` (already configured)
- Base ZIN Pool: `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7`
- Arbitrum ZIN Pool: `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD`

## Step 7.1: Create/Update bot/.env

**ACTION:** Copy `.env.example` to `.env` and fill in values:

```bash
cd bot
copy .env.example .env
```

Then edit `bot/.env`:
```env
# Core
PRIVATE_KEY=<your_private_key>
RPC_URL=https://mainnet.base.org
BASE_RPC_URL=https://mainnet.base.org
ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc

# ZIN Configuration
ZIN_SOLVER_LIVE=true
ZIN_CHAINS=base,arbitrum
ZIN_EXECUTOR_ADDRESS=0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995
ZIN_POOL_ADDRESS=0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7
ARBITRUM_ZIN_POOL_ADDRESS=0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD
ARBITRUM_VAULT_ADDRESS=0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF

# Guardrails
ZIN_MIN_PROFIT_BPS=10
ZIN_MAX_GAS_PRICE_GWEI=30
ZIN_MAX_INTENTS_PER_CYCLE=5

# Alerts
DISCORD_WEBHOOK_URL=<your_webhook>
```

## Step 7.2: Verify Pool Liquidity

```bash
# Check Base ZIN Pool liquidity (USDC)
cast call 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7 "maxFlashLoan(address)(uint256)" 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 --rpc-url https://mainnet.base.org

# Check Base ZIN Pool liquidity (WETH)
cast call 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7 "maxFlashLoan(address)(uint256)" 0x4200000000000000000000000000000000000006 --rpc-url https://mainnet.base.org

# Check Arbitrum ZIN Pool liquidity (USDC)
cast call 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD "maxFlashLoan(address)(uint256)" 0xaf88d065e77c8cC2239327C5EDb3A432268e5831 --rpc-url https://arb1.arbitrum.io/rpc
```

## Step 7.3: Fund ZIN Pools (CRITICAL)

**Current liquidity is ~$79 - TOO LOW**

Transfer USDC and WETH directly to pool addresses:

```bash
# Fund Base Pool with USDC (10,000 USDC example)
cast send 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913 "transfer(address,uint256)" 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7 10000000000 --private-key %PRIVATE_KEY% --rpc-url https://mainnet.base.org

# Fund Base Pool with WETH (1 WETH example)
cast send 0x4200000000000000000000000000000000000006 "transfer(address,uint256)" 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7 1000000000000000000 --private-key %PRIVATE_KEY% --rpc-url https://mainnet.base.org

# Fund Arbitrum Pool with USDC (10,000 USDC example)
cast send 0xaf88d065e77c8cC2239327C5EDb3A432268e5831 "transfer(address,uint256)" 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD 10000000000 --private-key %PRIVATE_KEY% --rpc-url https://arb1.arbitrum.io/rpc
```

## Step 7.4: Start Multi-Chain Solver

```bash
cd bot
python solver/zin_solver.py --live
```

Or via Docker:
```bash
docker-compose up -d kerne-zin-solver
```

## Status: ✅ READY (After Pool Funding)

---

# PRIORITY #9: Create KERNE/WETH Aerodrome Liquidity Pool

## Overview
Create the initial KERNE/WETH trading pool on Aerodrome to enable:
- Price discovery for KERNE token
- Treasury buyback execution
- Pre-TGE liquidity for early trading

## Key Parameters
| Parameter | Value |
|-----------|-------|
| Token0 | KERNE (`0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340`) |
| Token1 | WETH (`0x4200000000000000000000000000000000000006`) |
| Pool Type | Volatile (not stable) |
| Router | `0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43` |

## Step 9.1: Determine Initial Price

```
Recommended: $0.05 per KERNE (implies $5M FDV on 100M supply)

If seeding with 0.1 ETH (~$330) and 6,600 KERNE:
- Price = $330 / 6,600 = $0.05/KERNE
- FDV = $0.05 × 100M = $5M
```

Adjust based on your capital availability and desired FDV.

## Step 9.2: Approve Tokens

```bash
# Approve KERNE for Aerodrome Router (100,000 KERNE for headroom)
cast send 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 "approve(address,uint256)" 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43 100000000000000000000000 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%

# Approve WETH for Aerodrome Router (1 WETH for headroom)
cast send 0x4200000000000000000000000000000000000006 "approve(address,uint256)" 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43 1000000000000000000 --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Step 9.3: Add Liquidity (Creates Pool)

Using Forge script:
```bash
forge script script/SetupTreasuryBuyback.s.sol:CreateKernePool --rpc-url %BASE_RPC_URL% --broadcast --verify
```

Or manual via cast (with custom amounts):
```bash
# CRITICAL: Adjust amounts based on your capital and desired price
# Example: 10,000 KERNE + 0.15 WETH = ~$0.05/KERNE at $3300/ETH

cast send 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43 \
  "addLiquidity(address,address,bool,uint256,uint256,uint256,uint256,address,uint256)" \
  0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 \
  0x4200000000000000000000000000000000000006 \
  false \
  10000000000000000000000 \
  150000000000000000 \
  9500000000000000000000 \
  142500000000000000 \
  0x57D400cED462a01Ed51a5De038F204Df49690A99 \
  1737520000 \
  --private-key %PRIVATE_KEY% --rpc-url %BASE_RPC_URL%
```

## Step 9.4: Verify Pool Creation

```bash
# Query Aerodrome Factory for the pool address
cast call 0x420DD381b31aEf6683db6B902084cB0FFECe40Da "getPool(address,address,bool)(address)" 0x4200000000000000000000000000000000000006 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 false --rpc-url %BASE_RPC_URL%
```

## Step 9.5: Test Treasury Buyback Preview

```bash
# After pool exists, test buyback preview
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec "previewBuyback(address,uint256)(uint256,uint256)" 0x4200000000000000000000000000000000000006 10000000000000000 --rpc-url %BASE_RPC_URL%
```

## Status: ✅ READY (After Capital Allocation Decision)

---

# PRIORITY #11: Deploy Optimism Chain Expansion

## Overview
Deploy Kerne infrastructure to Optimism mainnet: KerneVault + OFT bridges.

## Step 11.1: Create Optimism Deployment Script

**ACTION:** Create `script/DeployOptimismVault.s.sol`:

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneVault.sol";

contract DeployOptimismVault is Script {
    // Optimism Mainnet Addresses
    address constant WSTETH = 0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb; // Lido wstETH on Optimism
    address constant STRATEGIST = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=== Deploying KerneVault on Optimism ===");
        console.log("Deployer:", deployer);
        console.log("Asset (wstETH):", WSTETH);
        
        KerneVault vault = new KerneVault(
            WSTETH,
            "Kerne wstETH Vault",
            "kvWSTETH",
            deployer // Initially deployer as admin
        );
        
        console.log("KerneVault deployed at:", address(vault));
        
        // Initialize vault
        vault.initialize(500, false); // 5% performance fee, not whitelisted
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Optimism Vault Deployed ===");
        console.log("Vault:", address(vault));
        console.log("Asset:", WSTETH);
    }
}
```

## Step 11.2: Deploy Optimism Vault

```bash
# Set Optimism RPC
set OPTIMISM_RPC_URL=https://mainnet.optimism.io
set OPTIMISM_ETHERSCAN_API_KEY=<your_key>

# Deploy
forge script script/DeployOptimismVault.s.sol:DeployOptimismVault --rpc-url %OPTIMISM_RPC_URL% --broadcast --verify -vvvv
```

## Step 11.3: Deploy OFT V2 Bridges on Optimism

Create and run OFT deployment for Optimism, then wire peers:

```bash
# After OFT deployment, wire peers:
# Base -> Optimism
cast send <BASE_KUSD_OFT> "setPeer(uint32,bytes32)" 111 <OPTIMISM_KUSD_OFT_BYTES32> --private-key %PRIVATE_KEY% --rpc-url https://mainnet.base.org

# Optimism -> Base
cast send <OPTIMISM_KUSD_OFT> "setPeer(uint32,bytes32)" 184 <BASE_KUSD_OFT_BYTES32> --private-key %PRIVATE_KEY% --rpc-url https://mainnet.optimism.io
```

## Step 11.4: Apply for Optimism Grant

1. Go to: https://app.optimism.io/grants
2. Apply under "Protocol Governance Fund"
3. Pitch: Delta-neutral yield infrastructure on Optimism
4. Requested amount: $100k-$500k in OP tokens

## Status: ⚠️ REQUIRES NEW SCRIPT CREATION

---

# Post-Execution Checklist

After completing all priorities:

- [ ] Update `docs/TREASURY_LEDGER.md` with all new contract addresses
- [ ] Update `bot/.env` with new addresses
- [ ] Update `project_state.md` with execution log
- [ ] Commit and push to private repository

```bash
git add -A
git commit -m "[2026-01-21] Execute Scofield priorities: Buyback flywheel, leverage infra, ZIN multi-chain, KERNE pool, Optimism expansion"
git push private main
```

---

# Risk Summary

| Priority | Risk Level | Reversible | Capital Required |
|----------|------------|------------|------------------|
| #1 Treasury Config | LOW | YES | ~0.005 ETH gas |
| #3 Leverage Deploy | LOW | YES | ~0.02 ETH gas |
| #5 TGE Prep | MEDIUM | PARTIAL | Requires new contract |
| #7 ZIN Multi-Chain | LOW | YES | Pool funding capital |
| #9 KERNE Pool | MEDIUM | NO* | ~$500-$10k liquidity |
| #11 Optimism | LOW | YES | ~0.02 ETH gas |

*Pool creation is irreversible, but LP tokens can be withdrawn.

---

## Questions for Mr. Scofield Before Execution

1. **KERNE/WETH Pool Price:** What initial price/FDV do you want for KERNE? ($5M/$10M/$50M?)
2. **Pool Liquidity:** How much KERNE + WETH do you want to seed? (Minimum: ~$500)
3. **ZIN Pool Funding:** How much USDC/WETH to fund ZIN pools? (Recommended: $10k+ per pool)
4. **Optimism Grant:** Should we apply for Optimism Foundation grant?
5. **TGE Timeline:** When should we target for TGE? (Need time to build airdrop contract)
