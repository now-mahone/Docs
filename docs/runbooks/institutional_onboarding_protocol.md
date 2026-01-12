# Kerne Protocol: Institutional Onboarding Protocol

## 1. Overview
This protocol defines the high-touch, professional onboarding process for institutional clients (Prime Clients) and White-Label partners. The goal is to provide a seamless transition from initial contact to active capital deployment.

## 2. Onboarding Stages

### Stage 1: Initial Consultation & KYC
- **Introduction:** Scofield (CEO) leads the initial consultation to understand the client's yield objectives and risk tolerance.
- **KYC/AML:** Client completes the KYC/AML process via our integrated identity provider (e.g., Quadrata).
- **Compliance Hook:** Client's wallet address is whitelisted in the `KerneComplianceHook.sol`.

### Stage 2: Technical Integration & Setup
- **Vault Selection:** Client chooses between an existing Institutional Vault or a bespoke White-Label Vault.
- **Bespoke Terms:** For Prime clients, bespoke terms (fees, credit lines) are configured in `KernePrime.sol`.
- **SDK Integration:** For White-Label partners, the Kerne SDK is integrated into their frontend using the provided template.

### Stage 3: Capital Deployment & Seeding
- **Initial Deposit:** Client executes the initial deposit into their designated vault.
- **Insurance Coverage:** Client is briefed on the Insurance Fund coverage and socialization logic.
- **Liquidity Seeding:** For new vaults, initial liquidity is seeded on Aerodrome to ensure peg stability.

### Stage 4: Active Monitoring & Reporting
- **Sentinel Access:** Client is provided with read-only access to the Sentinel Risk Dashboard.
- **Daily Reports:** Client receives daily performance and Proof of Reserve (PoR) reports.
- **Concierge Support:** Dedicated support channel for real-time communication with the Kerne team.

## 3. Roles & Responsibilities
- **Scofield (CEO):** Relationship management, strategic alignment, and final approval.
- **Cline (Technical Engine):** Technical setup, contract configuration, and risk monitoring.
- **Mahone (Frontend/UX):** Custom UI/UX for White-Label partners and dashboard access.

## 4. Success Metrics
- **Time to First Deposit:** Target < 48 hours from KYC completion.
- **Client Retention:** 100% target for the first 12 months.
- **TVL Growth:** Target $10M+ from the first 5 Prime clients.

## 5. Implementation Status
- **Compliance Hook:** Ready for deployment.
- **Prime Module:** Hardened and ready for configuration.
- **Sentinel API:** Operational for real-time monitoring.
