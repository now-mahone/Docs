# APY Framework Assessment - Kerne Protocol
## Analysis of OpenAI's Mathematical Framework for Delta-Neutral Yield Calculation

**Date:** 2026-01-19  
**Author:** Lead Architect  
**Status:** ASSESSMENT COMPLETE - AWAITING APPROVAL

---

## Executive Summary

The mathematical framework provided by OpenAI's model is **institutionally sound and directly applicable** to Kerne. It represents the gold standard for calculating and optimizing APY in delta-neutral strategies. This document assesses the framework against our current implementation and proposes an integration plan.

---

## 1. Framework Analysis

### 1.1 What OpenAI Provided

**Section 1: Realized APY Calculation (NAV-Based)**
```
r_k = (P_fund + P_stake + P_spr - C_k) / E_{k-1}

APY = exp((365/Σ Δt_k) × Σ ln(1+r_k)) - 1
```

Where:
- `P_fund`: Perp funding PnL (USD)
- `P_stake`: Staking rewards (USD)  
- `P_spr`: Spread capture / execution PnL (USD)
- `C_k`: All costs (fees, slippage, gas, etc.)
- `E_{k-1}`: Prior period NAV

**Section 2: Expected APY Model (For Optimization)**
```
dE(t)/E(t) ≈ [L(t)·f(t) + w(t)·s(t) + τ(t)·e(t) - c(·)] dt
```

Where:
- `L(t)`: Perp notional leverage (N/E)
- `w(t)`: Staked spot exposure vs equity (V/E)
- `τ(t)`: Turnover rate vs equity
- `f(t)`: Funding rate
- `s(t)`: Staking yield rate
- `e(t)`: Expected spread edge per traded notional
- `c(·)`: Cost function

**Section 3: Optimization Objective**
```
max E[∫(L·f + w·s + τ·e - c)dt] - λ·Risk(L,w,τ)
```

Subject to:
- Delta-neutrality: |Δ_net| ≤ ε
- Margin/liquidation buffer: L ≤ L_max
- Inventory/LP constraints

---

## 2. Current Kerne Implementation Gap Analysis

### 2.1 What We Have

| Component | Current State | Location |
|-----------|---------------|----------|
| **NAV Tracking** | ✅ `totalAssets()` in ERC-4626 | `KerneVault.sol` |
| **Off-chain Equity** | ✅ `offChainAssets` + `hedgingReserve` | `KerneVault.sol` |
| **Solvency Ratio** | ✅ `getSolvencyRatio()` | `KerneVault.sol` |
| **Projected APY** | ⚠️ Simple BPS storage, no calculation | `KerneVault.sol` |
| **Funding Rate Fetch** | ✅ `get_funding_rate()` | `bot/exchange_manager.py` |
| **Leverage Optimization** | ⚠️ Basic Kelly-like formula | `bot/engine.py` |
| **PnL Decomposition** | ❌ Not implemented | - |
| **Period Return Tracking** | ❌ Not implemented | - |
| **Log-Return APY** | ❌ Not implemented | - |
| **Cost Tracking** | ❌ Not implemented | - |

### 2.2 What We're Missing

1. **PnL Decomposition Engine** - We don't separately track:
   - Funding PnL (`P_fund`)
   - Staking rewards (`P_stake`)
   - Spread capture (`P_spr`)
   - Costs (`C_k`)

2. **Historical NAV Snapshots** - We have `totalAssets()` but no time-series storage

3. **Realized APY Calculator** - The log-return compounding formula isn't implemented

4. **Cost Attribution** - Gas, slippage, trading fees aren't tracked per-period

5. **Risk-Adjusted Optimization** - Current `calculate_optimal_leverage()` is simplistic

---

## 3. Kerne-Specific Additions Required

The OpenAI model correctly asked: *"If you tell me your exact structure..."*

For Kerne's architecture, we need to add:

### 3.1 Basis Risk Term
```python
# The spread between spot LST price and perp mark price
basis_risk_variance = var(spot_price - perp_mark_price)
```

### 3.2 Transfer Latency Risk
```python
# Window of exposure during on-chain ↔ CEX rebalancing
transfer_latency_risk = exposure_during_transfer * volatility * sqrt(transfer_time)
```

### 3.3 LST-Specific Yield Accrual
```python
# LST rebase timing (cbETH, wstETH have different mechanisms)
lst_yield_rate = (lst_price_t1 / lst_price_t0 - 1) / period_days * 365
```

