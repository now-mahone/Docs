# Zero-Fee Intent Network (ZIN)

The **Zero-Fee Intent Network (ZIN)** transforms Kerne from a passive yield vault into a primary execution engine for high-volume trading on Base and Arbitrum.

## The Concept

ZIN empowers authorized "Solvers" to utilize Kerne's internal liquidity (ETH, USDC, LSTs) via **Zero-Fee Flash Loans** to fulfill user intents (swaps, limit orders) across the DeFi ecosystem.

## Why ZIN?

1. **Spread Capture**: Instead of allowing external liquidity providers to extract value, Kerne utilizes its own liquidity to fulfill trades, capturing the spread for the protocol.
2. **Capital Velocity**: Idle liquidity in the vaults is utilized in the intent market, maximizing capital efficiency while maintaining a hedged position.
3. **Market Presence**: Every trade filled by the network is tagged as "Filled by Kerne," establishing a significant social footprint and driving organic protocol awareness.

## Architecture

- **KerneZINPool**: A multisource liquidity aggregator that provides flash loans.
- **KerneIntentExecutor**: The onchain contract that receives the flash loan, executes the swap on a DEX (e.g., Aerodrome), fulfills the intent, and returns the profit to the vault.
- **ZIN Solver**: An offchain bot that monitors intent venues (CowSwap, UniswapX), calculates profitability, and triggers the onchain execution.

## Safety & Governance

Access to zero fee flash loans is restricted to the `SOLVER_ROLE`. All executions are subject to the **Sentinel V2** guardrails, which enforce maximum position sizes, minimum profit thresholds, and gas ceilings.