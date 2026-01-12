# Kerne Mechanism Specification: Delta-Neutral Synthetic Dollar

**Date:** 2025-12-28
**Network:** Base (L2)

## 1. Overview
Kerne is a yield-bearing synthetic dollar protocol designed to maximize TVL by combining Ethereum staking yields with funding rate arbitrage from centralized exchanges (CEXs). The system creates a delta-neutral position to maintain a stable value relative to the US Dollar while capturing multiple yield streams.

## 2. Core Components
- **Collateral:** Liquid Staking Tokens (LSTs) - specifically `wstETH` (Lido) or `cbETH` (Coinbase).
- **Hedge:** 1x Short ETH-PERP positions on Tier-1 Centralized Exchanges (Binance, Bybit).
- **Synthetic Asset:** Kerne USD (kUSD) - a stablecoin backed by the delta-neutral position.

## 3. Operational Flow
1. **Deposit:** User deposits `USDC` into the Kerne Vault on Base.
2. **Swap:** The protocol swaps `USDC` for `wstETH` or `cbETH` via decentralized exchanges (e.g., Uniswap V3, Aerodrome).
3. **Custody/Bridge:** The LST collateral is moved to a designated institutional custody account or directly to a sub-account on a CEX (Binance/Bybit).
4. **Hedging:** The system opens a 1x Short ETH-PERP position against the deposited collateral.
5. **Yield Generation:**
   - **Staking Yield:** Earned from the LST (wstETH/cbETH).
   - **Funding Rate:** Earned from being short ETH-PERP when funding is positive (shorts get paid by longs).

## 4. Risk Management & Constraints
- **Collateral Ratio (CR):** The system must maintain a minimum CR of **130%**.
  - $CR = \frac{Value\ of\ Collateral}{Value\ of\ Debt}$
- **Delta Neutrality:** The hedge must be rebalanced periodically to ensure the net delta remains near zero.
- **Liquidation Risk:** While delta-neutral, extreme price gaps or decoupling between LSTs and ETH could affect the CR.
- **CEX Risk:** Counterparty risk associated with the centralized exchange and API security.
- **Sentinel Autonomous Defense:** The protocol employs an automated risk engine (Sentinel) that monitors health scores and can autonomously trigger on-chain circuit breakers (pausing) if health factors drop below critical thresholds (e.g., 1.1x).
- **Institutional Compliance:** Bespoke vaults can be gated via the `KerneComplianceHook`, allowing for automated KYC/AML verification before deposits are accepted.
- **Emergency Unwind:** In extreme scenarios, the protocol can execute a full unwind, pausing on-chain contracts and closing all CEX positions simultaneously to protect principal capital.

## 5. Peg Stability Module (PSM)
The KUSDPSM allows for 1:1 swaps between kUSD and other major stablecoins (USDC, cbBTC) to maintain the peg.
- **Tiered Fees:** Institutional users benefit from a tiered fee structure, where larger swap volumes incur lower basis point fees, incentivizing deep liquidity and peg stability.

## 6. Mathematical Goal
The total yield ($Y_{total}$) is defined as:
$Y_{total} = Y_{staking} + Y_{funding} - C_{operational}$
Where:
- $Y_{staking}$ is the annualized yield of the LST.
- $Y_{funding}$ is the annualized funding rate received.
- $C_{operational}$ includes swap fees, bridging costs, and protocol fees.

## 6. Recursive Leverage Engine (The Folding Mechanism)
Kerne employs a programmatic folding mechanism to synthetically amplify TVL and yield.

### 6.1 Mechanism
1. **Flash-Mint:** The protocol flash-mints kUSD against the user's initial collateral.
2. **Swap:** The flash-minted kUSD is swapped for more of the underlying LST.
3. **Re-collateralize:** The new LST is deposited back into the KerneVault, increasing the user's collateral balance.
4. **Debt Assignment:** The flash-minted amount is assigned as debt to the user's position.

### 6.2 The Multiplier Effect
By folding liquidity up to the liquidation threshold, the protocol achieves a **Gross Notional Multiplier** ($M$):
$M = \frac{1}{1 - L}$
Where $L$ is the Loan-to-Value ratio. At a 130% CR ($L \approx 0.76$), the multiplier is approximately **4.3x**.

### 6.3 Valuation Capture
Protocol fees are generated on the **Gross Notional Value** ($V_{gross} = V_{net} \times M$). This decouples protocol revenue from net capital inflows, creating a "Liquidity Black Hole" that justifies aggressive governance token valuations.