### 3.4 Insurance Fund Contribution
```python
# Currently 10% of gross yield goes to insurance
insurance_cost = gross_yield * insuranceFundBps / 10000
```

### 3.5 Founder Fee Deduction
```python
# Currently 10% performance fee
founder_fee = gross_yield * grossPerformanceFeeBps / 10000
```

---

## 4. Proposed Implementation Plan

### Phase 1: Data Collection Layer (Week 1)
**Location:** `bot/pnl_tracker.py` (NEW)

```python
class PnLTracker:
    """
    Tracks period-by-period PnL decomposition for APY calculation.
    """
    def __init__(self, db_path: str = "bot/data/pnl_history.db"):
        self.db = sqlite3.connect(db_path)
        self._init_schema()
    
    def record_period(self, period_data: PeriodPnL):
        """
        Records one period's PnL breakdown.
        
        period_data = {
            'timestamp': datetime,
            'nav_start': float,      # E_{k-1}
            'nav_end': float,        # E_k
            'funding_pnl': float,    # P_fund
            'staking_pnl': float,    # P_stake
            'spread_pnl': float,     # P_spr
            'trading_fees': float,   # Part of C_k
            'gas_costs': float,      # Part of C_k
            'slippage': float,       # Part of C_k
            'insurance_contrib': float,
            'founder_fee': float,
        }
        """
        pass
    
    def calculate_realized_apy(self, lookback_days: int = 30) -> float:
        """
        Implements the log-return APY formula:
        APY = exp((365/Σ Δt_k) × Σ ln(1+r_k)) - 1
        """
        pass
```

### Phase 2: APY Calculator Service (Week 1-2)
**Location:** `bot/apy_calculator.py` (NEW)

```python
import math
from typing import List
from dataclasses import dataclass

@dataclass
class PeriodReturn:
    timestamp: float
    delta_t_days: float
    r_k: float  # Period return

class APYCalculator:
    """
    Implements the OpenAI framework for APY calculation.
    """
    
    @staticmethod
    def calculate_period_return(
        funding_pnl: float,
        staking_pnl: float,
        spread_pnl: float,
        total_costs: float,
        prior_nav: float
    ) -> float:
        """
        r_k = (P_fund + P_stake + P_spr - C_k) / E_{k-1}
        """
        if prior_nav <= 0:
            return 0.0
        return (funding_pnl + staking_pnl + spread_pnl - total_costs) / prior_nav
    
    @staticmethod
    def calculate_realized_apy(periods: List[PeriodReturn]) -> float:
        """
        APY = exp((365/Σ Δt_k) × Σ ln(1+r_k)) - 1
        
        This is the "best" calculation because it:
        - Compounds correctly
        - Handles time-varying leverage and NAV
        - Avoids double-counting
        """
        if not periods:
            return 0.0
        
        total_time_days = sum(p.delta_t_days for p in periods)
        if total_time_days <= 0:
            return 0.0
        
        log_return_sum = sum(math.log(1 + p.r_k) for p in periods if p.r_k > -1)
        
        annualized_log_return = (365 / total_time_days) * log_return_sum
        apy = math.exp(annualized_log_return) - 1
        
        return apy
    
    @staticmethod
    def calculate_expected_apy(
        leverage: float,           # L(t)
        funding_rate: float,       # f(t) - per 8h
        staking_yield: float,      # s(t) - annual
        spread_edge: float,        # e(t) - per trade
        turnover_rate: float,      # τ(t) - trades per year
        cost_rate: float           # c(·) - annual
    ) -> float:
        """
        Expected APY = exp(L·f_annual + w·s + τ·e - c) - 1
        
        For delta-neutral: w ≈ L (spot exposure matches perp notional)
        """
        # Annualize funding rate (3 periods per day × 365 days)
        annual_funding = funding_rate * 3 * 365
        
        # For delta-neutral, w = L
        w = leverage
        
        # Expected annual log return
        expected_log_return = (
            leverage * annual_funding +
            w * staking_yield +
            turnover_rate * spread_edge -
            cost_rate
        )
        
        return math.exp(expected_log_return) - 1
```

### Phase 3: Leverage Optimizer (Week 2)
**Location:** `bot/leverage_optimizer.py` (NEW)

