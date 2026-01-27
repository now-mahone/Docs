# Protocol Architecture

Kerne is designed as a modular suite of smart contracts and off-chain engines that work in harmony to maintain a delta-neutral position while extracting maximum yield.

## High-Level Workflow

1. **Deposit**: Users deposit ETH or Liquid Staking Tokens (stETH, wstETH, cbETH) into the `KerneVault`.
2. **Hedge**: The off-chain Hedging Engine detects the deposit and opens an equivalent short position on a Centralized Exchange (e.g., Hyperliquid, Binance) using the protocol's insurance fund as margin.
3. **Yield Generation**:
    - **On-chain**: Assets earn staking rewards from the underlying LSTs.
    - **Off-chain**: The short position captures perpetual funding rates.
    - **Spread Capture**: The `KerneZINPool` uses idle liquidity to fulfill market intents, capturing spreads.
4. **Socialization**: Yield is socialized among vault participants, increasing the share price of the vault.
5. **Withdrawal**: Users can withdraw their principal and accrued yield at any time, subject to protocol liquidity and hedging adjustments.

## Core Components

### 1. KerneVault (ERC-4626)
The entry point for all liquidity. It handles accounting, share minting, and interaction with the hedging engine.

### 2. Peg Stability Module (PSM)
Ensures the stability of kUSD by allowing users to swap between kUSD and collateral assets (like USDC or stETH) within tight price bounds, backed by the protocol's reserves.

### 3. Hedging Engine (Bot)
A high-performance Python engine that monitors on-chain events and manages the CEX-based short positions to maintain delta-neutrality.

### 4. Zero-Fee Intent Network (ZIN)
A decentralized execution layer that allows authorized solvers to fulfill swaps and intents using the protocol's liquidity, with spreads captured for Kerne token holders.

### 5. KerneTreasury & Insurance Fund
The "Capital Fortress" of the protocol. The Treasury manages revenue distribution (buybacks and founder fees), while the Insurance Fund provides the margin required for CEX hedging.

---
*Created: 2026-01-26*
