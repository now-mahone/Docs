// Created: 2026-01-17

# ZIN Execution Plan (All 4 Paths)

## Overview
This runbook executes the four approved tracks:
1. **Base ZIN Micro-Live Run** (primary)
2. **Arbitrum ZIN Deployment + Dry-Run**
3. **ZIN Profit Telemetry & Reporting Hardening**
4. **Flash-Arb Micro-Run**

Each section includes guardrails, validation steps, and rollback safety.

---

## 1) Base ZIN Micro-Live Run (24h)
**Goal:** Real cashflow validation with minimal risk.

### Preconditions
- `bot/.env` has correct RPC, addresses, and `ZIN_SOLVER_LIVE=true`.
- Solver guardrails set (min profit, gas ceiling, max intent).
- Discord webhook configured for alerts.

### Guardrails (recommended)
- `ZIN_MIN_PROFIT_BPS=10`
- `ZIN_MAX_INTENT_USDC=500`
- `ZIN_MAX_INTENT_WETH=0.2`
- `ZIN_MAX_GAS_GWEI=25`
- `ZIN_MAX_INTENTS_PER_CYCLE=3`
- `ZIN_INTENT_TTL_SECONDS=45`
- `ZIN_AUTO_SCALE=true`

### Execution
1. Start solver in live mode.
2. Let run for 24 hours.
3. Capture logs and profit CSV snapshot.

### Success Criteria
- At least 1 successful fill.
- Positive net PnL after gas.
- No Sentinel rejections due to stale intents.

---

## 2) Arbitrum ZIN Deployment + Dry-Run
**Goal:** Validate higher intent flow without capital risk.

### Execution
1. Use `script/DeployZINArbitrum.s.sol` to deploy.
2. Configure Arbitrum addresses in `bot/.env`.
3. Run solver in `--dry-run` for 6–12 hours.

### Success Criteria
- Stable feed ingestion (UniswapX/CowSwap).
- Profitable intent candidates seen in logs.

---

## 3) ZIN Profit Telemetry & Reporting Hardening
**Goal:** Institutional-grade profit reporting for transparency and scaling.

### Tasks
- Add explicit daily rollup log/CSV snapshot.
- Emit on-chain profit events where applicable.
- Produce a daily summary for vault revenue attribution.

### Success Criteria
- Daily report auto-generated.
- Profit snapshots consistent with on-chain balances.

---

## 4) Flash-Arb Micro-Run (24h)
**Goal:** Validate graph-discovery arb bot profitability.

### Guardrails
- Conservative gas ceiling.
- Max notional per cycle.
- Kill-switch on 2 consecutive failed executions.

### Execution
1. Enable flash-arb scanner.
2. Run for 24 hours.
3. Record wins/losses and net PnL.

### Success Criteria
- Positive net PnL.
- No revert loops.

---

## Post-Run Review
- Summarize results (fills, PnL, gas).
- Decide scale-up parameter adjustments.
- Update `project_state.md` with outcomes.