```python
from scipy.optimize import minimize
import numpy as np

class LeverageOptimizer:
    """
    Implements mean-variance optimization for leverage selection.
    
    max μ(L,w,τ) - (γ/2)·σ²(L,w,τ)
    
    Subject to:
    - Delta-neutrality: |Δ_net| ≤ ε
    - Margin buffer: L ≤ L_max
    - Liquidation probability: P(liq) ≤ p_max
    """
    
    def __init__(
        self,
        risk_aversion: float = 2.5,
        max_leverage: float = 12.0,
        min_leverage: float = 1.5,
        max_liquidation_prob: float = 0.01
    ):
        self.gamma = risk_aversion
        self.L_max = max_leverage
        self.L_min = min_leverage
        self.p_max = max_liquidation_prob
    
    def optimize(
        self,
        funding_rate: float,
        funding_vol: float,
        staking_yield: float,
        basis_vol: float,
        cost_rate: float
    ) -> dict:
        """
        Returns optimal leverage and expected risk-adjusted return.
        """
        def objective(L):
            # Expected return
            mu = L * funding_rate * 3 * 365 + L * staking_yield - cost_rate
            
            # Variance (simplified: funding vol + basis risk)
            sigma_sq = (L ** 2) * (funding_vol ** 2 + basis_vol ** 2)
            
            # Negative because we minimize
            return -(mu - (self.gamma / 2) * sigma_sq)
        
        result = minimize(
            objective,
            x0=[3.0],  # Initial guess
            bounds=[(self.L_min, self.L_max)],
            method='L-BFGS-B'
        )
        
        optimal_L = result.x[0]
        
        return {
            'optimal_leverage': optimal_L,
            'expected_apy': -result.fun,
            'risk_adjusted': True
        }
```

### Phase 4: Integration with Existing Systems (Week 2-3)

1. **Update `bot/engine.py`:**
   - Replace `calculate_optimal_leverage()` with `LeverageOptimizer`
   - Add PnL tracking calls in `run_cycle()`

2. **Update `bot/reporting_service.py`:**
   - Add realized APY to vault reports
   - Add PnL decomposition breakdown

3. **Update `yield-server/`:**
   - Create Kerne adaptor using `APYCalculator`
   - Report both realized and projected APY to DefiLlama

4. **Update `KerneVault.sol`:**
   - Add `getHistoricalAPY()` view function (reads from oracle)
   - Store period snapshots on-chain for transparency

---

## 5. Risk Considerations

### 5.1 What the Framework Handles Well
- ✅ Compounding correctly
- ✅ Time-varying leverage
- ✅ Cost attribution
- ✅ Delta-neutral constraints

### 5.2 What We Need to Add for Kerne
- ⚠️ **Basis Risk:** Spot LST vs perp mark price divergence
- ⚠️ **Transfer Latency:** Exposure during on-chain ↔ CEX transfers
- ⚠️ **LST Rebase Timing:** Different LSTs have different yield accrual
- ⚠️ **Liquidation Path Dependence:** CEX margin calls during volatility

### 5.3 Recommended Risk Parameters
```python
RISK_PARAMS = {
    'risk_aversion_gamma': 2.5,      # Conservative
    'max_leverage': 8.0,              # Below CEX max for safety
    'min_solvency_ratio': 1.05,       # 105% minimum
    'max_basis_deviation': 0.02,      # 2% max basis spread
    'transfer_buffer_hours': 2,       # Assume 2h transfer time
    'funding_vol_lookback_days': 30,  # For variance estimation
}
```

---

## 6. Verdict

### Assessment: **APPROVED FOR IMPLEMENTATION**

The OpenAI framework is mathematically rigorous and directly applicable to Kerne. It represents institutional-grade APY calculation that will:

1. **Improve Accuracy:** Log-return compounding is the correct method
2. **Enable Optimization:** The leverage optimizer will maximize risk-adjusted returns
3. **Increase Transparency:** PnL decomposition shows exactly where yield comes from
4. **Support Compliance:** Institutional partners require this level of reporting

### Recommended Priority: **HIGH**

This should be implemented before mainnet launch to ensure:
- Accurate APY reporting to DefiLlama
- Optimal leverage selection for maximum yield
- Institutional-grade reporting for white-label partners

---

## 7. Next Steps

**Awaiting Scofield's Decision:**

- [ ] **Option A:** Implement full framework (Phases 1-4) - ~2-3 weeks
- [ ] **Option B:** Implement APY calculator only (Phases 1-2) - ~1 week
- [ ] **Option C:** Document for later, focus on other priorities
- [ ] **Option D:** Hybrid - Implement calculator now, optimizer post-launch

---

*Document generated by Lead Architect - 2026-01-19*
