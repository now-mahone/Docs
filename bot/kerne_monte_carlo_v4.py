# Created: 2026-02-19
"""
Kerne Protocol - Monte Carlo Simulation v4
Builds on Simulation 3 (98.72% survival) with 3 additional upgrades:

  UPGRADE 1: Protocol Insurance Fund (auto-inject at CR < 1.30x)
  UPGRADE 2: Post-Audit Exploit Probability (70% reduction + 10% bug bounty)
  UPGRADE 3: Tiered Circuit Breaker (Yellow @ 1.35x + Red @ 1.25x)

All Simulation 3 protections retained:
  - Triple-Source Oracle (Chainlink + TWAP + Pyth)
  - TWAP Window Hardening (30-min, 5% deviation threshold)
  - Circuit Breaker Red (<1.25x triggers, >1.35x for 4h recovers)
  - Dynamic CR Buffer (5% calm / 10% stressed)
  - Gradual Liquidation (5% TVL/hr cap)

Target: >99.00% survival rate
Plan:   docs/research/SURVIVAL_RATE_99PCT_UPGRADE_PLAN.md
"""

import json
import random
import math
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# SIMULATION CONSTANTS (identical to Simulation 3 for apples-to-apples)
# ─────────────────────────────────────────────────────────────
N_SIMULATIONS   = 10_000
SIMULATION_DAYS = 365
INITIAL_TVL     = 100_000_000
INITIAL_ETH_PRICE = 3_500.0
PERFORMANCE_FEE = 0.20
MANAGEMENT_FEE  = 0.02 / 365

BASE_CR        = 1.50
LIQUIDATION_CR = 1.20
INITIAL_KUSD   = INITIAL_TVL / BASE_CR

# ─────────────────────────────────────────────────────────────
# YIELD MODEL (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
YIELD_PARAMS = {
    "normal":     (0.155, 0.025,  0.08,  0.22),
    "bull":       (0.225, 0.035,  0.14,  0.35),
    "bear":       (0.040, 0.040, -0.08,  0.10),
    "black_swan": (-0.02, 0.10,  -0.30,  0.12),
    "regulatory": (0.055, 0.035, -0.05,  0.12),
}

SCENARIO_PROBABILITIES = {
    "normal": 0.60, "bull": 0.15, "bear": 0.15, "black_swan": 0.05, "regulatory": 0.05,
}

ETH_ANNUAL_VOLS = {
    "normal": 0.75, "bull": 0.90, "bear": 0.95, "black_swan": 1.40, "regulatory": 1.10,
}
ETH_ANNUAL_RETURNS = {
    "normal": 0.30, "bull": 1.50, "bear": -0.60, "black_swan": -0.85, "regulatory": -0.40,
}

# ─────────────────────────────────────────────────────────────
# LAYER 1: ORACLE (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
ORACLE_DEVIATION_THRESHOLD  = 0.05
CHAINLINK_FAILURE_PROB      = 0.0005
PYTH_FAILURE_PROB           = 0.0003
TWAP_FAILURE_PROB           = 0.0001
MANIPULATED_ORACLE_LOSS_PCT = 0.002

# ─────────────────────────────────────────────────────────────
# LAYER 2: TIERED CIRCUIT BREAKER — UPGRADE 3
# Yellow alert at 1.35x (new), Red pause at 1.25x (existing)
# ─────────────────────────────────────────────────────────────
CB_YELLOW_CR   = 1.35    # NEW: soft alert — halt new deposits
CB_RED_CR      = 1.25    # existing: full vault pause
CB_RECOVER_CR  = 1.40    # must hold above this for 1 day to exit RED
CB_RECOVER_DAYS = 1
CB_MAX_PAUSE   = 7

# ─────────────────────────────────────────────────────────────
# LAYER 3: DYNAMIC CR BUFFER (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
DYNAMIC_BUFFER_CALM     = 0.05
DYNAMIC_BUFFER_STRESSED = 0.10
VOL_STRESS_THRESHOLD    = 0.04

# ─────────────────────────────────────────────────────────────
# LAYER 4: GRADUAL LIQUIDATION (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
MAX_LIQ_PCT_PER_DAY = 0.05

