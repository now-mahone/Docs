// Created: 2026-02-19
# Liquidation Cascade Mitigation Plan

## Problem Statement

**Current State (2nd Monte Carlo Run):**
- Liquidation Cascades: 74 failures (78.7% of all failures)
- Mean Min CR: 1.33x (only 11% buffer above 1.20x liquidation threshold)
- Mean Final TVL: $103.53M (down from $119.40M in 1st run)

**Root Cause Analysis:**

From the simulation code, liquidation cascades trigger when:
1. Collateral ratio drops below 1.20x threshold
2. Liquidation count exceeds 10 events
3. CR remains below 1.10x after liquidations

The cascade effect:
```
ETH price drop → CR drops below threshold → Forced liquidation
→ TVL decreases → kUSD supply decreases → CR may drop further
→ More liquidations → CASCADE → Protocol failure
```

---

## Mitigation Strategies (Ranked by Impact)

### Strategy 1: Dynamic Collateral Ratio Buffer (HIGH IMPACT)

**Concept:** Automatically increase collateral ratio when volatility is detected.

**Implementation:**
```solidity
// In KerneVault.sol
uint256 public baseCollateralRatio = 1.50e18; // 150%
uint256 public dynamicBuffer = 0; // Additional buffer during stress

function getEffectiveCollateralRatio() public view returns (uint256) {
    return baseCollateralRatio + dynamicBuffer;
}

function updateDynamicBuffer(uint256 volatilityIndex) internal {
    // If ETH volatility > threshold, increase buffer
    if (volatilityIndex > VOLATILITY_THRESHOLD) {
        dynamicBuffer = 0.10e18; // Add 10% buffer (total 160%)
    } else {
        dynamicBuffer = 0;
    }
}
```

**Expected Impact:** 30-50% reduction in liquidation cascades

---

### Strategy 2: Circuit Breaker Pause (HIGH IMPACT)

**Concept:** Pause withdrawals/deposits when CR approaches dangerous levels.

**Implementation:**
```solidity
// In KerneVault.sol
uint256 public constant CRITICAL_CR = 1.25e18; // 125%
bool public circuitBreakerActive = false;

event CircuitBreakerTriggered(uint256 cr, uint256 timestamp);

modifier notInCircuitBreaker() {
    require(!circuitBreakerActive, "Circuit breaker active");
    _;
}

function checkCircuitBreaker() internal {
    uint256 cr = calculateCollateralRatio();
    
    if (cr < CRITICAL_CR && !circuitBreakerActive) {
        circuitBreakerActive = true;
        emit CircuitBreakerTriggered(cr, block.timestamp);
        // Pause for 4 hours to allow recovery
        _pause();
    } else if (cr >= 1.35e18 && circuitBreakerActive) {
        circuitBreakerActive = false;
        _unpause();
    }
}
```

**Expected Impact:** 40-60% reduction in liquidation cascades

---

### Strategy 3: Gradual Liquidation (MEDIUM IMPACT)

**Concept:** Instead of large single liquidations, spread over time.

**Implementation:**
```solidity
// In KerneVault.sol
uint256 public constant MAX_LIQUIDATION_PER_HOUR = 5; // 5% of TVL max
mapping(uint256 => uint256) public hourlyLiquidations;

function canLiquidate(uint256 amount) internal view returns (bool) {
    uint256 hour = block.timestamp / 3600;
    uint256 alreadyLiquidated = hourlyLiquidations[hour];
    uint256 maxAllowed = (totalAssets() * MAX_LIQUIDATION_PER_HOUR) / 100;
    
    return (alreadyLiquidated + amount) <= maxAllowed;
}
```

**Expected Impact:** 20-30% reduction in cascade severity

---

### Strategy 4: Emergency Insurance Fund Injection (MEDIUM IMPACT)

**Concept:** Insurance fund automatically injects capital when CR is critical.

**Implementation:**
```solidity
// In KerneInsuranceFund.sol
uint256 public constant CRITICAL_CR = 1.15e18; // 115%

function emergencyInject(address vault) external returns (uint256) {
    require(msg.sender == address(this), "Only self-call");
    
    uint256 cr = KerneVault(vault).calculateCollateralRatio();
    require(cr < CRITICAL_CR, "CR not critical");
    
    // Calculate injection needed to reach 1.30x
    uint256 deficit = calculateDeficit(vault);
    uint256 injection = min(deficit, availableFunds());
    
    // Transfer to vault
    asset.transfer(vault, injection);
    
    emit EmergencyInjection(vault, injection, cr);
    return injection;
}
```

**Expected Impact:** 15-25% reduction in failures

---

### Strategy 5: Reduce ETH-Correlated Collateral (LOW-MEDIUM IMPACT)

**Concept:** Diversify collateral away from pure ETH exposure.

**Current Collateral Weights:**
```
wstETH: 30%
rETH: 15%
cbETH: 10%
eETH: 10%
weETH: 5%
USDC: 20%
sDAI: 10%
```

**Proposed Weights:**
```
wstETH: 20% (-10%)
rETH: 10% (-5%)
cbETH: 10% (same)
eETH: 5% (-5%)
weETH: 5% (same)
USDC: 35% (+15%)
sDAI: 15% (+5%)
```

**Expected Impact:** 10-20% reduction in CR volatility

---

## Implementation Priority

| Priority | Strategy | Effort | Impact | Files to Modify |
|----------|----------|--------|--------|-----------------|
| 1 | Circuit Breaker Pause | Medium | HIGH | KerneVault.sol |
| 2 | Dynamic CR Buffer | Medium | HIGH | KerneVault.sol |
| 3 | Gradual Liquidation | Low | MEDIUM | KerneVault.sol |
| 4 | Insurance Injection | Medium | MEDIUM | KerneInsuranceFund.sol |
| 5 | Collateral Diversification | Low | LOW | Simulation config |

---

## Implementation Plan

### Phase 1: Circuit Breaker (Week 1)
1. Add `circuitBreakerActive` state variable
2. Add `CRITICAL_CR` constant (1.25x)
3. Implement `checkCircuitBreaker()` function
4. Add `notInCircuitBreaker` modifier to deposit/withdraw
5. Add events and tests
6. Deploy and verify

### Phase 2: Dynamic Buffer (Week 1-2)
1. Add `dynamicBuffer` state variable
2. Create volatility oracle integration
3. Implement `updateDynamicBuffer()` function
4. Modify `getEffectiveCollateralRatio()`
5. Add tests
6. Deploy and verify

### Phase 3: Gradual Liquidation (Week 2)
1. Add `MAX_LIQUIDATION_PER_HOUR` constant
2. Add `hourlyLiquidations` mapping
3. Implement `canLiquidate()` check
4. Modify liquidation logic
5. Add tests
6. Deploy and verify

### Phase 4: Insurance Integration (Week 2-3)
1. Add `CRITICAL_CR` constant to InsuranceFund
2. Implement `emergencyInject()` function
3. Add automatic trigger from vault
4. Add tests
5. Deploy and verify

---

## Expected Outcomes

| Metric | Current | After Implementation |
|--------|---------|---------------------|
| Liquidation Cascade Failures | 74 (78.7%) | ~15-25 (25-40%) |
| Survival Rate | 99.06% | 99.5%+ |
| Mean Min CR | 1.33x | 1.40x+ |
| Mean Final TVL | $103.53M | $115M+ |

---

## Next Steps

1. **Approve plan** — Confirm which strategies to implement
2. **Start with Circuit Breaker** — Highest impact, medium effort
3. **Run new Monte Carlo** — Validate improvements after each phase
4. **Deploy to mainnet** — After testing

**Ready to implement upon approval.**