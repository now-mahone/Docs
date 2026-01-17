# Technical Specification: Kerne LST Sentinel (v2.0)

## 1. Overview
The Kerne LST Sentinel is an autonomous DeFi agent designed to stabilize Liquid Staking Token (LST) pegs on the Base network while extracting MEV (Maximal Extractable Value) for the Kerne Protocol Treasury.

## 2. Core Upgrades Required

### 2.1 External Flash Loan Integration
Currently, `KerneFlashArbBot.sol` only supports internal lenders. To scale without upfront capital, we must implement:
- **Aave V3 Flash Loans**: Support for borrowing large amounts of WETH/USDC.
- **Balancer V3 Flash Loans**: Access to Beets/Balancer liquidity pools.
- **Uniswap V3 Flash Swaps**: Intra-transaction borrowing of pool assets.

### 2.2 Aerodrome Slipstream Support
The current router-based approach is inefficient for Aerodrome's new Concentrated Liquidity (CL) pools. We need:
- Direct interaction with `ICLRouter` for Slipstream pools.
- Path encoding for multi-hop CL swaps.

### 2.3 Liquidation Module
To move beyond pure arbitrage, the Sentinel will include:
- `executeLiquidation()`: A function to liquidate underwater positions on Aave/Moonwell where LSTs are used as collateral.
- Target: 50% of the liquidation bonus to be kept as profit.

## 3. Autonomous Discovery (Off-Chain)
The `GraphArbScanner.py` must be updated to:
1.  **Poll Oracles**: Monitor Chainlink/Redstone LST "Fair Price" vs. DEX prices.
2.  **Simulation Engine**: Use `eth_call` or `tenderly` to simulate transactions before broadcasting to avoid failing on-chain and wasting gas.
3.  **Flashbots/MEV Protection**: Evaluate the use of private RPCs (if available on Base) to prevent front-running.

## 4. Branding & Identity
- **Address Vanity**: Generate an `0x6b65726e...` (Kerne) executor address.
- **On-Chain Tagging**: Every `ArbExecuted` event will include a `protocolId` to clearly identify Kerne as the stabilizer.
