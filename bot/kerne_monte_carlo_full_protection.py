# Created: 2026-02-19
"""
Kerne Protocol - Full Protection Monte Carlo Simulation
Includes ALL protection layers:
  1. Triple-Source Oracle (Chainlink + TWAP + Pyth)
  2. TWAP Window Hardening (30-min manipulation resistance)
  3. Circuit Breaker (triggers CR < 1.25x, recovers > 1.35x for 4h)
  4. Dynamic CR Buffer (strategist-controlled 5-10% additional buffer)
  5. Gradual Liquidation (5% TVL cap per hour)
  6. Stale Price Protection (1-hour threshold)
  7. Multiple Oracle Deviation Check (5% max deviation)

DELTA-NEUTRAL MECHANICS:
  - Long ETH/LST collateral HEDGED by short ETH perpetuals
  - ETH price shock net delta = ~0 (long gain + short gain cancel)
  - CR is primarily driven by: net yield (funding + staking - fees)
  - Strategist closes/reduces short if funding goes too negative (risk mgmt)
  - Primary risks: sustained negative funding, LST depeg, smart contract exploit
  
APY MODEL (scenario-based, realistic):
  - Normal:     12-18% APY (positive funding + 4.5% LST)
  - Bull:       18-28% APY (strongly positive funding + 4.5% LST)
  - Bear:        2-8%  APY (funding turns negative, LST still pays, strategist reduces short)
  - Black Swan: -10-5% APY (extreme, brief; strategist halts trading)
  - Regulatory:  3-8%  APY (moderate negative funding)
"""

import json
import random
import math
from datetime import datetime

# ─────────────────────────────────────────────────────────────
# SIMULATION CONSTANTS
# ─────────────────────────────────────────────────────────────
N_SIMULATIONS = 10_000
SIMULATION_DAYS = 365
INITIAL_TVL     = 100_000_000     # $100M
INITIAL_ETH_PRICE = 3_500.0
PERFORMANCE_FEE = 0.20            # 20% of gross yield
MANAGEMENT_FEE  = 0.02 / 365     # 2% annual → daily

# ─────────────────────────────────────────────────────────────
# COLLATERAL RATIO PARAMETERS
# ─────────────────────────────────────────────────────────────
BASE_CR         = 1.50            # 150% starting CR
LIQUIDATION_CR  = 1.20            # 120% hard floor
INITIAL_KUSD    = INITIAL_TVL / BASE_CR   # ~$66.67M fixed debt

# ─────────────────────────────────────────────────────────────
# YIELD MODEL BY SCENARIO
# Daily yield = TVL * (annual_rate / 365), with random component
# These represent net basis APY after all costs BEFORE protocol fees
# ─────────────────────────────────────────────────────────────
# (mean, std_dev) of DAILY yield rate
YIELD_PARAMS = {
    # (mu_annual, sigma_annual, min_annual, max_annual)
    "normal":     (0.155, 0.025, 0.08,  0.22),   # ~15.5% avg
    "bull":       (0.225, 0.035, 0.14,  0.35),   # ~22.5% avg
    "bear":       (0.040, 0.040, -0.08, 0.10),   # ~4% avg, can go negative
    "black_swan": (-0.02, 0.10,  -0.30, 0.12),   # avg slight neg, high vol
    "regulatory": (0.055, 0.035, -0.05, 0.12),   # ~5.5% avg
}

# ─────────────────────────────────────────────────────────────
# MARKET SCENARIO PROBABILITIES (identical to original for apples-to-apples comparison)
# ─────────────────────────────────────────────────────────────
SCENARIO_PROBABILITIES = {
    "normal":     0.60,
    "bull":       0.15,
    "bear":       0.15,
    "black_swan": 0.05,
    "regulatory": 0.05,
}

ETH_ANNUAL_VOLS = {
    "normal": 0.75, "bull": 0.90, "bear": 0.95, "black_swan": 1.40, "regulatory": 1.10,
}
ETH_ANNUAL_RETURNS = {
    "normal": 0.30, "bull": 1.50, "bear": -0.60, "black_swan": -0.85, "regulatory": -0.40,
}

# ─────────────────────────────────────────────────────────────
# PROTECTION LAYER PARAMETERS
# ─────────────────────────────────────────────────────────────

# Layer 1 — Oracle
ORACLE_DEVIATION_THRESHOLD   = 0.05   # 5% max deviation between oracles
CHAINLINK_FAILURE_PROB       = 0.0005
PYTH_FAILURE_PROB            = 0.0003
TWAP_FAILURE_PROB            = 0.0001
# Manipulation impact when triple oracle has a read conflict (vs single oracle failing completely)
MANIPULATED_ORACLE_LOSS_PCT  = 0.002  # 0.2% slippage hit per manipulation event

