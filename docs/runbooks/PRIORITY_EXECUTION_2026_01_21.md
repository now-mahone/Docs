# Priority Execution Runbook - January 21, 2026
## Priorities: #3 Buyback Flywheel, #5 Token TGE Prep, #7 Leverage Engine

---

## VERIFIED ON-CHAIN DEPLOYMENTS

### Base Mainnet (Chain 8453)

| Contract | Address | Status |
|----------|---------|--------|
| KerneToken | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | ✅ DEPLOYED |
| KerneStaking | `0x032Af1631671126A689614c0c957De774b45D582` | ✅ DEPLOYED |
| KerneTreasury | `0xB656440287f8A1112558D3df915b23326e9b89ec` | ✅ DEPLOYED |
| KerneVault | `0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC` | ✅ DEPLOYED |
| KUSD PSM | `0x7286200Ba4C6Ed5041df55965c484a106F4716FD` | ✅ DEPLOYED |
| InsuranceFund | `0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9` | ✅ DEPLOYED |

### Key Addresses
- Deployer/Owner: `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- WETH (Base): `0x4200000000000000000000000000000000000006`
- USDC (Base): `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`
- Aerodrome Router: `0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43`
- Aerodrome Factory: `0x420DD381b31aEf6683db6B902084cB0FFECe40Da`

---

## PRIORITY #3: BUYBACK FLYWHEEL AUTOMATION

### Current State
- KerneTreasury has full Aerodrome buyback logic implemented
- KERNE Token exists with 100M supply (held by deployer)
- Staking contract ready to receive purchased KERNE
- **MISSING**: KERNE/WETH pool on Aerodrome, Treasury configuration

### Execution Steps

#### Step 3.1: Configure Treasury Buyback Settings
```bash
# Run setup script to configure Treasury
forge script script/SetupTreasuryBuyback.s.sol:SetupTreasuryBuyback \
  --rpc-url $BASE_RPC_URL \
  --broadcast \
  --verify
```

This will:
- Approve WETH as buyback token
- Approve USDC as buyback token
- Set USDC routing hop through WETH

#### Step 3.2: Create KERNE/WETH Pool on Aerodrome

**Option A: Via Script**
```bash
forge script script/SetupTreasuryBuyback.s.sol:CreateKernePool \
  --rpc-url $BASE_RPC_URL \
  --broadcast
```

**Option B: Via Aerodrome UI**
1. Go to https://aerodrome.finance/liquidity
2. Connect deployer wallet
3. Create new pool: KERNE/WETH (volatile)
4. Initial liquidity: 10,000 KERNE + 0.1 WETH (~$0.033/KERNE implied price)

#### Step 3.3: Test Buyback Preview
```bash
# Test that buyback quotes work
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "previewBuyback(address,uint256)" \
  0x4200000000000000000000000000000000000006 \
  10000000000000000 \
  --rpc-url $BASE_RPC_URL
```

#### Step 3.4: Enable Bot Automation
Add to `bot/.env`:
```
BUYBACK_ENABLED=true
BUYBACK_THRESHOLD_WETH=100000000000000000  # 0.1 WETH
BUYBACK_THRESHOLD_USDC=100000000           # 100 USDC
BUYBACK_COOLDOWN=86400                      # 24 hours
```

---

## PRIORITY #5: TOKEN TGE PREPARATION

### Current State
- KERNE Token deployed with 100M supply
- All 100M currently in deployer wallet
- Staking contract deployed and linked
- **MISSING**: Token distribution, liquidity pool, airdrop mechanism

### Tokenomics Allocation (Proposed)

| Allocation | Amount | Percentage | Vesting |
|------------|--------|------------|---------|
| Team & Founders | 15M | 15% | 12mo cliff, 36mo linear |
| Treasury | 20M | 20% | Unlocked for operations |
| Community Airdrop | 30M | 30% | Prisoner's Dilemma structure |
| Ecosystem & Grants | 15M | 15% | DAO controlled |
| Liquidity (Aerodrome) | 10M | 10% | Locked LP tokens |
| Strategic Partners | 10M | 10% | 6mo cliff, 24mo linear |

### Execution Steps

#### Step 5.1: Create Initial Liquidity Pool
```solidity
// Transfer KERNE to create pool
// 10,000,000 KERNE + 30 ETH = ~$0.01/KERNE initial price
// At $100M FDV: 100M tokens * $1 = $100M
```

#### Step 5.2: Distribution Transfers
```bash
# Transfer to Treasury contract for operational buybacks
cast send 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 \
  "transfer(address,uint256)" \
  0xB656440287f8A1112558D3df915b23326e9b89ec \
  20000000000000000000000000 \
  --rpc-url $BASE_RPC_URL \
  --private-key $PRIVATE_KEY
```

#### Step 5.3: Configure Staking DISTRIBUTOR_ROLE
```bash
# Grant DISTRIBUTOR_ROLE to Treasury (for reward distribution)
DISTRIBUTOR_ROLE=$(cast keccak "DISTRIBUTOR_ROLE()")