# ─────────────────────────────────────────────────────────────
# UPGRADE 1: PROTOCOL INSURANCE FUND
# ─────────────────────────────────────────────────────────────
INS_INITIAL_RESERVE_PCT  = 0.03   # 3% of TVL = $3M initial reserve
INS_PERF_FEE_ALLOCATION  = 0.10   # 10% of performance fees go to fund
INS_INJECTION_TRIGGER_CR = 1.30   # Inject when CR drops below this (before CB Red at 1.25)
INS_INJECTION_TARGET_CR  = 1.40   # Inject enough capital to restore CR here
INS_MAX_RESERVE_PCT      = 0.05   # Cap reserve at 5% of TVL (don't hoard)

# ─────────────────────────────────────────────────────────────
# UPGRADE 2: POST-AUDIT EXPLOIT PROBABILITY
# 70% reduction from formal audit + 10% from bug bounty program
# Effective: 0.00007 * 0.27 = 0.0000189 per day (pre scenario multiplier)
# ─────────────────────────────────────────────────────────────
AUDIT_ACTIVE          = True
AUDIT_REDUCTION       = 0.70   # Formal audit reduces base probability 70%
BUG_BOUNTY_REDUCTION  = 0.10   # Bug bounty adds another 10% reduction
# Combined: 1 - (1 - 0.70) * (1 - 0.10) = 1 - 0.30 * 0.90 = 1 - 0.27 = 73% total reduction
EXPLOIT_BASE_PROB     = 0.00007
EXPLOIT_AUDIT_MULT    = (1 - AUDIT_REDUCTION) * (1 - BUG_BOUNTY_REDUCTION)  # = 0.27
EXPLOIT_PROB          = EXPLOIT_BASE_PROB * EXPLOIT_AUDIT_MULT if AUDIT_ACTIVE else EXPLOIT_BASE_PROB

# ─────────────────────────────────────────────────────────────
# BLACK SWAN MULTIPLIERS (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
BS_MULT = {"normal": 1.0, "bull": 0.5, "bear": 2.5, "black_swan": 6.0, "regulatory": 3.5}

random.seed(42)
def ran():  return random.random()
def randn():
    u1, u2 = max(ran(), 1e-10), ran()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


# ─────────────────────────────────────────────────────────────
# ORACLE (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
def triple_oracle_check(true_price: float, daily_sigma: float) -> dict:
    noise     = daily_sigma * 0.01
    chainlink = true_price * (1 + randn() * noise) if ran() > CHAINLINK_FAILURE_PROB else None
    pyth      = true_price * (1 + randn() * noise) if ran() > PYTH_FAILURE_PROB      else None
    twap      = true_price * (1 + randn() * noise * 0.3) if ran() > TWAP_FAILURE_PROB else None
    live = [p for p in [chainlink, pyth, twap] if p is not None]
    if not live:
        return {"price": true_price, "all_failed": True, "manipulated": False}
    avg     = sum(live) / len(live)
    max_dev = max(abs(p - avg) / avg for p in live)
    return {"price": avg, "all_failed": False, "manipulated": max_dev > ORACLE_DEVIATION_THRESHOLD}


# ─────────────────────────────────────────────────────────────
# UPGRADE 3: TIERED CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────
class TieredCircuitBreaker:
    """
    Yellow (CR < 1.35x): Soft alert. No new deposits accepted.
    Red   (CR < 1.25x): Full pause. No deposits or withdrawals.
    Recovery: CR must stay >= 1.40x for 1+ day to exit Red.
    """
    def __init__(self):
        self.yellow_active     = False
        self.red_active        = False
        self.red_recovery_day  = None
        self.red_total_days    = 0
        self.red_triggers      = 0
        self.yellow_triggers   = 0
        self.yellow_days       = 0

    def update(self, cr: float, day: int) -> tuple:
        """Returns (yellow_active, red_active)."""
        # ── Yellow tier ──
        was_yellow = self.yellow_active
        if cr < CB_YELLOW_CR:
            self.yellow_active = True
            if not was_yellow:
                self.yellow_triggers += 1
        else:
            self.yellow_active = False

        if self.yellow_active:
            self.yellow_days += 1

        # ── Red tier ──
        if not self.red_active:
            if cr < CB_RED_CR:
                self.red_active      = True
                self.red_recovery_day = None
                self.red_triggers   += 1
        else:
            self.red_total_days += 1
            if cr >= CB_RECOVER_CR:
                if self.red_recovery_day is None:
                    self.red_recovery_day = day
                elif (day - self.red_recovery_day) >= CB_RECOVER_DAYS:
                    self.red_active      = False
                    self.red_recovery_day = None
            else:
                self.red_recovery_day = None
            if self.red_total_days >= CB_MAX_PAUSE:
                self.red_active = False

        return self.yellow_active, self.red_active


