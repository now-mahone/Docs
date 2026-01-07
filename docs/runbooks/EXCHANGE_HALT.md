# RUNBOOK: EXCHANGE HALT / CEX INSOLVENCY

**Severity:** CRITICAL
**Trigger:** CEX withdrawals suspended, API downtime > 4 hours, or rumors of insolvency.

## Overview
Kerne uses CEXs for capital-efficient hedging. If a CEX fails, the short position is lost, leaving the protocol with long ETH exposure (via wstETH).

## Immediate Actions
1.  **Pause Vault:** Prevent any further user interaction.
2.  **Emergency Withdrawal:** Attempt to withdraw all available USDT/ETH from the affected exchange immediately.

## Migration to On-Chain Hedging (GMX / Synthetix)
If the CEX is unusable, the hedge must be migrated to a decentralized perpetual exchange to maintain delta-neutrality.

### Step 1: Capital Procurement
-   If USDT was successfully withdrawn from CEX: Bridge to Base/Arbitrum.
-   If USDT is stuck: Use the `Withdrawal Buffer` in the `KerneVault` to provide initial margin for a new hedge.

### Step 2: Open Decentralized Hedge
-   **Venue:** GMX (Arbitrum/Base) or Synthetix (Optimism/Base).
-   **Action:** Open a short ETH position equal to the total wstETH held by the vault.
-   **Note:** Be mindful of slippage and borrow rates on DEXs, which are typically higher than CEXs.

### Step 3: Re-calibrate Bot
-   Update `bot/exchange_manager.py` to use the `ccxt.gmx` or a custom Web3 wrapper for the chosen DEX.
-   Restart the `Main Loop`.

## Long-term Resolution
-   Diversify hedging across at least 3 different venues (e.g., Binance, Bybit, and GMX) to prevent single point of failure.
-   Publish a transparency report regarding the stuck capital and the recovery plan.
