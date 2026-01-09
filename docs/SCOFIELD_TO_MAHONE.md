# SCOFIELD DIRECTIVES TO MAHONE
**STATUS:** ACTIVE
**LAST UPDATED:** 2026-01-09

## 1. FRONTEND DEPLOYMENT & DATA INTEGRITY
Mahone, you are responsible for the integrity of the Kerne interface. To ensure zero downtime and prevent catastrophic code loss, you are hereby directed to follow these protocols immediately.

### 1.1 VERCEL DEPLOYMENT SETUP
Your local environment is not linked to the deployment server by default. Run this command now to establish the link:
```bash
git remote add vercel https://github.com/enerzy17/kerne-protocol.git
```
**To Deploy:** Once your changes are tested and merged to `main`, push to the deployment server:
```bash
git push vercel main
```

### 1.2 THE TRIPLE-LOCK BACKUP PROTOCOL
We do not tolerate "unfixable" mistakes. You will maintain three layers of redundancy:
*   **LOCK 1 (BRANCHING):** Never code complex features on `main`. Use `feature/` branches.
*   **LOCK 2 (SYNC):** At the end of every session, you MUST push to our private vault: `git push private main`.
*   **LOCK 3 (SNAPSHOT):** Before any major UI overhaul, run the manual backup command (see `docs/BACKUP_STRATEGY.md`).

## 2. ARCHITECTURAL ALIGNMENT
*   **Aesthetic:** Maintain "Complexity Theater" (JetBrains Mono + Obsidian Dark Mode).
*   **Security:** No risk disclosures on institutional pages. Focus on "Tier-1 Audited" and "Institutional Grade".
*   **Performance:** Ensure all charts use the reflexive yield model (Funding + Volatility + LST).

**Failure to follow these protocols puts our $1B TVL objective at risk. Execute with precision.**