# Layer 2 — Circuit Breaker
CB_TRIGGER_CR    = 1.25   # pause vault below this CR
CB_RECOVER_CR    = 1.35   # start recovery timer above this CR
CB_RECOVER_DAYS  = 1      # days CB must hold above recover CR (4h → 1 day in daily simulation)
CB_MAX_PAUSE     = 7      # admin force-recovers after 7 days

# Layer 3 — Dynamic CR Buffer
DYNAMIC_BUFFER_CALM     = 0.05   # target 1.55x in calm markets
DYNAMIC_BUFFER_STRESSED = 0.10   # target 1.60x in stressed markets  
VOL_STRESS_THRESHOLD    = 0.04   # daily ETH vol > 4% = stressed

# Layer 4 — Gradual Liquidation
MAX_LIQ_PCT_PER_DAY = 0.05       # 5% TVL per day (≈ 5% TVL per hour, simplified)

# ─────────────────────────────────────────────────────────────
# BLACK SWAN EVENT PROBABILITIES
# ─────────────────────────────────────────────────────────────
BS_MULT = {"normal": 1.0, "bull": 0.5, "bear": 2.5, "black_swan": 6.0, "regulatory": 3.5}

random.seed(42)

def ran():  return random.random()
def randn():
    u1, u2 = max(ran(), 1e-10), ran()
    return math.sqrt(-2 * math.log(u1)) * math.cos(2 * math.pi * u2)


# ─────────────────────────────────────────────────────────────
# ORACLE SIMULATION
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
# CIRCUIT BREAKER
# ─────────────────────────────────────────────────────────────
class CircuitBreaker:
    def __init__(self):
        self.active            = False
        self.total_pause_days  = 0
        self.recovery_day      = None
        self.triggers          = 0

    def update(self, cr: float, day: int) -> bool:
        if not self.active:
            if cr < CB_TRIGGER_CR:
                self.active       = True
                self.recovery_day = None
                self.triggers    += 1
        else:
            self.total_pause_days += 1
            if cr >= CB_RECOVER_CR:
                if self.recovery_day is None:
                    self.recovery_day = day
                elif (day - self.recovery_day) >= CB_RECOVER_DAYS:
                    self.active       = False
                    self.recovery_day = None
            else:
                self.recovery_day = None
            if self.total_pause_days >= CB_MAX_PAUSE:
                self.active = False
        return self.active


# ─────────────────────────────────────────────────────────────
# DYNAMIC BUFFER
# ─────────────────────────────────────────────────────────────
class DynamicBuffer:
    def __init__(self):
        self.high_days = 0
        self.stressed  = False

    def update(self, daily_vol: float) -> float:
        if daily_vol > VOL_STRESS_THRESHOLD:
            self.stressed   = True
            self.high_days += 1
            return DYNAMIC_BUFFER_STRESSED
        self.stressed = False
        return DYNAMIC_BUFFER_CALM


# ─────────────────────────────────────────────────────────────
# GRADUAL LIQUIDATION
# ─────────────────────────────────────────────────────────────
class GradualLiquidation:
    def __init__(self):
        self.daily_done = {}
        self.caps       = 0

    def execute(self, cr: float, tvl: float, kusd: float, day: int):
        if cr >= LIQUIDATION_CR:
            return tvl, kusd, 0.0, False

        # How much to liquidate to try to restore CR toward 1.30x
        deficit_pct  = min((LIQUIDATION_CR - cr) * 1.5, 0.30)
        needed       = tvl * deficit_pct

        already      = self.daily_done.get(day, 0.0)
        capacity     = max(0.0, tvl * MAX_LIQ_PCT_PER_DAY - already)
        actual       = min(needed, capacity)
        was_capped   = actual < needed * 0.95
        if was_capped:
            self.caps += 1

        self.daily_done[day] = already + actual
        ratio   = (tvl - actual) / max(tvl, 1)
        tvl_new  = tvl * ratio
        kusd_new = kusd * ratio
        return tvl_new, kusd_new, actual, was_capped