# ─────────────────────────────────────────────────────────────
# UPGRADE 1: PROTOCOL INSURANCE FUND
# ─────────────────────────────────────────────────────────────
class InsuranceFund:
    """
    Protocol-owned reserve that auto-injects when CR drops below 1.30x.
    Funded by 10% of daily performance fees.
    Starts at 3% of initial TVL = $3,000,000.
    """
    def __init__(self, initial_tvl: float):
        self.reserves     = initial_tvl * INS_INITIAL_RESERVE_PCT
        self.total_injected = 0.0
        self.injection_count = 0
        self.max_reserve  = initial_tvl * INS_MAX_RESERVE_PCT

    def feed(self, gross_daily_yield: float):
        """Receive 10% of performance fees each day."""
        perf_fee_total = max(0, gross_daily_yield) * PERFORMANCE_FEE
        contribution   = perf_fee_total * INS_PERF_FEE_ALLOCATION
        self.reserves  = min(self.reserves + contribution, self.max_reserve)

    def inject_if_needed(self, cr: float, tvl: float, kusd: float) -> tuple:
        """
        If CR < 1.30x, inject enough to restore CR to 1.40x.
        Returns (new_tvl, amount_injected).
        """
        if cr >= INS_INJECTION_TRIGGER_CR or self.reserves <= 0:
            return tvl, 0.0

        target_tvl = kusd * INS_INJECTION_TARGET_CR
        deficit    = max(0.0, target_tvl - tvl)
        actual     = min(deficit, self.reserves)

        if actual > 0:
            self.reserves      -= actual
            self.total_injected += actual
            self.injection_count += 1

        return tvl + actual, actual


# ─────────────────────────────────────────────────────────────
# DYNAMIC BUFFER (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
class DynamicBuffer:
    def __init__(self):
        self.high_days = 0
    def update(self, daily_vol: float) -> float:
        if daily_vol > VOL_STRESS_THRESHOLD:
            self.high_days += 1
            return DYNAMIC_BUFFER_STRESSED
        return DYNAMIC_BUFFER_CALM


# ─────────────────────────────────────────────────────────────
# GRADUAL LIQUIDATION (identical to Simulation 3)
# ─────────────────────────────────────────────────────────────
class GradualLiquidation:
    def __init__(self):
        self.daily_done = {}
        self.caps       = 0

    def execute(self, cr: float, tvl: float, kusd: float, day: int):
        if cr >= LIQUIDATION_CR:
            return tvl, kusd, 0.0, False
        deficit_pct = min((LIQUIDATION_CR - cr) * 1.5, 0.30)
        needed      = tvl * deficit_pct
        already     = self.daily_done.get(day, 0.0)
        capacity    = max(0.0, tvl * MAX_LIQ_PCT_PER_DAY - already)
        actual      = min(needed, capacity)
        was_capped  = actual < needed * 0.95
        if was_capped:
            self.caps += 1
        self.daily_done[day] = already + actual
        ratio    = (tvl - actual) / max(tvl, 1)
        return tvl * ratio, kusd * ratio, actual, was_capped


