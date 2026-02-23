# Draft: Kerne Protocol - Strategic Launch Phase

## Requirements (confirmed)
- Goal: $1B+ TVL in 12 months.
- Strategy: Liquidity Black Hole (Restaking, Leverage Loops, Points, Prisoner's Dilemma Airdrop).
- Multi-chain: Base (Live), Arbitrum (Live), Optimism (Ready).
- Revenue: ZIN (Intents), Flash-Arb, Treasury Buybacks.

## Technical Decisions
- **ZIN**: Zero-fee flash loans for solvers to capture spreads.
- **Hedging**: Delta-neutral using Hyperliquid/Binance.
- **Airdrop**: Tiered mechanism (Mercenary/Vesting/Loyalist).
- **Recursive Leverage**: 1-click folding using Flash Loans.

## Research Findings
- **ZIN Status**: Deployed but under-capitalized (~$79). Base RPC returning empty code on some calls.
- **Treasury**: Currently misconfigured (pointing to deployer instead of token/staking).
- **Optimism**: Deployment scripts ready, blocked by gas in deployer wallet.
- **Airdrop**: `KerneAirdrop.sol` exists but implementation of "Prisoner's Dilemma" needs verification.

## Open Questions
- **Priority**: Technical stabilization vs. Flywheel ignition vs. Marketing launch.
- **KERNE Price**: Initial seeding price/FDV (Runbook suggests $0.05 / $5M FDV).
- **Capital**: Amount for ZIN pool seeding ($10k+ recommended).
- **Grant**: Optimism Foundation grant application status.

## Scope Boundaries
- **INCLUDE**: Base, Arbitrum, Optimism. ZIN Solver, Leverage Infrastructure, Airdrop, Treasury Buybacks.
- **EXCLUDE**: Public code exposure (PRIVATE REPO ONLY).
