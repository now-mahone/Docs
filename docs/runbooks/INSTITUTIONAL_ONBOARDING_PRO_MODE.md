# Runbook: Institutional Onboarding (Pro Mode)
// Created: 2026-01-31
// Status: OPERATIONAL

This document outlines the step-by-step protocol for onboarding a regulated institutional partner into a Kerne "Pro Mode" (KYC-gated) vault.

## 1. Pre-Onboarding Requirements
- Partner must provide a primary Ethereum wallet address for whitelisting.
- Partner must complete off-chain KYC/AML verification (handled via Kerne Foundation or integrated provider).
- Partner must agree to the "Institutional Yield Agreement" (Legal).

## 2. Technical Execution (Admin Actions)

### Step A: Deploy the Compliance Hook (If not already deployed)
If the `KerneComplianceHook` is not yet live on the target chain, execute:
```bash
forge script script/DeployCompliance.s.sol --rpc-url $RPC_URL --broadcast
```

### Step B: Whitelist the Partner
The `COMPLIANCE_MANAGER_ROLE` (held by Scofield/Admin) must authorize the partner's address.

**Option 1: Global Whitelisting (Recommended for Prime Partners)**
This allows the partner to access ANY vault that uses the compliance hook.
```bash
cast send $COMPLIANCE_HOOK_ADDR "setGlobalCompliance(address,bool)" $PARTNER_ADDR true --private-key $ADMIN_KEY
```

**Option 2: Vault-Specific Whitelisting**
This restricts the partner to a specific vault instance.
```bash
cast send $COMPLIANCE_HOOK_ADDR "setComplianceStatus(address,address,bool)" $VAULT_ADDR $PARTNER_ADDR true --private-key $ADMIN_KEY
```

### Step C: Link Identity (Optional)
To maintain a "Glass Box" audit trail, link the partner's wallet to their internal ID.
```bash
cast send $COMPLIANCE_HOOK_ADDR "linkIdentity(address,string)" $PARTNER_ADDR "PARTNER_ID_001" --private-key $ADMIN_KEY
```

## 3. Partner Interaction
1. **Deposit:** The partner can now call `deposit()` or `mint()` on the vault. The transaction will be rejected by the `KerneVault` if the compliance check fails.
2. **Verification:** The partner can verify their status by calling `isCompliant(vault, account)` on the hook contract.

## 4. Emergency Revocation
In the event of a compliance breach or regulatory request, revoke access immediately:
```bash
cast send $COMPLIANCE_HOOK_ADDR "setGlobalCompliance(address,bool)" $PARTNER_ADDR false --private-key $ADMIN_KEY
```

## 5. Troubleshooting
- **Revert: "Not whitelisted or compliant"**: Ensure `strictCompliance[vault]` is set to `true` on the hook and the user has been added to `globalCompliance` or `complianceStatus`.
- **AccessControl Error**: Ensure the caller has `COMPLIANCE_MANAGER_ROLE` on the hook contract.