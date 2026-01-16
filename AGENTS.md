# Kerne Protocol Agent Guide

## Project Overview
Kerne is a delta-neutral synthetic dollar protocol on the Base network. It leverages LST collateral and CEX-based hedging (Binance/Bybit) to generate stable yield for the KUSD stablecoin. The protocol focuses on institutional-grade security, capital efficiency, and 100% on-chain transparency.

### Core Premise
The protocol maximizes capital efficiency and institutional-grade security. All architectural decisions prioritize long-term stability and wealth capture for the protocol ecosystem.

---

## 1. Technical Stack & Architecture
- **Smart Contracts**: Solidity 0.8.24, Foundry, OpenZeppelin v5.0 (EVM: `cancun`, `via_ir: true`).
- **Hedging Engine (Bot)**: Python 3.10+, CCXT (Binance/Bybit), Web3.py, Loguru.
- **Frontend**: Next.js 16+, Tailwind CSS 4, Wagmi/Viem, Radix UI, Framer Motion.
- **SDK**: TypeScript, Vitest, Viem, TanStack Query.
- **Yield Server**: Serverless Node.js, Jest, PostgreSQL.

---

## 2. Command Reference

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

## 3. Code Style & Guidelines

### Solidity (`src/`, `test/`)
- **Solidity Version**: `0.8.24` (EVM: `cancun`, `via_ir: true`).
- **Patterns**: ERC-4626 for vaults. Use AccessControl for roles (`STRATEGIST_ROLE`, `PAUSER_ROLE`).
- **Naming**: Contracts prefixed with `Kerne`. Test files end in `.t.sol`. Interfaces in `src/interfaces/`.
- **NatSpec**: Mandatory for all public/external functions. Follow `@notice` and `@dev` conventions.
- **Error Handling**: Use custom errors (`error InsufficientBuffer()`) instead of strings.
- **Formatting**: Strictly follow `foundry.toml` (`line_length = 120`, `tab_width = 4`, `bracket_spacing = true`).

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
- **Logging**: Use `loguru.logger` only. Avoid `print()`.
- **Error Handling**: Comprehensive `try-except` blocks around exchange/chain interactions.
- **Async/Loops**: Use `time.sleep` for throttling, handle `SIGINT/SIGTERM` for clean exits.

---

## 4. Key Environment Variables
Ensure these are configured in `.env` files:
- `BASE_RPC_URL`: Primary network for protocol.
- `BASESCAN_API_KEY`: For contract verification.
- `PRIVATE_KEY`: Deployment and bot execution.
- `BINANCE_API_KEY` / `BINANCE_SECRET`: For CEX hedging engine.
- `BYBIT_API_KEY` / `BYBIT_SECRET`: For CEX hedging engine.
- `DISCORD_WEBHOOK_URL`: For bot alerts and monitoring.

---

## 5. Directory Structure
```text
.
├── bot/                # Python-based hedging engine & monitoring
├── frontend/           # Next.js 16 web application
├── src/                # Solidity smart contracts
│   ├── interfaces/     # Contract interfaces (e.g., IKerneVault.sol)
│   └── mocks/          # Test mocks
├── test/               # Foundry tests (unit, integration, security)
├── sdk/                # TypeScript client library (Viem-based)
├── yield-server/       # APY/TWAY reporting backend (Serverless/Node)
├── integrations/       # External protocol integrations (e.g., DefiLlama)
├── script/             # Foundry deployment & management scripts
└── docs/               # Protocol specifications & technical reports
```

---

## 6. Testing Strategy
- **Unit Tests**: Mandatory for all new contract logic. Use `vm.expectRevert` for error cases.
- **Integration Tests**: Focus on the full deposit -> hedge -> yield -> withdraw cycle.
- **Bot Verification**: Use `python main.py --dry-run` to verify engine logic before execution.
- **SDK Vitest**: Use `npm run test:run` in `sdk/` to ensure frontend-contract compatibility.
- **Yield Adapters**: Every new yield source must have an adapter in `yield-server/src/adaptors/` with 100% test coverage.

---

## 7. Git Workflow
- **Branching**: Use `feature/`, `fix/`, or `refactor/` prefixes.
- **Commits**: Follow Conventional Commits (e.g., `feat: add circuit breaker to KerneVault`).
- **PRs**: All PRs must include a summary of changes and reference relevant issues. Use `gh pr create` for automation.
