# Protocol Architecture

Kerne is a modular suite of smart contracts and off-chain engines engineered to maintain a delta-neutral position while extracting maximum yield.

## Execution Logic

1. **Deposit**: Users deposit ETH or Liquid Staking Tokens (stETH, wstETH, cbETH) into the `KerneVault`.
2. **Hedge**: The offchain Hedging Engine detects the deposit and opens an equivalent short position on a Centralized Exchange (e.g., Hyperliquid, Binance) using the protocol's insurance fund as margin.
3. **Yield Generation**:
    - **Onchain**: Assets earn staking rewards from the underlying LSTs.
    - **Offchain**: The short position captures perpetual funding rates.
    - **Spread Capture**: The `KerneZINPool` uses idle liquidity to fulfill market intents, capturing spreads.
4. **Socialization**: Yield is socialized among vault participants, increasing the share price of the vault.
5. **Withdrawal**: Users can withdraw their principal and accrued yield at any time, subject to protocol liquidity and hedging adjustments.

## The Infrastructure

### 1. KerneVault (ERC-4626)
The primary liquidity gateway. It manages accounting, share minting, and real-time interaction with the hedging engine.

### 2. Peg Stability Module (PSM)
The stability anchor for kUSD. It facilitates high-efficiency swaps between kUSD and collateral assets (USDC/stETH) within strict price bounds, backed by protocol reserves.

### 3. Hedging Engine
A high-performance Python engine that monitors onchain events and executes CEX-based short positions to enforce delta neutrality.

### 4. Zero-Fee Intent Network (ZIN)
A decentralized execution layer that allows authorized solvers to fulfill swaps using protocol liquidity, capturing market spreads for the Kerne ecosystem.

### 5. KerneTreasury & Insurance Fund
The **Capital Fortress**. The Treasury manages revenue distribution (buybacks and founder fees), while the Insurance Fund provides the margin required for CEX hedging and protocol solvency.
