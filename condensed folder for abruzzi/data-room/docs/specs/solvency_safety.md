# Kerne Solvency & Safety Guarantees

**Date:** 2026-01-12
**Version:** 1.0
**Status:** Draft

## 1. Core Solvency Invariant
The fundamental guarantee of Kerne is that the protocol remains solvent if and only if:
`Total Assets (On-chain + Verified Off-chain) >= Total Liabilities (kUSD Supply + Vault Shares Value)`

### 1.1 Asset Definitions
- **On-chain Assets:** LSTs (wstETH, cbETH) held in `KerneVault` and stablecoins in `KUSDPSM`.
- **Off-chain Assets:** Net equity in CEX hedging accounts, cryptographically attested via `KerneVerificationNode`.
- **Liabilities:** Total supply of kUSD (debt) and the underlying value of all issued vault shares.

## 2. Safety Guarantees & Invariants

### 2.1 Oracle Integrity
- **Invariant:** `KerneYieldOracle` updates must be bounded by a maximum deviation per update (e.g., 500 bps) and a minimum update interval (e.g., 24h).
- **Protection:** Outlier rejection and staleness checks on all price/yield feeds.

### 2.2 Redemption Liquidity
- **Invariant:** A minimum of `X%` (e.g., 10%) of total assets must remain on-chain in liquid form (LSTs/Stablecoins) to facilitate immediate redemptions.
- **Protection:** `KerneVault` withdrawal buffers and tiered withdrawal limits.

### 2.3 Delta Neutrality
- **Invariant:** The net delta of the protocol (On-chain LSTs vs. Off-chain Shorts) must remain within `[-0.05, +0.05]` range.
- **Protection:** Sentinel bot automated rebalancing and "Panic Mode" deleveraging.

### 2.4 Role & Permission Limits
- **Invariant:** No single role (Admin, Strategist, Verifier) can unilaterally drain the vault.
- **Protection:** 
    - `Strategist` can only report yield and rebalance, not withdraw to arbitrary addresses.
    - `Verifier` can only attest to existing CEX equity.
    - `Admin` (Multisig) is required for structural changes and fee adjustments.

## 3. Failure Modes & Response Matrix

| Failure Mode | Detection | Protocol Response |
|--------------|-----------|-------------------|
| **LST Depeg (>5%)** | Sentinel Oracle Monitor | Pause Deposits/Withdrawals, Trigger Emergency Unwind |
| **CEX API Failure** | Sentinel Heartbeat | Switch to Fallback CEX, Alert Admin |
| **Oracle Manipulation** | `KerneYieldOracle` Bounds | Reject Update, Pause Oracle, Alert Admin |
| **kUSD Depeg (<$0.98)** | PSM Monitor | Increase PSM Fees, Sentinel Buyback |
| **Verification Staleness** | `KerneVerificationNode` | Exclude Off-chain Assets from `totalAssets()` |

## 4. Verification & Auditability
- **On-chain:** All invariants are enforced via `require` statements in core contracts and verified via the `KerneSecuritySuite` test battery.
- **Off-chain:** Proof of Solvency attestations are publicly verifiable on BaseScan via `KerneVerificationNode` events.
- **External:** DefiLlama adapter provides real-time visibility into the `totalAssets()` invariant.
