# RUNBOOK: wstETH/ETH DEPEG EVENT

**Severity:** CRITICAL
**Trigger:** wstETH/ETH price ratio < 0.98 on Chainlink or Uniswap V3.

## Overview
Kerne relies on the stability of wstETH relative to ETH. A significant depeg threatens the delta-neutrality of the protocol, as the short position on the exchange (ETH) will no longer perfectly offset the collateral (wstETH).

## Immediate Actions (Automated)
1.  **Pause Vault:** The `Canary` or `Panic` script should automatically call `pause()` on the `KerneVault` contract to prevent new deposits and withdrawals.
2.  **Alert Team:** Discord/Telegram alerts sent with `@everyone` tag.

## Manual Intervention Steps
1.  **Assess the Depth:** Check the depeg depth across multiple venues (Curve, Lido, Binance).
2.  **Unwind Strategy:**
    -   If the depeg is deemed permanent or high-risk:
        -   **Step A:** Close the short position on the CEX immediately to lock in the ETH value.
        -   **Step B:** Swap wstETH for ETH on-chain using the most liquid path (likely CowSwap or 1inch to minimize slippage).
        -   **Step C:** Update `offChainAssets` to 0 in the contract.
3.  **Settlement:**
    -   Once all assets are in ETH, calculate the final NAV.
    -   Enable a "Settlement Mode" where users can withdraw their pro-rata share of the remaining ETH.

## Recovery
-   Only resume operations if wstETH returns to > 0.998 for a sustained period of 48 hours.
-   Perform a full audit of the loss and publish a post-mortem.