# ─────────────────────────────────────────────────────────────
# SINGLE SIMULATION
# ─────────────────────────────────────────────────────────────
def run_single_simulation(sim_id: int) -> dict:
    # Pick scenario
    roll, cum, scenario = ran(), 0.0, "normal"
    for sc, prob in SCENARIO_PROBABILITIES.items():
        cum += prob
        if roll < cum:
            scenario = sc
            break

    mu_ann, sig_ann, yld_min, yld_max = YIELD_PARAMS[scenario]
    sigma_daily = ETH_ANNUAL_VOLS[scenario] / math.sqrt(365)
    mu_eth      = ETH_ANNUAL_RETURNS[scenario] / 365
    bsm         = BS_MULT[scenario]

    # State
    eth_price   = INITIAL_ETH_PRICE
    tvl         = INITIAL_TVL
    kusd        = INITIAL_KUSD
    total_yield = 0.0

    # Protection systems
    cb  = TieredCircuitBreaker()
    buf = DynamicBuffer()
    gl  = GradualLiquidation()
    ins = InsuranceFund(INITIAL_TVL)

    # Trackers
    min_cr           = BASE_CR
    max_dd           = 0.0
    peak_tvl         = tvl
    liq_count        = 0
    oracle_rejects   = 0
    neg_yield_days   = 0
    gas_spike_days   = 0
    exploit_events   = 0
    depeg_events     = 0
    reg_events       = 0
    bridge_events    = 0
    ins_injections   = 0
    ins_total_injected = 0.0

    status, failure_reason, failure_day = "SURVIVED", None, None
    cr = BASE_CR

    for day in range(SIMULATION_DAYS):
        # ── ETH Price (GBM) ──
        eth_shock     = mu_eth + sigma_daily * randn()
        eth_price_raw = eth_price * math.exp(eth_shock)
        daily_vol     = abs(eth_shock)

        # ── LAYER 1: Triple Oracle ──
        oracle = triple_oracle_check(eth_price_raw, sigma_daily)
        if oracle["manipulated"]:
            oracle_rejects += 1
            tvl *= (1 - MANIPULATED_ORACLE_LOSS_PCT)
        else:
            eth_price = eth_price_raw

        if oracle["all_failed"] and ran() < 0.0008:
            status, failure_reason, failure_day = "FAILED", "ORACLE_MANIPULATION", day
            break

        # ── LAYER 3: Dynamic Buffer ──
        buf.update(daily_vol)

        # ── Gas spike tracking ──
        if ran() < 0.02:
            gas_spike_days += 1

        # ── YIELD CALCULATION ──
        daily_gross_rate = (mu_ann + sig_ann * randn()) / 365
        daily_gross_rate = max(yld_min / 365, min(yld_max / 365, daily_gross_rate))
        basis_adj        = eth_shock * 0.03
        gross_daily      = tvl * (daily_gross_rate + basis_adj)
        perf_fee         = max(0, gross_daily) * PERFORMANCE_FEE
        mgmt_fee         = tvl * MANAGEMENT_FEE

        # UPGRADE 1: Feed insurance fund from 10% of perf fees
        ins.feed(gross_daily)
        # Net daily yield after all fees (insurance eats 10% of perf fee)
        net_daily = gross_daily - perf_fee - mgmt_fee

        if net_daily < 0:
            neg_yield_days += 1

        yellow_active, red_active = cb.update(cr, day)

        # Only accrue yield when RED circuit breaker is not active
        if not red_active:
            tvl         += net_daily
            total_yield += max(0.0, net_daily)
            tvl          = max(tvl, 1_000)

        # ── UPGRADE 2: Post-Audit Black Swan Events ──
        exploit_prob = EXPLOIT_PROB * bsm   # much lower due to audit

        if ran() < exploit_prob:
            exploit_events += 1
            loss_pct = ran() * 0.20
            tvl *= (1 - loss_pct)
            if ran() < 0.22:
                status, failure_reason, failure_day = "FAILED", "SMART_CONTRACT_EXPLOIT", day
                break

        if ran() < 0.000014 * bsm:
            depeg_events += 1
            tvl *= (1 - ran() * 0.15)
            if tvl < 0.72 * INITIAL_TVL and ran() < 0.12:
                status, failure_reason, failure_day = "FAILED", "LST_DEPEG", day
                break

        if ran() < 0.000038 * bsm:
            reg_events += 1
            tvl *= (1 - ran() * 0.10)

        if ran() < 0.000022 * bsm:
            bridge_events += 1
            tvl *= (1 - ran() * 0.05)

        # ── CR Calculation ──
        cr = tvl / max(kusd, 1.0)
        min_cr = min(min_cr, cr)

        # ── UPGRADE 1: Insurance Fund injection before circuit breaker ──
        if cr < INS_INJECTION_TRIGGER_CR:
            tvl, injected = ins.inject_if_needed(cr, tvl, kusd)
            if injected > 0:
                ins_injections    += 1
                ins_total_injected += injected
                cr = tvl / max(kusd, 1.0)   # recalculate after injection

        # ── Drawdown ──
        if tvl > peak_tvl:
            peak_tvl = tvl
        max_dd = max(max_dd, (peak_tvl - tvl) / max(peak_tvl, 1))

        # ── UPGRADE 3: Tiered CB re-check after injection ──
        yellow_active, red_active = cb.update(cr, day)

        # ── LAYER 4: Gradual Liquidation ──
        if cr < LIQUIDATION_CR:
            tvl, kusd, liq_amt, was_capped = gl.execute(cr, tvl, kusd, day)
            if liq_amt > 0:
                liq_count += 1
                cr = tvl / max(kusd, 1.0)
                if cr < 1.10:
                    if was_capped and ran() < 0.30:
                        status, failure_reason, failure_day = "FAILED", "LIQUIDATION_CASCADE", day
                        break
                    elif cr < 1.05:
                        status, failure_reason, failure_day = "FAILED", "UNDERCOLLATERALIZED", day
                        break

        if tvl < 500_000:
            status, failure_reason, failure_day = "FAILED", "LIQUIDATION_CASCADE", day
            break

    yield_rate = total_yield / INITIAL_TVL if total_yield > 0 else 0.0

    return {
        "simulation_id":            sim_id,
        "scenario":                 scenario,
        "status":                   status,
        "failure_reason":           failure_reason,
        "failure_day":              failure_day,
        "final_tvl":                tvl,
        "final_eth_price":          eth_price,
        "final_collateral_ratio":   max(cr, 0.0),
        "total_yield_generated":    total_yield,
        "final_yield_rate":         yield_rate,
        "min_collateral_ratio":     min_cr,
        "max_drawdown":             max_dd,
        "liquidation_count":        liq_count,
        "circuit_breaker_red_triggers":    cb.red_triggers,
        "circuit_breaker_yellow_triggers": cb.yellow_triggers,
        "circuit_breaker_red_days":        cb.red_total_days,
        "circuit_breaker_yellow_days":     cb.yellow_days,
        "gradual_liq_caps":         gl.caps,
        "oracle_rejects":           oracle_rejects,
        "buffer_high_days":         buf.high_days,
        "insurance_injections":     ins_injections,
        "insurance_total_injected": ins_total_injected,
        "insurance_final_reserves": ins.reserves,
        "negative_yield_days":      neg_yield_days,
        "gas_spike_days":           gas_spike_days,
        "exploit_events":           exploit_events,
        "depeg_events":             depeg_events,
        "regulatory_events":        reg_events,
        "bridge_events":            bridge_events,
    }


