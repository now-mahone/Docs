# Work Plan: Kerne LST-Solver & "Shadow-Yield" Hook

## Objective
Implement a public-facing Intent Solver that leverages Kerne's 0-fee flash liquidity and delta-neutral hedging engine to provide "Zero-Slippage" LST swaps for the Base ecosystem. This drives organic TVL growth and captures basis yield (revenue) without requiring user outreach or frontend interaction.

## Phase 1: Smart Contract Layer (The "Settler")
### 1.1 KerneLSTSolver.sol
- Create a new contract `KerneLSTSolver.sol` that inherits from `KerneIntentExecutor`.
- Implement `settleLSTIntent` function:
  - Takes a CowSwap/UniswapX intent.
  - Flash borrows required liquidity from `KerneVault` (0% fee).
  - Fulfills the user's swap at the Oracle Price (beating DEX market price).
  - Transfers the user's original token (e.g., cbETH) into the `KerneVault`.
- Integrate with `KerneArbExecutor` to allow the solver to "backrun" its own settlement for additional profit extraction.

### 1.2 KUSDPSM Integration
- Update `KUSDPSM.sol` to allow the Solver to use LSTs as temporary collateral to mint kUSD for settlement purposes.

## Phase 2: Bot Intelligence Layer (The "Searcher")
### 2.1 Intent Monitor (Python)
- Develop `bot/solver/lst_intent_listener.py`:
  - Polls CowSwap and UniswapX OrderBooks.
  - Filters for LST/ETH or LST/USDC pairs on Base.
- Implement `ProfitabilityEngine`:
  - Fetch Funding Rates from `bot/exchanges/hyperliquid.py`.
  - Fetch LST APRs from `bot/defillama/yield_adapter.js`.
  - Calculate: `NetProfit = (BasisYield + LST_Yield) - HedgeCost`.

### 2.2 Execution Logic
- Update `bot/solver/core.py` to trigger `KerneLSTSolver.execute()` when a profitable intent is found.
- Ensure the `MEVProtectedSubmitter` is used to prevent frontrunning of the settlement.

## Phase 3: Revenue & Awareness Capture
### 3.1 Basis Harvest
- Automated routine to claim CEX funding profits and swap them back to kUSD on-chain.
- Deposit profits into `KerneVault` to increase `projectedAPY`.

### 3.2 "Settled by Kerne" Branding
- Ensure the solver address is labelled "Kerne Solver" on BaseScan.
- Every successful trade will show "Price Improved" in the user's transaction history, leading them back to the Kerne ecosystem.

## Success Metrics
- **Revenue**: Total Basis Yield captured from settled positions.
- **TVL**: Total LST assets acquired via settlement.
- **Awareness**: Number of unique wallets whose trades were settled by Kerne.

## Technical Constraints
- Must maintain `minSolvencyThreshold` in `KUSDPSM` at all times.
- All hedging must be confirmed via `por_attestation.py` before settlement.

