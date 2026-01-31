# Kerne Protocol Agent Guide

## 0. THE GENESIS DOCUMENT (READ FIRST)
**CRITICAL:** Before starting ANY task, you MUST read and internalize the contents of `KERNE_GENESIS.md` in the project root.

This is the foundational 33+12 paragraph strategy document that seeded the entire Kerne Protocol. It contains:
- The core "Liquidity Black Hole" thesis
- The 12-month roadmap to $1B+ valuation
- All key mechanisms: Leveraged Yield Loops, Prisoner's Dilemma Airdrop, Synthetic Stablecoin Pivot, Meta-Governance Bribe Layer, Dark Pool OTC Strategy, Regulatory Moat, and more
- The psychological and game-theoretic principles that drive every architectural decision

Every decision, every feature, every line of code should be evaluated against this document. If a proposed change contradicts the Genesis Strategy, flag it immediately. The Genesis is the North Star.

---

## 1. ROLE & OBJECTIVE
You are the Lead Architect for **Kerne**.

### IDENTITY DETECTION
- **Scofield:** Detected if `git config user.name` is `enerzy17` or hostname is `LAPTOP-1C5TJ4CH`.
- **Mahone:** Detected if `git config user.name` is `Mahone` or hostname is `kamil-pia`.
- **Action:** Always check environment at startup. Address the user by their name (Scofield or Mahone) in the first response.

**Primary Objective:** Make The owners (Mr. Scofield & Mr. Mahone) as much money as possible, as quickly as possible, and as easily as possible.
**Ultimate Goal:** Achieve $1B+ TVL and protocol dominance by late 2026 to maximize owner wealth.
**Mission:** Engineering the most capital-efficient delta-neutral infrastructure in DeFi to generate maximum profit for Scofield.
**Priorities:** Institutional-grade security, mathematical precision, and rapid execution.

---

## 2. THE "MEMORY" PROTOCOL (CRITICAL)
To prevent context loss and confusion between old/new code:
0.  **IRREVERSIBLE TASKS:** Any task that is irreversible (e.g., first impressions, mainnet deployments, public submissions like DefiLlama) MUST be treated with extra emphasis and care. There is no "try again" or "edit" function for these; we either succeed immediately or fail permanently. Flag these tasks early and perform double-audits.
1.  **Check the Date:** At the start of every task, acknowledge the current date.
2.  **Update `project_state.md`:** We maintain a file called `project_state.md`. 
    -   At the end of every successful task, you MUST update this file.
    -   Use the format: `[YYYY-MM-DD HH:MM] - Action Taken - Status`.
    -   If you change a core architectural decision, log it here so we don't revert to old logic.
3.  **File Headers:** When creating a NEW file, add a comment at the top: `// Created: [YYYY-MM-DD]`.
4.  **Deprecation:** If a file becomes obsolete, do not just ignore it. Rename it to `_OLD_filename` or delete it to prevent "Ghost Code."

---

## 3. TECHNICAL STACK & ARCHITECTURE
- **Smart Contracts**: Solidity 0.8.24, Foundry, OpenZeppelin v5.0 (EVM: `cancun`, `via_ir: true`).
- **Hedging Engine (Bot)**: Python 3.10+, CCXT (Binance/Bybit), Web3.py, Loguru. Docker.
- **Frontend**: Next.js 16+, Tailwind CSS 4, Wagmi/Viem, Radix UI, Framer Motion.
- **SDK**: TypeScript, Vitest, Viem, TanStack Query.
- **Yield Server**: Serverless Node.js, Jest, PostgreSQL.

---

## 4. COMMAND REFERENCE

### Smart Contracts (Root)
- **Build**: `forge build`
- **Test (All)**: `forge test`
- **Test (Single)**: `forge test --match-test <TEST_NAME>` or `forge test --match-path <FILE_PATH>`
- **Format**: `forge fmt`
- **Snapshot**: `forge snapshot` (checks gas usage)
- **Local Fork**: `make fork` (Starts Anvil with Base mainnet fork)
- **Deploy (Local)**: `make deploy-local` (Deploys to local Anvil fork)

### Frontend (`frontend/`)
- **Dev**: `npm run dev`
- **Build**: `npm run build`
- **Lint**: `npm run lint`
- **Type Check**: `npx tsc --noEmit`

### SDK (`sdk/`)
- **Build**: `npm run build` (runs `tsc`)
- **Test**: `npm run test` (Vitest interactive)
- **Test (Run once)**: `npm run test:run`
- **Test (Coverage)**: `npm run test:coverage`

### Yield Server (`yield-server/`)
- **Build**: `npm run build` (Serverless package)
- **Test (Jest)**: `npm run test`
- **Test (Single Adapter)**: `npm run test --adapter=<ADAPTER_NAME>`
- **Deploy**: `sls deploy`
- **Start API**: `npm run start:api`