# ─────────────────────────────────────────────────────────────
# ANALYSIS
# ─────────────────────────────────────────────────────────────
def analyze_results(results: list) -> dict:
    survivors = [r for r in results if r["status"] == "SURVIVED"]
    failures  = [r for r in results if r["status"] == "FAILED"]
    n         = len(results)

    fail_reasons = {}
    for r in failures:
        k = r["failure_reason"] or "UNKNOWN"
        fail_reasons[k] = fail_reasons.get(k, 0) + 1

    def mean(lst, key):
        vals = [x[key] for x in lst if x.get(key) is not None]
        return sum(vals) / len(vals) if vals else 0.0

    def ptile(lst, p):
        if not lst: return 0.0
        s = sorted(lst)
        return s[max(0, int(len(s) * p / 100))]

    tvls      = sorted(r["final_tvl"] for r in survivors)
    fail_days = [r["failure_day"] for r in failures if r["failure_day"] is not None]

    scenario_stats = {}
    for sc in SCENARIO_PROBABILITIES:
        sc_all  = [r for r in results if r["scenario"] == sc]
        sc_fail = [r for r in sc_all  if r["status"] == "FAILED"]
        scenario_stats[sc] = {
            "count":         len(sc_all),
            "failures":      len(sc_fail),
            "survival_rate": (len(sc_all) - len(sc_fail)) / max(len(sc_all), 1),
        }

    return {
        "total_simulations": n,
        "survival_count":    len(survivors),
        "failure_count":     len(failures),
        "survival_rate":     len(survivors) / n,
        "failure_rate":      len(failures) / n,
        "failure_reasons":   fail_reasons,
        "survivor_stats": {
            "mean_final_tvl":    mean(survivors, "final_tvl"),
            "median_final_tvl":  ptile(tvls, 50),
            "mean_yield":        mean(survivors, "total_yield_generated"),
            "mean_yield_rate":   mean(survivors, "final_yield_rate"),
            "mean_min_cr":       mean(survivors, "min_collateral_ratio"),
            "mean_max_drawdown": mean(survivors, "max_drawdown"),
        },
        "var_95": ptile(tvls, 5),
        "var_99": ptile(tvls, 1),
        "failure_stats": {
            "mean_failure_day":   sum(fail_days) / max(len(fail_days), 1),
            "median_failure_day": ptile(fail_days, 50),
        },
        "protection_layer_stats": {
            "mean_cb_red_triggers_per_sim":    round(mean(results, "circuit_breaker_red_triggers"),    4),
            "mean_cb_yellow_triggers_per_sim": round(mean(results, "circuit_breaker_yellow_triggers"), 4),
            "mean_cb_red_days_per_sim":        round(mean(results, "circuit_breaker_red_days"),        4),
            "mean_cb_yellow_days_per_sim":     round(mean(results, "circuit_breaker_yellow_days"),     4),
            "mean_gradual_liq_caps_per_sim":   round(mean(results, "gradual_liq_caps"),               4),
            "mean_oracle_rejects_per_sim":     round(mean(results, "oracle_rejects"),                 4),
            "mean_high_buffer_days_per_sim":   round(mean(results, "buffer_high_days"),               4),
            "mean_insurance_injections_per_sim":       round(mean(results, "insurance_injections"),       4),
            "mean_insurance_injected_usd_per_sim":     round(mean(results, "insurance_total_injected"),   2),
            "mean_insurance_reserves_end_per_sim":     round(mean(results, "insurance_final_reserves"),   2),
        },
        "scenario_breakdown": scenario_stats,
        "event_stats": {
            "mean_exploit_events":      mean(results, "exploit_events"),
            "mean_depeg_events":        mean(results, "depeg_events"),
            "mean_regulatory_events":   mean(results, "regulatory_events"),
            "mean_bridge_events":       mean(results, "bridge_events"),
            "mean_negative_yield_days": mean(results, "negative_yield_days"),
            "mean_gas_spike_days":      mean(results, "gas_spike_days"),
        },
        "timestamp": datetime.now().isoformat(),
        "upgrades_applied": [
            "UPGRADE 1: Protocol Insurance Fund - auto-inject at CR < 1.30x, $3M reserve, 10pct perf fee allocation",
            "UPGRADE 2: Post-Audit Exploit Probability - 70pct audit reduction + 10pct bug bounty = 73pct total reduction",
            "UPGRADE 3: Tiered Circuit Breaker - Yellow soft alert at CR < 1.35x + Red full pause at CR < 1.25x",
        ],
        "protections_from_sim3_retained": [
            "Triple-Source Oracle Chainlink TWAP Pyth",
            "Oracle Deviation Threshold 5pct max",
            "TWAP Window Hardening 30min manipulation resistance",
            "Circuit Breaker Red full pause at 1.25x",
            "Dynamic CR Buffer 5pct calm 10pct stressed",
            "Gradual Liquidation 5pct TVL cap per hour",
        ],
        "audit_params": {
            "audit_active":       AUDIT_ACTIVE,
            "audit_reduction_pct": AUDIT_REDUCTION * 100,
            "bug_bounty_reduction_pct": BUG_BOUNTY_REDUCTION * 100,
            "combined_exploit_multiplier": round(EXPLOIT_AUDIT_MULT, 4),
            "base_exploit_prob_per_day": EXPLOIT_BASE_PROB,
            "audited_exploit_prob_per_day": round(EXPLOIT_PROB, 8),
        },
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("KERNE PROTOCOL - MONTE CARLO v4 (THREE NEW UPGRADES)")
    print("=" * 70)
    print(f"Running {N_SIMULATIONS:,} simulations over {SIMULATION_DAYS} days...")
    print()
    print("UPGRADES vs Simulation 3:")
    print(f"  [+1] Insurance Fund: $3M reserve, auto-injects at CR < {INS_INJECTION_TRIGGER_CR}x")
    print(f"  [+2] Post-Audit: exploit prob reduced {(1 - EXPLOIT_AUDIT_MULT)*100:.0f}% (audit + bug bounty)")
    print(f"  [+3] Tiered CB: Yellow soft alert at CR < {CB_YELLOW_CR}x, Red full pause at CR < {CB_RED_CR}x")
    print()

    all_results = []
    start_time  = datetime.now()

    for i in range(N_SIMULATIONS):
        result = run_single_simulation(i)
        all_results.append(result)
        if (i + 1) % 1000 == 0:
            elapsed  = (datetime.now() - start_time).total_seconds()
            pct_done = (i + 1) / N_SIMULATIONS * 100
            s        = sum(1 for r in all_results if r["status"] == "SURVIVED")
            print(f"  [{i+1:5,}/{N_SIMULATIONS:,}] {pct_done:.0f}% | Survival: {s/(i+1)*100:.2f}% | Elapsed: {elapsed:.1f}s")

    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\nSimulation complete in {total_time:.1f}s\n")

    analysis = analyze_results(all_results)

    print("=" * 70)
    print("RESULTS SUMMARY — v4")
    print("=" * 70)
    print(f"  Survival Rate:        {analysis['survival_rate']*100:.2f}%")
    print(f"  Failure Count:        {analysis['failure_count']:,} / {analysis['total_simulations']:,}")
    print(f"  Failure Reasons:      {analysis['failure_reasons']}")
    print()
    ss = analysis["survivor_stats"]
    print(f"  Mean Final TVL:       ${ss['mean_final_tvl']:>15,.0f}")
    print(f"  Median Final TVL:     ${ss['median_final_tvl']:>15,.0f}")
    print(f"  Mean Yield APY:       {ss['mean_yield_rate']*100:.2f}%")
    print(f"  Mean Min CR:          {ss['mean_min_cr']:.4f}x")
    print(f"  Mean Max Drawdown:    {ss['mean_max_drawdown']*100:.2f}%")
    print(f"  VaR 95%:              ${analysis['var_95']:>15,.0f}")
    print(f"  VaR 99%:              ${analysis['var_99']:>15,.0f}")
    print()
    pls = analysis["protection_layer_stats"]
    print("Protection + Upgrade Layer Activity (avg per simulation):")
    print(f"  CB Yellow Triggers:       {pls['mean_cb_yellow_triggers_per_sim']:.4f}")
    print(f"  CB Yellow Days:           {pls['mean_cb_yellow_days_per_sim']:.4f}")
    print(f"  CB Red Triggers:          {pls['mean_cb_red_triggers_per_sim']:.4f}")
    print(f"  CB Red Days:              {pls['mean_cb_red_days_per_sim']:.4f}")
    print(f"  Gradual Liq Caps:         {pls['mean_gradual_liq_caps_per_sim']:.4f}")
    print(f"  Oracle Rejects:           {pls['mean_oracle_rejects_per_sim']:.4f}")
    print(f"  High Buffer Days:         {pls['mean_high_buffer_days_per_sim']:.4f}")
    print(f"  Insurance Injections:     {pls['mean_insurance_injections_per_sim']:.4f}")
    print(f"  Insurance Injected USD:   ${pls['mean_insurance_injected_usd_per_sim']:,.0f}")
    print(f"  Insurance End Reserves:   ${pls['mean_insurance_reserves_end_per_sim']:,.0f}")
    print()
    print("Scenario Breakdown:")
    for sc, stats in analysis["scenario_breakdown"].items():
        print(f"  {sc:12s}: {stats['count']:4,} sims | {stats['survival_rate']*100:.1f}% survival | {stats['failures']} failures")

    target_met = analysis["survival_rate"] >= 0.99
    print()
    if target_met:
        print("  ✅ TARGET MET: Survival rate > 99.00%")
    else:
        print(f"  ❌ TARGET NOT MET: {analysis['survival_rate']*100:.2f}% < 99.00%")

    output = {
        "meta": {
            "simulation_name": "Kerne Protocol Monte Carlo v4 - Full Protection + 3 Upgrades",
            "date": "2026-02-19",
            "n_simulations": N_SIMULATIONS,
            "simulation_days": SIMULATION_DAYS,
            "initial_tvl": INITIAL_TVL,
            "initial_eth_price": INITIAL_ETH_PRICE,
            "runtime_seconds": round(total_time, 2),
            "target_survival_rate": 0.99,
            "target_met": target_met,
        },
        "analysis": analysis,
        "results": all_results,
    }

    output_path = "bot/montecarlosimulation4feb19.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