cast send 0x032Af1631671126A689614c0c957De774b45D582 \
  "grantRole(bytes32,address)" \
  $DISTRIBUTOR_ROLE \
  0xB656440287f8A1112558D3df915b23326e9b89ec \
  --rpc-url $BASE_RPC_URL \
  --private-key $PRIVATE_KEY
```

---

## PRIORITY #7: RECURSIVE LEVERAGE ENGINE (FOLDING)

### Current State
- kUSDMinter.sol has complete fold() logic
- Health factor enforcement at 1.3e18 (130%)
- Liquidation threshold at 1.2e18 (120%)
- **MISSING**: dexAggregator configuration, kUSD deployment verification

### Key Parameters
```
MINT_COLLATERAL_RATIO: 150% (1.5e18)
LIQUIDATION_THRESHOLD: 120% (1.2e18)
MIN_HEALTH_FACTOR: 130% (1.3e18)
LIQUIDATION_BONUS: 5% (0.05e18)
```

### Leverage Tiers
| Tier | Leverage | APY Projection | Risk Level |
|------|----------|----------------|------------|
| Conservative | 2x | ~13% | Low |
| Standard | 3x | ~20% | Medium |
| Aggressive | 5x | ~36% | High |
| Degen | 8x | ~64% | Very High |

### Execution Steps

#### Step 7.1: Deploy kUSDMinter (if not deployed)
```bash
# Check if kUSDMinter is deployed
# If not, create deployment script

forge script script/DeployKUSDMinter.s.sol \
  --rpc-url $BASE_RPC_URL \
  --broadcast \
  --verify
```

#### Step 7.2: Configure DEX Aggregator
The kUSDMinter needs a DEX aggregator for swapping kUSD → ETH during folding.

Options:
1. **1inch Aggregator Router**: `0x1111111254EEB25477B68fb85Ed929f73A960582`
2. **Aerodrome Router**: `0xcF77a3Ba9A5CA399B7c97c478569A74Dd55c726f`
3. **Custom Adapter**: Create `KerneDexAdapter.sol` that wraps Aerodrome

```bash
# Set Aerodrome as DEX aggregator
cast send $KUSD_MINTER_ADDRESS \
  "setDexAggregator(address)" \
  0xcF77a3Ba9A5CA399B7c97c478569A74Dd55c726f \
  --rpc-url $BASE_RPC_URL \
  --private-key $PRIVATE_KEY
```

#### Step 7.3: Test Leverage Flow
```solidity
// 1. User deposits 1 ETH to vault, receives kLP shares
// 2. User calls leverage(1 ETH, 0.66 kUSD) - starts at 150% CR
// 3. User calls fold(0.5 kUSD, minOut) - increases leverage
// 4. Health factor checked: must remain > 130%
```

---

## EXECUTION ORDER

### Phase 1: Treasury Configuration (Now)
1. ✅ Verify KERNE token deployment
2. [ ] Run SetupTreasuryBuyback.s.sol
3. [ ] Create KERNE/WETH Aerodrome pool

### Phase 2: Token Distribution (After Pool)
1. [ ] Transfer tokens to Treasury
2. [ ] Grant DISTRIBUTOR_ROLE to Treasury
3. [ ] Configure staking rewards

### Phase 3: Leverage Engine (Requires kUSD)
1. [ ] Verify kUSD token and kUSDMinter deployment
2. [ ] Configure DEX aggregator
3. [ ] Test fold() on local fork

---

## SUCCESS CRITERIA

### #3 Buyback Flywheel
- [ ] Treasury can execute buybacks via Aerodrome
- [ ] WETH and USDC approved as buyback tokens
- [ ] KERNE/WETH pool has liquidity
- [ ] previewBuyback() returns valid quotes

### #5 Token TGE
- [ ] Tokenomics distribution executed
- [ ] Liquidity pool created and seeded
- [ ] Staking rewards configured
- [ ] Team tokens locked (if applicable)

### #7 Leverage Engine
- [ ] dexAggregator configured
- [ ] fold() executes successfully
- [ ] Health factor enforcement verified
- [ ] Leverage tiers working correctly

---

## GAS ESTIMATES

| Action | Estimated Gas | Est. Cost (@ 0.001 gwei) |
|--------|---------------|--------------------------|
| SetupTreasuryBuyback | ~200,000 | ~$0.05 |
| Create Pool + Add Liquidity | ~500,000 | ~$0.12 |
| Token Transfers | ~100,000 | ~$0.02 |
| Grant Role | ~50,000 | ~$0.01 |
| **Total** | ~850,000 | ~$0.20 |

---

## ROLLBACK PLAN

If any step fails:
1. Pause affected contracts using PAUSER_ROLE
2. Document failure in project_state.md
3. Assess root cause before retry
4. Treasury has emergencyWithdraw() as last resort
