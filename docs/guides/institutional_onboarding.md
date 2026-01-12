# Kerne Institutional Onboarding Protocol

**Classification:** Internal / Confidential
**Target:** $1M+ Allocation Partners
**Objective:** Secure high-value, low-churn capital to anchor Phase 3 TVL.

---

## 1. The Institutional Value Proposition
Kerne is not a retail yield farm. It is a **Delta-Neutral Financial Primitive**.
- **Capital Preservation:** 1x Short hedge ensures principal is immune to ETH price volatility.
- **Yield Stacking:** Combines LST staking yield (~3-4%) with CEX funding rates (~8-15%).
- **Non-Custodial:** Assets remain in audited smart contracts on Base; only the hedge is managed off-chain.
- **Transparency:** Real-time Proof of Solvency via the Institutional Dashboard.

## 2. Onboarding Workflow

### Step 1: Lead Capture & Scoring
- Leads are captured via `/institutional`.
- Scoring Criteria:
    - **Tier A:** $25M+ (Direct Founder contact required).
    - **Tier B:** $5M - $25M (Institutional Desk follow-up).
    - **Tier C:** $1M - $5M (Automated KYC link).

### Step 2: KYC/AML Verification
- Partners must complete verification via our compliance provider.
- Required Documents:
    - Certificate of Incorporation.
    - Authorized Signatory ID.
    - Source of Wealth Declaration.

### Step 3: Vault Whitelisting
- Once verified, the Admin (Multisig) calls `setWhitelisted(partner_address, true)` on the `KerneVault`.
- For Tier A partners, a dedicated `KerneVault` instance may be deployed with bespoke fee structures.

### Step 4: Capital Deployment
- Partner deposits USDC/WETH into the whitelisted vault.
- The Hedging Engine automatically scales the short position to maintain delta-neutrality.

## 3. Institutional Fee Structure
| Allocation | Performance Fee | Management Fee |
|------------|-----------------|----------------|
| $1M - $5M  | 15%             | 1%             |
| $5M - $25M | 10%             | 0.5%           |
| $25M+      | Bespoke         | 0%             |

## 4. Reporting & API Access
Institutional partners receive a dedicated API key for:
- Real-time position monitoring.
- Historical yield attribution.
- Direct CSV export for tax/audit compliance.

---
**Kerne Core Architecture Team**
*Institutional Grade. Mathematical Precision.*
