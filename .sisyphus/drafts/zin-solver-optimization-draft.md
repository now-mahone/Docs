# Draft: ZIN Solver Optimization: Multi-Venue Intent Capture

## Objective
Upgrade the Kerne ZIN Solver to capture intents from 1inch Fusion, LI.FI, and Aori, maximizing spread capture and protocol revenue.

## Key Components
1.  **Extensible Solver Architecture**: Refactor `zin_solver.py` to allow easy addition of new intent sources.
2.  **New Venue Integrations**:
    *   **1inch Fusion**: High-volume Dutch auctions on Base/Arbitrum.
    *   **LI.FI**: Cross-chain and local intent flow.
    *   **Aori**: Real-time intent settlement.
3.  **Hedged Pricing Engine**: Leverage Hyperliquid funding rates to outbid competitors.
4.  **On-chain Settlement**: Utilize `KerneIntentExecutorV2` for zero-fee flash loan fulfillment.

## Verification Strategy
-   **Unit Tests**: Mock each venue's API and settlement logic in Solidity.
-   **Integration Tests**: Python-based dry-run tests to verify the full fetch-quote-calculate-fulfill cycle.
-   **Shadow Mode**: Run the solver in dry-run mode on mainnet to validate "winning" bids without risking capital.

## Constraints & Guardrails
-   **Min Profit**: 8-10 bps minimum profit after gas.
-   **Position Caps**: $15-$500 depending on pool liquidity and venue.
-   **Gas Ceiling**: 40 gwei on Base/Arbitrum.
