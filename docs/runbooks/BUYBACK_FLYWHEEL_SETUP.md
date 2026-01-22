# KERNE Token Buyback Flywheel - Setup & Operations Runbook
> Created: 2026-01-21
> Last Updated: 2026-01-21

## Overview

The KERNE Token Buyback Flywheel is an automated system that creates continuous deflationary pressure on KERNE governance token supply by using 100% of protocol revenue to buy back and burn tokens.

### Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       KERNE BUYBACK FLYWHEEL                            │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│   Protocol Revenue                    Buyback Execution                 │
│   ──────────────────                  ──────────────────                │
│                                                                         │
│   ┌──────────────┐                    ┌──────────────────┐              │
│   │ KerneVault   │──── WETH ────────► │                  │              │
│   │ (Yield Fees) │                    │  KerneTreasury   │              │
│   └──────────────┘                    │  0xB65644...     │              │
│                                       │                  │              │
│   ┌──────────────┐                    │  ┌────────────┐  │              │
│   │ ZIN Pool     │──── WETH/USDC ───► │  │ Aerodrome  │  │              │
│   │ (MEV Profit) │                    │  │  Swap      │  │              │
│   └──────────────┘                    │  └─────┬──────┘  │              │
│                                       │        │         │              │
│   ┌──────────────┐                    │        ▼         │              │
│   │ PSM Fees     │──── USDC ────────► │  ┌────────────┐  │              │
│   │ (Mint/Redeem)│                    │  │ KERNE Token│  │              │
│   └──────────────┘                    │  │ Purchased  │  │              │
│                                       │  └─────┬──────┘  │              │
│                                       └────────┼─────────┘              │
│                                                │                        │
│                              ┌─────────────────┼─────────────────┐      │
│                              │                 │                 │      │
│                              ▼                 ▼                 ▼      │
│                        ┌──────────┐     ┌──────────┐     ┌──────────┐   │
│                        │  BURN    │     │ STAKING  │     │ ECOSYSTEM│   │
│                        │  (Dead   │     │ REWARDS  │     │   FUND   │   │
│                        │  Address)│     │          │     │          │   │
│                        └──────────┘     └──────────┘     └──────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Contract Addresses (Base Mainnet)

| Contract | Address | Purpose |
|----------|---------|---------|
| KerneTreasury | `0xB656440287f8A1112558D3df915b23326e9b89ec` | Revenue aggregation & buyback execution |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | Governance token being bought back |
| KERNE Staking | `0x032Af1631671126A689614c0c957De774b45D582` | Optional destination for purchased KERNE |
| Aerodrome Router | `0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43` | DEX router for swaps |
| WETH | `0x4200000000000000000000000000000000000006` | Wrapped ETH (Base) |
| USDC | `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913` | USD Coin (Base) |

---

## Prerequisites

### 1. Treasury Configuration

Before the buyback system can operate, the Treasury must be configured:

```bash
# Run the setup script (requires admin privileges)
forge script script/SetupTreasuryBuyback.s.sol:SetupTreasuryBuyback \
  --rpc-url $BASE_RPC_URL \
  --private-key $ADMIN_PRIVATE_KEY \
  --broadcast
```

This script:
- Approves WETH for buybacks (infinite approval to Aerodrome Router)
- Approves USDC for buybacks (infinite approval to Aerodrome Router)
- Sets USDC→WETH routing hop (for USDC→WETH→KERNE multi-hop swaps)
- Verifies Treasury configuration

### 2. KERNE/WETH Liquidity Pool

Ensure sufficient liquidity exists on Aerodrome:

```bash
# Check if pool exists
cast call 0x420DD381b31aEf6683db6B902084cB0FFECe40Da \
  "getPool(address,address,bool)" \
  0x4200000000000000000000000000000000000006 \
  0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 \
  false \
  --rpc-url https://mainnet.base.org
```

If no pool exists, create one:
```bash
forge script script/SetupTreasuryBuyback.s.sol:CreateKernePool \
  --rpc-url $BASE_RPC_URL \
  --private-key $ADMIN_PRIVATE_KEY \
  --broadcast
```

### 3. Bot Environment Configuration

Update your `bot/.env` file:

```bash
# Treasury & Token addresses
TREASURY_ADDRESS=0xB656440287f8A1112558D3df915b23326e9b89ec
KERNE_TOKEN_ADDRESS=0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340
KERNE_STAKING_ADDRESS=0x032Af1631671126A689614c0c957De774b45D582

# Buyback thresholds
BUYBACK_MIN_WETH=100000000000000000  # 0.1 ETH
BUYBACK_MIN_USDC=250000000           # 250 USDC
BUYBACK_COOLDOWN_HOURS=24            # Daily buybacks

# Token addresses
WETH_ADDRESS=0x4200000000000000000000000000000000000006
USDC_ADDRESS=0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913

# Aerodrome
AERODROME_ROUTER=0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43
BUYBACK_SLIPPAGE_BPS=500  # 5%
```

---

## Operations

### Automatic Operation (Recommended)

The buyback system runs automatically as part of the main bot loop:

```bash
cd bot
python main.py
```

The engine will:
1. Check buyback conditions every cycle
2. Execute buyback if thresholds are met and cooldown has passed
3. Log all buybacks to `bot/data/buyback_log.json`
4. Post Discord alerts for executed buybacks

### Manual Operations

#### Check Buyback Status
```python
from bot.engine import HedgingEngine

engine = HedgingEngine()
stats = engine.get_buyback_stats()
print(f"Total WETH spent: {stats['total_weth_spent_formatted']} ETH")
print(f"Total USDC spent: {stats['total_usdc_spent_formatted']} USDC")
print(f"Total KERNE bought: {stats['total_kerne_bought_formatted']} KERNE")
print(f"Lifetime buybacks: {stats['lifetime_buybacks']}")
```

