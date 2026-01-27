# Zero-Fee Intent Network (ZIN)

The **Zero-Fee Intent Network (ZIN)** transforms Kerne from a passive yield vault into a primary execution engine for high-volume trading on networks like Base and Arbitrum.

## The Concept

ZIN allows authorized "Solvers" to access Kerne's internal liquidity (ETH, USDC, LSTs) via **Zero-Fee Flash Loans** to fulfill user intents (swaps, limit orders) on platforms like CowSwap and UniswapX.

## Why ZIN?

1. **Spread Capture**: Instead of letting external liquidity providers (like Aave or Uniswap LPs) capture the spread on intents, Kerne uses its own liquidity to fulfill the trade and captures the spread for the protocol.
2. **Capital Efficiency**: Idle liquidity in the vaults, which would otherwise be sitting dormant while hedged, is put to work in the intent market.
3. **Organic Awareness**: Every trade filled by the network is tagged as "Filled by Kerne," creating a massive social footprint and organic user acquisition.

## Architecture

- **KerneZINPool**: A multi-source liquidity aggregator that provides flash loans.
- **KerneIntentExecutor**: The on-chain contract that receives the flash loan, executes the swap on a DEX (e.g., Aerodrome), fulfills the intent, and returns the profit to the vault.
- **ZIN Solver**: An off-chain bot that monitors intent venues (CowSwap, UniswapX), calculates profitability, and triggers the on-chain execution.

## Safety & Governance

Access to zero-fee flash loans is restricted to the `SOLVER_ROLE`. All executions are subject to the **Sentinel V2** guardrails, which enforce maximum position sizes, minimum profit thresholds, and gas ceilings.

---
*Created: 2026-01-26*
