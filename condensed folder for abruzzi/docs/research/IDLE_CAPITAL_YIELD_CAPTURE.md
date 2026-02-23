# Idle Capital Yield Capture - Future Opportunity

## Overview

Deploy idle USDC to Aave V3 during bridge wait times to capture yield.

## Status: NOT IMPLEMENTED (Economically Net-Negative for Current Use Case)

## The Problem

When bridging capital between chains, funds sit idle during the 30-second wait period. This implementation would deploy that idle capital to Aave to earn yield during the wait.

## Why It Was NOT Implemented

### Economic Analysis

| Factor | Value |
|--------|-------|
| Bridge wait time | 30 seconds |
| Gas to deposit to Aave | ~$0.25-1.00 |
| Gas to withdraw from Aave | ~$0.20-0.80 |
| **Total gas overhead** | ~$0.45-1.80 |
| Yield earned in 30 sec @ 4% APY on $1,000 | ~$0.0003 |
| **Net result** | **Loss of ~$0.45-1.80 per move** |

The bridge wait time is too short for Aave yield to cover the gas costs.

## Conditions Required for Implementation

For this feature to be economically viable:

1. **Minimum idle time: 5+ minutes**
   - At 4% APY on $1,000: 5 min = $0.003 yield
   - Still barely covers gas, but for larger amounts ($10,000+) it becomes viable

2. **Minimum capital per move: $10,000+**
   - $10,000 @ 4% APY for 5 min = $0.03 yield
   - Still marginal, but for very long waits (30+ min) it could work

3. **Lower gas costs (L2 optimization)**
   - If Base/Arbitrum gas drops to <$0.10 per TX
   - Break-even time drops to ~2-3 minutes

4. **Hyperliquid deposits (longer settlement)**
   - HL deposits take 10-30 minutes to settle
   - This would be the ideal use case for idle capital yield

## Implementation (Reference Only)

### Files Created (then rolled back)
- `bot/aave_integration.py` - Aave V3 deposit/withdraw functions
- `bot/capital_router.py` - Modified with `IDLE_CAPITAL_CONFIG`

### Configuration
```python
IDLE_CAPITAL_CONFIG = {
    "enabled": False,  # Keep disabled until conditions met
    "min_amount": 100.0,
    "min_idle_time": 300,  # 5 minutes
    "supported_chains": ["BASE", "ARBITRUM"],
    "max_deploy_ratio": 0.10,
}
```

### Aave V3 Addresses
- Base Pool: `0x87E7380ee004305d61460B69933Bb25C226D0B63`
- Arbitrum Pool: `0x794a61358D6845594F94dc1DB02A252b5b4814aD`

## Potential Upside

If conditions are met (longer waits, lower gas, larger capital):

| Scenario | Idle Time | Capital | Yield Earned | Gas Cost | Net |
|----------|-----------|---------|--------------|----------|-----|
| Current | 30 sec | $1,000 | $0.0003 | $0.50 | -$0.50 |
| Longer wait | 10 min | $10,000 | $0.19 | $0.50 | -$0.31 |
| HL deposit | 30 min | $50,000 | $2.85 | $0.50 | +$2.35 |
| Ideal | 30 min | $100,000 | $5.70 | $0.50 | +$5.20 |

## Recommendation

**Revisit this feature when:**
1. Protocol has longer idle periods (Hyperliquid deposits, multi-step bridges)
2. Gas costs on L2s decrease significantly
3. Aave yields increase substantially (>10% APY)

For now, the complexity and gas costs outweigh the minimal yield benefit.

---

Created: 2026-02-19
Status: Rolled back - economically net-negative for current use case