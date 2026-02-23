# Kerne Paper Trade Simulation: "Happy Path"

**Date:** 2025-12-28
**Initial Deposit:** $10,000 USDC

## 1. Operational Flow Simulation

| Step | Action | Asset | Amount | Fee (Est.) | Time Taken (Est.) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | Swap USDC to wstETH | USDC -> wstETH | $10,000 | $5.00 (0.05%) | 1 min |
| 2 | Bridge to CEX | wstETH | $9,995 | $5.00 (Gas) | 15-30 mins |
| 3 | Open 1x Short | ETH-PERP | $9,990 | $5.00 (0.05%) | 1 min |
| **Total** | **Net Equity** | **kUSD Backing** | **$9,985** | **$15.00** | **~32 mins** |

## 2. Break-Even Analysis

-   **Initial Loss (Entry Fees):** $15.00 (0.15% of principal)
-   **Target Annualized Yield (APY):** 20% (Staking + Funding)
-   **Daily Yield:** $10,000 * (0.20 / 365) = **$5.48 / day**
-   **Break-Even Time:** $15.00 / $5.48 ≈ **2.74 Days**

## 3. Conclusion
The entry cost for the delta-neutral strategy is approximately 15 basis points (bps). At a conservative 20% APY, the protocol recovers its operational costs in less than 3 days, after which it generates pure profit for the vault.
