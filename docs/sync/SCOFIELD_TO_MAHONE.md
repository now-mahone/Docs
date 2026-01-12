# SCOFIELD TO MAHONE: DIRECTIVES & UPDATES (2026-01-10)

## 1. PROTOCOL HARDENING (CRITICAL)
We have completed a major hardening sprint. The protocol is now "Production Active."
- **Sentinel Autonomous Defense:** The bot can now autonomously pause vaults if health scores fall below 50.0. Strategist has been granted `PAUSER_ROLE`.
- **Tiered PSM Fees:** `KUSDPSM.sol` now supports tiered fees for institutional volume. Larger swaps = lower fees.
- **Verified Yield Oracle:** `KerneYieldOracle.sol` is now linked to `KerneVerificationNode.sol`. Yield updates require a recent cryptographic attestation of solvency.
- **OFT Fix:** Downgraded `KerneOFT.sol` to LayerZero V1 to match our library. Compilation is now green.

## 2. REPOSITORY RESTRUCTURING
>>>>+++ REPLACE

To bypass Vercel's "Pro Plan" requirement for organizations, we have restructured the remotes:
- **PRIMARY REPO:** `https://github.com/enerzy17/kerne-vercel` (Personal repo, bypasses paywall)
- **ORG BACKUP:** `https://github.com/kerne-protocol/kerne-main` (Renamed from `kerne-private`)

**ACTION REQUIRED:** Update your local remotes:
```bash
git remote set-url vercel https://github.com/enerzy17/kerne-vercel.git
git remote set-url private https://github.com/kerne-protocol/kerne-main.git
```

## 2. TECHNICAL UPDATES
- **KerneVault.sol Fix:** Resolved a syntax error (extra closing brace) that was breaking `forge fmt` and CI/CD.
- **Formatting:** Ran `forge fmt` across the entire codebase. All contracts are now standardized.
- **Merge Conflicts:** Resolved conflicts in `project_state.md` and synchronized the state.

## 3. VERCEL DEPLOYMENT
The project is now ready to be imported into Vercel from the `kerne-vercel` repository. This allows us to use the free tier while keeping the code private.

## 4. NEXT STEPS
1. **Mahone:** Pull from `vercel main` to sync your local environment.
2. **Mahone:** Verify the Lead Scanner V3 results and prepare the next batch of institutional targets.
3. **Both:** All future pushes should go to `vercel main` to trigger auto-deployments.

---
*Stay focused. $1B TVL is the only metric that matters.*
