# Work Plan: Kerne "Base Stability & Yield" (BSY) Agent

## Goal
To build an autonomous, revenue-generating agent that performs liquidations and delta-neutral arbitrage on the Base network, driving organic protocol awareness through visible on-chain "Action."

## Phase 1: Morpho Blue "Backstop" (Liquidation Engine)
- **Task 1.1**: Develop `src/KerneMorphoLiquidator.sol`.
  - Integration with `KerneVault` for flash loans.
  - Logic to repay debt in KUSD/USDC and receive LST collateral (wstETH/cbETH).
- **Task 1.2**: Extend Python Bot (`bot/liquidator.py`).
  - Implement Morpho GraphQL API listener to monitor unhealthy positions in Steakhouse/Re7 pools.
  - Automate `liquidate()` calls with optimized gas bidding.

## Phase 2: Aerodrome CLMM "Delta-Neutral" Strategy
- **Task 2.1**: Implement `bot/strategies/aerodrome_slipstream.py`.
  - Fetch real-time tick-data from Aerodrome Slipstream.
  - Calculate LP Delta and transmit rebalance signals to `bot/exchanges/binance.py`.
- **Task 2.2**: Update `src/KerneUniversalAdapter.sol`.
  - Add support for concentrated liquidity provision and automated reward (AERO) harvesting/compounding.

## Phase 3: "Proof-of-Action" & Revenue Capture
- **Task 3.1**: Enhance `src/KerneLSTHook.sol`.
  - Add `emit AlphaCaptured(uint256 amount, string source)` event for every successful arbitrage/liquidation.
- **Task 3.2**: Configure Profit Split.
  - Ensure 80% of BSY profits flow to `KerneVault` (increasing KUSD value) and 20% to the `InsuranceFund`.

## Success Metrics
- **Revenue**: >15% APY generated from arbitrage/liquidation fees.
- **Awareness**: Visibility on Basescan as a top 50 "active" address on Morpho/Aerodrome.
- **Stability**: Maintaining KUSD peg within 0.1% during market volatility.

---
**Note**: This is a plan only. No code has been modified.