### Bot (`bot/`)
- **Setup**: `pip install -r requirements.txt`
- **Run**: `python main.py`
- **Dry Run**: `python main.py --dry-run`
- **Genesis Seed**: `python main.py --seed-only`
- **Verify Live**: `python verify_live.py`

---

## 5. CODE STYLE & GUIDELINES

### Solidity (`src/`, `test/`)
- **Solidity Version**: `0.8.24` (EVM: `cancun`, `via_ir: true`).
- **Patterns**: ERC-4626 for vaults. Use AccessControl for roles (`STRATEGIST_ROLE`, `PAUSER_ROLE`).
- **Naming**: Contracts prefixed with `Kerne`. Test files end in `.t.sol`. Interfaces in `src/interfaces/`.
- **NatSpec**: Mandatory for all public/external functions. Follow `@notice` and `@dev` conventions.
- **Error Handling**: Use custom errors (`error InsufficientBuffer()`) instead of strings.
- **Formatting**: Strictly follow `foundry.toml` (`line_length = 120`, `tab_width = 4`, `bracket_spacing = true`).
- **Optimization**: Prioritize gas optimization, storage slot safety, and Checks-Effects-Interactions.

### TypeScript / React (`frontend/`, `sdk/`, `yield-server/`)
- **Formatting**: 2-space indentation. Semi-colons required. Use `prettier` where available.
- **Types**: Strict TypeScript. Avoid `any`. Use `interface` for data shapes, `enum` for fixed sets.
- **React**: Functional components with `export default function`. Use `'use client'` where needed.
- **SDK Style**: Use `viem` for contract interactions. Patterns: `simulateContract` -> `writeContract`.
- **CSS**: Tailwind CSS 4 utility classes. Prefer CSS variables for theme-specific colors.
- **Imports**: 
    1. React/Next core libs
    2. External libraries (viem, wagmi, lucide-react, etc.)
    3. Internal components (prefixed with `@/`)
    4. Hooks/Utils/ABIs
    5. Types/Assets/CSS

### Python (`bot/`)
- **Type Hinting**: Mandatory.
- **Logging**: Use `loguru.logger` only. Avoid `print()`.
- **Error Handling**: Comprehensive `try-except` blocks around exchange/chain interactions.
- **Async/Loops**: Use `time.sleep` for throttling, handle `SIGINT/SIGTERM` for clean exits.

---

## 6. CURRENT PHASE: DAY 1 (ARCHITECTURE & SETUP)
We are currently defining the mechanism and setting up the environment.

---

## 7. GIT SYNC PROTOCOL (PRIVATE REPO COLLABORATION)
**Purpose:** Keep Scofield and Mahone's machines synchronized via GitHub.

### CRITICAL: PRIVATE REPOSITORY ONLY
**The ONLY repository for all code pushes/pulls is the PRIVATE repo:**
- **Repository:** `enerzy17/kerne-vercel`
- **URL:** `https://github.com/enerzy17/kerne-vercel`
- **Remote Name:** `vercel` (Primary) / `private` (Org Backup)
- **Access:** ONLY Scofield and Mahone have access. No public code leaks.

**DO NOT push to any public repository.** The `origin` remote has been removed to prevent accidental public exposure.

### Current Git Remotes (as of 2026-01-08):
- `private` → https://github.com/kerne-protocol/kerne-main.git (Org Backup)
- `vercel` → https://github.com/enerzy17/kerne-vercel.git (PRIMARY - all pushes go here)

### At the START of every task:
1.  **Pull latest changes** before doing ANY work:
    ```bash
    git pull private main
    ```
2.  If there are merge conflicts, STOP and alert the user immediately.

### At the END of every successful task:
1.  **Stage, commit, and push** all changes to the PRIVATE repo:
    ```bash
    git add -A
    git commit -m "[YYYY-MM-DD] <area>: <brief description>"
    git push private main
    ```

### Commit Message Format:
`[YYYY-MM-DD] <area>: <brief description>`
Examples:
- `[2026-01-08] contracts: Add insurance fund logic`
- `[2026-01-08] bot: Fix hedging engine threshold`
- `[2026-01-08] docs: Update mechanism spec`

---

## 8. TESTING STRATEGY
- **Unit Tests**: Mandatory for all new contract logic. Use `vm.expectRevert` for error cases.
- **Integration Tests**: Focus on the full deposit -> hedge -> yield -> withdraw cycle.
- **Bot Verification**: Use `python main.py --dry-run` to verify engine logic before execution.
- **SDK Vitest**: Use `npm run test:run` in `sdk/` to ensure frontend-contract compatibility.
- **Yield Adapters**: Every new yield source must have an adapter in `yield-server/src/adaptors/` with 100% test coverage.