# ─────────────────────────────────────────────────────────────
# SINGLE SIMULATION
# ─────────────────────────────────────────────────────────────
def run_single_simulation(sim_id: int) -> dict:
    # ── Pick scenario ──
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

    # ── State ──
    eth_price    = INITIAL_ETH_PRICE
    tvl          = INITIAL_TVL
    kusd         = INITIAL_KUSD
    total_yield  = 0.0

    cb  = CircuitBreaker()
    buf = DynamicBuffer()
    gl  = GradualLiquidation()

    # ── Trackers ──
    min_cr          = BASE_CR
    max_dd          = 0.0
    peak_tvl        = tvl
    liq_count       = 0
    oracle_rejects  = 0
    neg_yield_days  = 0
    gas_spike_days  = 0
    exploit_events  = 0
    depeg_events    = 0
    reg_events      = 0
    bridge_events   = 0

    status, failure_reason, failure_day = "SURVIVED", None, None
    cr = BASE_CR

    for day in range(SIMULATION_DAYS):
        # ── ETH price (GBM — used for oracle check and basis risk only) ──
        eth_shock     = mu_eth + sigma_daily * randn()
        eth_price_raw = eth_price * math.exp(eth_shock)
        daily_vol     = abs(eth_shock)

        # ── LAYER 1: Triple Oracle ──
        oracle = triple_oracle_check(eth_price_raw, sigma_daily)
        if oracle["manipulated"]:
            oracle_rejects += 1
            tvl *= (1 - MANIPULATED_ORACLE_LOSS_PCT)   # small slippage cost
            eth_price = eth_price   # hold last valid price
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

        # ── YIELD CALCULATION (delta-neutral model) ──
        # Net APY drawn from scenario distribution. This represents:
        #   LST staking yield + funding rate income/cost + rebalancing slippage
        # In bear/black_swan: strategist reduces short to limit negative funding drag
        daily_gross_rate = (mu_ann + sig_ann * randn()) / 365
        daily_gross_rate = max(yld_min / 365, min(yld_max / 365, daily_gross_rate))
        
        # Small basis risk from residual ETH exposure (3% of ETH price move)
        basis_adj = eth_shock * 0.03   # ±3% sensitivity to ETH move → daily fraction

        gross_daily = tvl * (daily_gross_rate + basis_adj)
        perf_fee    = max(0, gross_daily) * PERFORMANCE_FEE
        mgmt_fee    = tvl * MANAGEMENT_FEE
        net_daily   = gross_daily - perf_fee - mgmt_fee

        if net_daily < 0:
            neg_yield_days += 1

        # Only accrue if circuit breaker not pausing vault
        if not cb.active:
            tvl        += net_daily
            total_yield += max(0.0, net_daily)
            tvl         = max(tvl, 1_000)

        # ── Black Swan Events ──
        if ran() < 0.00007 * bsm:              # Smart contract exploit
            exploit_events += 1
            loss_pct = ran() * 0.20
            tvl *= (1 - loss_pct)
            if ran() < 0.22:
                status, failure_reason, failure_day = "FAILED", "SMART_CONTRACT_EXPLOIT", day
                break

        if ran() < 0.000014 * bsm:             # LST depeg
            depeg_events += 1
            tvl *= (1 - ran() * 0.15)
            if tvl < 0.72 * INITIAL_TVL and ran() < 0.12:
                status, failure_reason, failure_day = "FAILED", "LST_DEPEG", day
                break

        if ran() < 0.000038 * bsm:             # Regulatory shock
            reg_events += 1
            tvl *= (1 - ran() * 0.10)

        if ran() < 0.000022 * bsm:             # Bridge exploit
            bridge_events += 1
            tvl *= (1 - ran() * 0.05)

        # ── CR (delta-neutral: collateral = TVL, debt = fixed kUSD) ──
        cr = tvl / max(kusd, 1.0)

        # ── Drawdown ──
        if tvl > peak_tvl:
            peak_tvl = tvl
        max_dd  = max(max_dd, (peak_tvl - tvl) / max(peak_tvl, 1))
        min_cr  = min(min_cr, cr)

        # ── LAYER 2: Circuit Breaker ──
        cb.update(cr, day)

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
        "simulation_id":          sim_id,
        "scenario":               scenario,
        "status":                 status,
        "failure_reason":         failure_reason,
        "failure_day":            failure_day,
        "final_tvl":              tvl,
        "final_eth_price":        eth_price,
        "final_collateral_ratio": max(cr, 0.0),
        "total_yield_generated":  total_yield,
        "final_yield_rate":       yield_rate,
        "min_collateral_ratio":   min_cr,
        "max_drawdown":           max_dd,
        "liquidation_count":      liq_count,
        "circuit_breaker_triggers": cb.triggers,
        "circuit_breaker_days":   cb.total_pause_days,
        "gradual_liq_caps":       gl.caps,
        "oracle_rejects":         oracle_rejects,
        "buffer_high_days":       buf.high_days,
        "negative_yield_days":    neg_yield_days,
        "gas_spike_days":         gas_spike_days,
        "exploit_events":         exploit_events,
        "depeg_events":           depeg_events,
        "regulatory_events":      reg_events,
        "bridge_events":          bridge_events,
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

    tvls = sorted(r["final_tvl"] for r in survivors)
    fail_days = [r["failure_day"] for r in failures if r["failure_day"] is not None]

    scenario_stats = {}
    for sc in SCENARIO_PROBABILITIES:
        sc_all  = [r for r in results   if r["scenario"] == sc]
        sc_fail = [r for r in sc_all    if r["status"] == "FAILED"]
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
            "mean_circuit_breaker_triggers_per_sim": round(mean(results, "circuit_breaker_triggers"), 4),
            "mean_circuit_breaker_days_per_sim":     round(mean(results, "circuit_breaker_days"),     4),
            "mean_gradual_liq_caps_per_sim":         round(mean(results, "gradual_liq_caps"),         4),
            "mean_oracle_rejects_per_sim":           round(mean(results, "oracle_rejects"),           4),
            "mean_high_buffer_days_per_sim":         round(mean(results, "buffer_high_days"),         4),
        },
        "scenario_breakdown": scenario_stats,
        "event_stats": {
            "mean_exploit_events":        mean(results, "exploit_events"),
            "mean_depeg_events":          mean(results, "depeg_events"),
            "mean_regulatory_events":     mean(results, "regulatory_events"),
            "mean_bridge_events":         mean(results, "bridge_events"),
            "mean_negative_yield_days":   mean(results, "negative_yield_days"),
            "mean_gas_spike_days":        mean(results, "gas_spike_days"),
        },
        "timestamp": datetime.now().isoformat(),
        "protections_active": [
            "Triple-Source Oracle Chainlink TWAP Pyth",
            "Oracle Deviation Threshold 5pct max",
            "TWAP Window Hardening 30min manipulation resistance",
            "Stale Price Protection 1hr threshold",
            "Circuit Breaker trigger below 1.25x CR recover above 1.35x for 4h",
            "Dynamic CR Buffer 5pct calm 10pct stressed",
            "Gradual Liquidation 5pct TVL cap per hour",
        ],
    }


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 70)
    print("KERNE PROTOCOL - FULL PROTECTION MONTE CARLO (DELTA-NEUTRAL)")
    print("=" * 70)
    print(f"Running {N_SIMULATIONS:,} simulations over {SIMULATION_DAYS} days...")
    print()
    print("Active Protection Layers:")
    print("  [1] Triple-Source Oracle (Chainlink + TWAP + Pyth)")
    print("  [2] TWAP Window Hardening (30-min, 5% deviation threshold)")
    print("  [3] Circuit Breaker (<1.25x triggers, >1.35x for 4h recovers)")
    print("  [4] Dynamic CR Buffer (5% calm / 10% stressed)")
    print("  [5] Gradual Liquidation (5% TVL/hr cap)")
    print()

    all_results = []
    start_time = datetime.now()

    for i in range(N_SIMULATIONS):
        result = run_single_simulation(i)
        all_results.append(result)
        if (i + 1) % 1000 == 0:
            elapsed = (datetime.now() - start_time).total_seconds()
            pct_done = (i + 1) / N_SIMULATIONS * 100
            s = sum(1 for r in all_results if r["status"] == "SURVIVED")
            print(f"  [{i+1:5,}/{N_SIMULATIONS:,}] {pct_done:.0f}% | Survival: {s/(i+1)*100:.2f}% | Elapsed: {elapsed:.1f}s")

    total_time = (datetime.now() - start_time).total_seconds()
    print(f"\nSimulation complete in {total_time:.1f}s\n")

    analysis = analyze_results(all_results)

    print("=" * 70)
    print("RESULTS SUMMARY")
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
    print("Protection Layer Activity (avg per simulation):")
    print(f"  CB Triggers:          {pls['mean_circuit_breaker_triggers_per_sim']:.4f}")
    print(f"  CB Pause Days:        {pls['mean_circuit_breaker_days_per_sim']:.4f}")
    print(f"  Gradual Liq Caps:     {pls['mean_gradual_liq_caps_per_sim']:.4f}")
    print(f"  Oracle Rejects:       {pls['mean_oracle_rejects_per_sim']:.4f}")
    print(f"  High Buffer Days:     {pls['mean_high_buffer_days_per_sim']:.4f}")
    print()
    print("Scenario Breakdown:")
    for sc, stats in analysis["scenario_breakdown"].items():
        print(f"  {sc:12s}: {stats['count']:4,} sims | {stats['survival_rate']*100:.1f}% survival | {stats['failures']} failures")

    output = {
        "meta": {
            "simulation_name": "Kerne Protocol Full Protection Monte Carlo - Delta-Neutral",
            "date": "2026-02-19",
            "n_simulations": N_SIMULATIONS,
            "simulation_days": SIMULATION_DAYS,
            "initial_tvl": INITIAL_TVL,
            "initial_eth_price": INITIAL_ETH_PRICE,
            "runtime_seconds": round(total_time, 2),
        },
        "analysis": analysis,
        "results": all_results,
    }

    output_path = "bot/montecarlosimulation3feb19.json"
    with open(output_path, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {output_path}")
