# Kerne Risk Policy: The Safety Module

**Date:** 2025-12-28
**Status:** Draft / Technical Specification

## 1. Collateral Health & Liquidation Logic
To ensure the solvency of the synthetic dollar, the system monitors the Collateral Ratio (CR) in real-time.

-   **Target Collateral Ratio (CR):** **130%**. This is the baseline for a healthy system.
-   **Soft Liquidation Threshold:** **115%**.
    -   **Action:** If CR falls below 115%, the Strategist Bot must execute a **"Partial Unwind"**. This involves closing a portion of the short position on the CEX and unlocking the corresponding collateral to restore the CR back to the 130% target.
-   **Hard Liquidation Threshold:** **105%**.
    -   **Action:** Emergency solvency check. If CR falls below 105%, the system must **halt new mints** immediately. The protocol enters emergency mode to protect existing holders.

## 2. Depeg Protection (The "Oracle Guard")
The system must protect against decoupling between the Liquid Staking Token (LST) and its underlying asset (ETH).

-   **Metric:** Exchange rate between Collateral (e.g., wstETH) and Liability (ETH).
-   **Threshold:** Deviation of **>2.0%** from the 24-hour Moving Average (MA).
-   **Action:** Trigger `PAUSE` on the `KerneVault`. This prevents "toxic flow" where arbitrageurs might dump depegged assets into the vault at the expense of existing liquidity providers.

## 3. Funding Rate Risk (The "Bleed" Check)
Since a significant portion of the yield comes from the funding rate, the system must avoid positions that lose money.

-   **Metric:** 3-Day Simple Moving Average (SMA) of the ETH-PERP Funding Rate.
-   **Threshold:** 3-Day SMA **< 0%** (Negative Funding).
-   **Action:** Signal **"Strategy Idle"**. The bot should close short positions and hold Spot ETH/LST until the funding rate returns to positive territory. This prevents the "bleed" of capital during bearish or neutral funding environments.

## 4. Custody & Counterparty Risk
Diversification and liquidity are key to mitigating centralized exchange risks.

-   **TVL Limit per CEX:** Maximum TVL per CEX account is capped at **$5,000,000**. As the protocol scales, additional accounts or exchanges must be integrated.
-   **Liquidity Buffer:** A **10% Withdrawal Buffer** of total TVL must remain liquid in the smart contract (as wstETH/cbETH) on the Base network. This ensures that users can perform instant withdrawals without waiting for the bridging process from CEXs.
