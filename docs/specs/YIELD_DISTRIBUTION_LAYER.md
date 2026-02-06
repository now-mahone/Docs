# Kerne: Yield Distribution Layer (YDL) Specification

// Created: 2026-02-04

## 1. Vision
Kerne is a non-custodial, audited, risk-scored, tokenized-vault protocol that transforms on-chain yields into simple, "embed-and-earn" savings products for wallets, exchanges, and apps.

### Core Thesis
1. **Distribution is the Moat**: Liquidity follows clicks. Kerne focuses on being the default "Earn" backend for B2B partners.
2. **Technical Modularity**: Packaging strategies + risk controls + reporting into a trustable standard (ERC-4626).
3. **Real Revenue**: Monetization via management/performance fees and white-label integration fees.
4. **Trust at Scale**: Institutional-grade transparency and risk management.

## 2. Architectural Components

### A. Vault Core (`KerneVault.sol`)
- **Standard**: ERC-4626 compliant.
- **Accounting**: Hybrid on-chain/off-chain tracking (`offChainAssets`, `l1Assets`, `hedgingReserve`).
- **Monetization**: Performance fees and white-label "Founder Fees".
- **Guardrails**: 
    - Circuit breakers (Deposit/Withdraw limits).
    - Solvency thresholds with automatic pausing.
    - Withdrawal queue with cooldowns.
    - Emergency exit with "Panic Fee".

### B. Strategy Adapters (`KerneUniversalAdapter.sol`)
- **Function**: Wraps external protocols (Aave, Moonwell, Aerodrome) into the Kerne standard.
- **Isolation**: Strategies can be swapped, paused, or rotated without affecting core vault accounting.
- **Harvesting**: Automated reward collection and reinvestment.

### C. Risk Engine
- **Position Limits**: Hard caps per vault (`maxTotalAssets`).
- **Oracle Sanity**: Integration with `KerneYieldOracle` for TWAY reporting.
- **Solvency Verification**: `trustAnchor` and `verificationNode` for real-time Proof of Reserves.
- **Compliance**: `IComplianceHook` for automated KYC/AML/Sanctions screening.

### D. Observability & Transparency
- **Real-time NAV**: Calculated via `totalAssets()` combining on-chain and verified off-chain data.
- **Strategy Attribution**: Tracked via individual adapters.
- **Audit Trails**: All strategist updates and sweeps are emitted as events.

## 3. B2B Distribution Strategy
- **White-Labeling**: Partners can deploy their own branded vaults using `KerneVaultFactory`.
- **Integration Ergonomics**: 
    - ERC-4626 shares + Permit support.
    - Clean events for off-chain indexing.
    - "One-click earn" logic via `KerneYieldRouter`.
- **Partner Admin Console**: (Off-chain) Dashboard for partners to monitor their users' exposure and performance.

## 4. Risk Policy & Constraints
- **Mandate-First**: Start with "Cash Vaults" (stablecoins, overcollateralized lending).
- **Concentration Limits**: Enforced by strategists and verified by the `trustAnchor`.
- **Liquidity Stress Tests**: Managed via the withdrawal queue and liquid buffer requirements.

## 5. Roadmap Integration
- **Phase 1**: Launch "USDC Cash Vault" on Base L2.
- **Phase 2**: Expand to LST/LRT strategies with recursive leverage.
- **Phase 3**: Launch `rUSD` (Restaked USD) synthetic stablecoin.
- **Phase 4**: Institutional "Pro Mode" with full compliance wrappers.