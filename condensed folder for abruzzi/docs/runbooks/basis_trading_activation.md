# Hyperliquid Basis Trading — Activation Runbook

## Current State (2026-02-05 22:30 MST)

| Component | Status | Details |
|-----------|--------|---------|
| HL API Connection | ✅ LIVE | Mainnet, address `0x57D4...0A99` |
| HL Account Equity | $32.20 USDC | Fully withdrawable, idle |
| HL Open Positions | **NONE** | `assetPositions: []` |
| HL Margin Used | $0.00 | No active trades |
| Base Hot Wallet | 361.39 USDC | Undeployed |
| Vault TVL (Base) | ~0 | No user deposits |
| Bot Code (engine.py) | ✅ Built | Async V2, event-driven |
| Exchange Integration | ✅ Built | HyperliquidExchange class (SDK) |
| Capital Router | ✅ Built | Multi-chain, Li.Fi bridging |
| Total Protocol Capital | ~$393.59 | All USDC, no ETH exposure |

### Diagnosis

**The basis trade cannot activate because there is no ETH exposure to hedge.**

The delta-neutral strategy requires:
1. **Long leg**: ETH/wstETH deposited in the vault (on-chain)
2. **Short leg**: Matching ETH short on Hyperliquid (off-chain)
3. **Revenue**: Funding rate payments (shorts get paid when funding > 0) + LST staking yield

Currently all $393.59 is in USDC with zero ETH exposure. The $32.2 on HL could open a short, but without a corresponding long position, that would be a directional bet — not delta-neutral.

---

## Activation Plan: Micro Basis Trade (Proof of Concept)

### Goal
Execute a real, end-to-end basis trade with ~$350 total capital to prove the complete pipeline works: deposit → hedge → earn funding → report.

### Capital Split
Based on `capital_router.py` DEFAULT_ALLOCATION (55% to HL):

| Destination | Amount | Purpose |
|-------------|--------|---------|
| Hyperliquid | ~$200 USDC | Short collateral (already $32.2 there) |
| Base Vault | ~$150 USDC → WETH | Long exposure (deposit into vault) |
| Gas Reserve | ~$10 | Base ETH for transactions |

### Step-by-Step Execution

#### Phase 1: Prepare Long Leg (Base)

1. **Swap USDC → WETH on Base**
   ```bash
   cd z:\kerne-new
   python bot/capital_router.py swap 150 USDC -> WETH BASE
   ```
   This converts 150 USDC into ~0.055 WETH (at ~$2,700/ETH).

2. **Deposit WETH into KerneVault**
   The vault at `0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC` accepts WETH deposits via ERC-4626 `deposit()`.
   
   > **NOTE**: The vault's `totalAssets()` call is currently failing. This needs investigation — possible causes:
   > - Contract may be paused
   > - ABI mismatch (vault may use a different function signature)
   > - Contract proxy not initialized
   > 
   > **Action**: Review the deployed vault bytecode on BaseScan and verify the correct ABI before depositing.

#### Phase 2: Prepare Short Leg (Hyperliquid)

3. **Bridge additional USDC to Arbitrum → Hyperliquid**
   ```bash
   # Bridge USDC from Base to Arbitrum
   python bot/capital_router.py bridge 170 USDC BASE -> ARBITRUM
   
   # Deposit USDC from Arbitrum to Hyperliquid
   python bot/capital_router.py deposit-hl 170
   ```
   After: HL balance = ~$200 USDC ($32.2 existing + $170 bridged).

4. **Open ETH Short on Hyperliquid**
   With ~$200 collateral at 3x leverage, the bot can short ~0.22 ETH.
   At 2x leverage (conservative), it can short ~0.15 ETH.
   
   The bot handles this automatically when `run_cycle()` detects vault TVL > 0.

#### Phase 3: Activate the Bot

5. **Start the bot in dry-run first**
   ```bash
   cd z:\kerne-new\bot
   python main.py --dry-run
   ```
   Verify it connects to both Base RPC and Hyperliquid, reads vault TVL, and calculates the correct hedge delta.

6. **Go live**
   ```bash
   python main.py
   ```
   The bot will:
   - Read vault TVL (~0.055 ETH)
   - Open a matching short on HL (~0.055 ETH)
   - Collect funding rate payments every 8 hours
   - Report off-chain value back to the vault

### Expected Revenue (Micro Scale)

| Parameter | Value |
|-----------|-------|
| Notional Exposure | ~$150 (0.055 ETH) |
| Funding Rate (avg) | ~0.005% per 8h period |
| Annual Funding Income | ~$8.21 |
| LST Staking Yield (3.5%) | ~$5.25 (if using wstETH) |
| **Total Expected APY** | **~15-25%** |
| **Daily Revenue** | **~$0.04** |

At this scale, the revenue is negligible ($0.04/day). The purpose is purely **proof of concept** — verifying the complete pipeline works before scaling with larger capital. 

---

## Blockers to Investigate

### 1. Vault `totalAssets()` Failure
The `check_vault_assets.py` script throws `BadFunctionCallOutput`. Possible causes:
- The vault contract at `0xDF9a...C695` may not implement standard ERC-4626 (custom ABI)
- The vault may be in an uninitialized proxy state
- The underlying asset may not be WETH (could be wstETH or something else)

**Investigation**: 
```bash
# Check if contract exists and has code
cast code 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC --rpc-url https://mainnet.base.org

# Check the asset
cast call 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC "asset()(address)" --rpc-url https://mainnet.base.org

# Check if paused
cast call 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC "paused()(bool)" --rpc-url https://mainnet.base.org
```

### 2. Capital Efficiency
With only ~$393, basis trading generates <$0.05/day. The real path to meaningful revenue is:
- **Scale capital to $2,000+** (next PayTrie deposit from Scofield)
- **Aggregator listings** (DappRadar, DeBank) to attract external deposits
- **ZIN solver revenue** (intent spread capture is independent of vault TVL)

### 3. Bot Stability for 24/7 Operation
The bot needs to run continuously. Options:
- Local machine (Scofield's PC) — unreliable
- Docker on a VPS — $5-10/month
- Render.com free tier — possible with keep-alive pings

---

## Priority Recommendation

Given current capital ($393.59):

1. **Investigate vault contract** — Fix the `totalAssets()` issue first
2. **Execute micro basis trade** — Prove the pipeline works ($150 WETH long / $200 HL short)
3. **Focus on aggregator submissions** — DappRadar listing is higher ROI than $0.04/day basis trade
4. **Scale when $2,000+ arrives** — Next PayTrie deposit unlocks meaningful yield

The aggregator submission guide (`docs/runbooks/aggregator_submissions.md`) is the higher-leverage play right now. Getting listed on DappRadar/DeBank can attract external TVL which would make the basis trade worthwhile.