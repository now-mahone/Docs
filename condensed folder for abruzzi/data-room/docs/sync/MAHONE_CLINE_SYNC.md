# MAHONE CLINE CONTEXT SYNC (2026-01-09)

## 1. CRITICAL REPO UPDATE
We have moved the primary deployment repository to bypass Vercel Pro requirements.
- **New Primary (Vercel):** `https://github.com/enerzy17/kerne-vercel`
- **Org Backup (Main):** `https://github.com/kerne-protocol/kerne-main`

**CLINE INSTRUCTION:** Update your remotes immediately:
```bash
git remote set-url vercel https://github.com/enerzy17/kerne-vercel.git
git remote set-url private https://github.com/kerne-protocol/kerne-main.git
```

## 2. RECENT ARCHITECTURAL FIXES
- **KerneVault.sol:** Fixed a syntax error at line 416 (extra closing brace). The contract now compiles and passes `forge fmt`.
- **Formatting:** The entire codebase has been formatted using `forge fmt`. Do not revert these changes.
- **Project State:** `project_state.md` has been synchronized. Always read this file at the start of a task to avoid "Ghost Code" or logic regression.

## 3. CURRENT PROTOCOL STATUS
- **Phase:** Day 1 (Architecture & Setup) / Week 2 Initiation.
- **Focus:** Institutional Hardening and Multi-Chain Expansion (Arbitrum/Optimism).
- **Key Contracts:** `KerneVault`, `kUSDMinter`, `KerneOFT`, `KernePrime`.
- **Security:** Insurance Fund is active; Health Factor enforcement is set to 1.3e18 for institutional safety.

## 4. CLINE OPERATIONAL RULES
- **Identity:** You are Mahone's Lead Architect.
- **Sync:** Always `git pull private main` at start and `git push vercel main` at end.
- **Memory:** Update `project_state.md` after every successful task.
- **Style:** Solidity 0.8.24, gas-optimized, OZ 5.0.

## 5. MISSION OBJECTIVE
Establish Kerne as the premier institutional liquidity layer on Base. Target: $1B TVL.

---
*Mahone, feed this entire file to your Cline to ensure perfect alignment.*
