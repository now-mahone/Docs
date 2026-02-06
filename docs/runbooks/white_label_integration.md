# Kerne Protocol: White-Label Integration Runbook
// Created: 2026-02-04

## Overview
This document outlines the process for B2B partners (wallets, exchanges, apps) to integrate Kerne's "Yield Distribution Layer" as a turnkey "Earn" solution. This strategy captures early revenue through integration fees and management fees before protocol TVL reaches critical mass.

## 1. The Value Proposition
- **Turnkey Earn:** Partners can offer high-yield "Savings" products without building their own DeFi infrastructure.
- **Institutional Safety:** Backed by the Kerne Sentinel Risk Engine (VaR, circuit breakers, multi-factor scoring).
- **Custom Branding:** Vaults can be named and branded to match the partner's UI.
- **Revenue Share:** Partners can set their own management fees on top of Kerne's base performance fee.

## 2. Technical Integration Steps

### Phase 1: Vault Deployment
1.  **Clone Factory:** Use `KerneVaultFactory.sol` to deploy a new `KerneVault` instance.
2.  **Configuration:**
    - `asset`: The underlying token (e.g., USDC, WETH).
    - `name`: Partner-branded name (e.g., "Binance Earn ETH").
    - `symbol`: Partner-branded symbol (e.g., "bEarnETH").
    - `performanceFee`: Blended fee (typically 30-80 bps).
3.  **Whitelisting:** Enable `whitelistEnabled` if the partner requires KYC/AML gating.

### Phase 2: Risk Engine Onboarding
1.  **Sentinel Registration:** Register the new vault address with the `RiskEngine`.
2.  **Threshold Calibration:** Set custom circuit breakers for the partner (e.g., tighter drawdown limits for conservative users).
3.  **Oracle Setup:** Connect the vault to `KerneYieldOracle` for real-time NAV reporting.

### Phase 3: Frontend Integration
1.  **SDK Integration:** Use the `Infinite Garden SDK` to embed vault interactions (deposit, request withdrawal, claim) into the partner's app.
2.  **Transparency Dashboard:** Embed the "Glass House" dashboard showing real-time Proof of Reserves and strategy attribution.

## 3. Monetization Model
- **Integration Fee:** $50k - $250k (one-time setup fee).
- **Management Fee:** 10-20 bps on TVL (annualized).
- **Performance Fee:** 10% of generated yield.
- **Founder Fee:** A portion of the partner's fee is routed to the Kerne Founder address.

## 4. Emergency Procedures
- **Partner Pause:** Partners are granted the `PAUSER_ROLE` to halt their specific vault in case of a frontend exploit.
- **Emergency Exit:** Users can utilize the `emergencyExit()` function in `KerneVault.sol` to bypass cooldowns if the protocol is paused for >3 days (charges a 5% Panic Fee).

---
**Status:** Operational
**Lead:** Scofield