# Created: 2026-01-19
# Depeg Event Response Runbook

## Purpose
Provide a clear, repeatable protocol for responding to LST/ETH depeg events, preserving solvency, protecting LPs, and maintaining institutional trust.

---

## Definitions
- **Depeg:** LST spot price deviates from ETH by more than 2%.
- **Critical Depeg:** Deviation exceeds 5%.
- **Severe Depeg:** Deviation exceeds 10%.

---

## Signal Sources
- Chainlink Oracle (Primary)
- DEX TWAP (Aerodrome / Uniswap)
- CEX perp mark price (Hyperliquid)

---

## Severity Levels

### Level 1: Warning (2% - 5%)
**Objective:** Monitor and prepare.
- Increase monitoring frequency to 1-min intervals.
- Freeze new deposits if volatility spikes.
- Notify internal alert channel.

### Level 2: Critical (5% - 10%)
**Objective:** Reduce exposure and protect NAV.
- Pause new deposits and mints.
- Reduce leverage to minimum safe baseline (≤2x).
- Begin partial unwind of LST exposure.
- Activate Sentinel auto-pause readiness.

### Level 3: Severe (>10%)
**Objective:** Preserve solvency and prevent liquidation.
- Immediately pause vault operations.
- Fully unwind hedge and LST exposure.
- Activate emergency unwind script.
- Notify stakeholders with status update.

---

## Execution Checklist
1. Confirm depeg with 2 data sources.
2. Trigger appropriate severity response.
3. Log actions in `project_state.md`.
4. Update Treasury Ledger if funds move.
5. Publish incident summary in daily report.

---

## Post-Event Review
- Record timeline of events and actions.
- Assess NAV impact and recovery steps.
- Update risk parameters if needed.
- Produce short incident report for partners.