#### Execute Manual Buyback (Cast)
```bash
# Check Treasury balances
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "getTreasuryBalances()" \
  --rpc-url https://mainnet.base.org

# Preview buyback (check expected output)
cast call 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "previewBuyback(address,uint256)" \
  0x4200000000000000000000000000000000000006 \
  100000000000000000 \
  --rpc-url https://mainnet.base.org

# Execute buyback (requires STRATEGIST_ROLE)
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "executeBuyback(address,uint256,uint256)" \
  0x4200000000000000000000000000000000000006 \
  100000000000000000 \
  0 \
  --rpc-url https://mainnet.base.org \
  --private-key $STRATEGIST_PRIVATE_KEY
```

#### Combined Distribute + Buyback
```bash
# Distribute and buyback in one tx (sends 80% to founder, 20% to buyback, then executes)
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "distributeAndBuyback(address)" \
  0x4200000000000000000000000000000000000006 \
  --rpc-url https://mainnet.base.org \
  --private-key $STRATEGIST_PRIVATE_KEY
```

---

## Monitoring

### Discord Alerts

Buyback events trigger Discord notifications:
- ✅ **Successful buyback**: Token, amount spent, KERNE received, tx hash
- ⚠️ **Pending conditions**: Waiting for threshold or cooldown
- ❌ **Failed buyback**: Error message and suggested action

### Log Files

Buyback history is stored in `bot/data/buyback_log.json`:

```json
{
  "buybacks": [
    {
      "timestamp": "2026-01-21T18:30:00Z",
      "token_in": "WETH",
      "amount_in": "0.5 ETH",
      "amount_in_wei": "500000000000000000",
      "kerne_received": "10000.5",
      "kerne_received_wei": "10000500000000000000000",
      "tx_hash": "0x...",
      "block_number": 12345678
    }
  ],
  "lifetime_stats": {
    "total_weth_spent_wei": "2500000000000000000",
    "total_usdc_spent": "5000000000",
    "total_kerne_bought_wei": "125000000000000000000000",
    "total_buybacks": 12
  },
  "last_buyback_timestamp": 1737500000
}
```

### On-Chain Verification

```bash
# Check buyback history via Treasury events
cast logs \
  --from-block 21000000 \
  --address 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "BuybackExecuted(address,uint256,uint256)" \
  --rpc-url https://mainnet.base.org
```

---

## Troubleshooting

### Common Issues

#### 1. "Insufficient liquidity" error
**Cause**: KERNE/WETH pool on Aerodrome has low liquidity
**Solution**: Add liquidity to the pool or reduce buyback amount

#### 2. "Slippage too high" error
**Cause**: Large price impact on swap
**Solution**: 
- Reduce buyback amount
- Increase `BUYBACK_SLIPPAGE_BPS` (not recommended)
- Wait for more liquidity

#### 3. "AccessControl: account missing role" error
**Cause**: Bot wallet doesn't have STRATEGIST_ROLE
**Solution**: 
```bash
cast send 0xB656440287f8A1112558D3df915b23326e9b89ec \
  "grantRole(bytes32,address)" \
  0x17a8e30262c1f919c33056d877a3c22b95c2f5e4dac44683c1c2323cd79fbdb0 \
  $BOT_ADDRESS \
  --rpc-url https://mainnet.base.org \
  --private-key $ADMIN_PRIVATE_KEY
```

#### 4. "Token not approved for buyback" error
**Cause**: Treasury hasn't approved token for Aerodrome Router
**Solution**: Run `SetupTreasuryBuyback` script

#### 5. Buyback not executing despite having balance
**Cause**: Cooldown period hasn't elapsed
**Solution**: Check `last_buyback_timestamp` in buyback log, wait for cooldown

---

## Security Considerations

### Access Control
- Only `STRATEGIST_ROLE` can execute buybacks
- Only `DEFAULT_ADMIN_ROLE` can configure Treasury parameters
- Bot wallet should have minimal permissions

### Slippage Protection
- All buybacks have maximum slippage of 5% (configurable)
- Use `previewBuyback()` to check expected output before executing
- Cancel if price impact exceeds acceptable threshold

### Rate Limiting
- Default 24-hour cooldown between buybacks
- Prevents rapid depletion of Treasury
- Configurable via `BUYBACK_COOLDOWN_HOURS`

### MEV Protection
- Consider using Flashbots RPC for large buybacks
- Split large buybacks into smaller tranches
- Monitor for sandwich attacks

---

## Future Enhancements

1. **TWAP Buybacks**: Split large buybacks over time to reduce price impact
2. **Conditional Buybacks**: Only buy when KERNE price is below moving average
3. **Multi-DEX Routing**: Use 1inch/Paraswap for better rates
4. **Auto-Burn Integration**: Automatically burn purchased KERNE
5. **Governance Voting**: Let stakers vote on buyback vs. distribution ratio

---

## Quick Reference

| Action | Command |
|--------|---------|
| Check Treasury balance | `cast call 0xB65... "getTreasuryBalances()"` |
| Preview buyback | `cast call 0xB65... "previewBuyback(address,uint256)" <token> <amount>` |
| Execute buyback | `cast send 0xB65... "executeBuyback(address,uint256,uint256)" ...` |
| Check buyback stats | Bot: `engine.get_buyback_stats()` |
| View buyback log | `cat bot/data/buyback_log.json` |
| Run setup script | `forge script script/SetupTreasuryBuyback.s.sol:SetupTreasuryBuyback ...` |

---

*This runbook is maintained by the Kerne Protocol team. For questions, contact the engineering team.*
