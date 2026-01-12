# Kerne Smart Contract Architecture

**Date:** 2025-12-28
**Standard:** ERC-4626 (Tokenized Vaults)

## 1. Overview
The Kerne smart contract system is built on the ERC-4626 standard to provide a composable and standardized interface for yield-bearing assets. The architecture separates the vault logic from the specific yield-generation strategies.

## 2. Core Contracts

### `KerneVault.sol`
- **Inheritance:** `ERC4626`, `ERC20`, `Ownable`, `Pausable`.
- **Role:** The primary entry point for users. It handles deposits, withdrawals, and share accounting.
- **Asset:** `USDC` (or the underlying LST depending on final implementation).
- **Functions:**
  - `deposit()` / `mint()`: Accepts assets and issues shares.
  - `withdraw()` / `redeem()`: Burns shares and returns assets.
  - `totalAssets()`: Returns the total value managed by the vault (on-chain + off-chain).

### `KUSDPSM.sol`
- **Role:** Peg Stability Module for kUSD.
- **Logic:** Allows 1:1 swaps between kUSD and other stablecoins with tiered institutional fees.

### `KerneYieldOracle.sol`
- **Role:** Manipulation-resistant TWAY yield reporting.
- **Logic:** Records share price observations and calculates annualized yield over a rolling window.

### `KerneVerificationNode.sol`
- **Role:** Cryptographic Proof of Reserve.
- **Logic:** Authorized signers submit signed attestations of off-chain assets, which are verified on-chain to back the vault's solvency.

## 3. Roles & Permissions (Access Control)

- **Admin (Multisig):**
  - Highest authority.
  - Can upgrade contracts (if using proxies).
  - Can change critical parameters (fees, CR thresholds).
  - Can grant/revoke other roles.
- **Strategist (Bot/EOA):**
  - Authorized to trigger rebalancing.
  - Updates the off-chain valuation in `CexStrategy`.
  - Manages the bridging of assets between Base and CEXs.
- **Pauser:**
  - Emergency role capable of halting deposits and withdrawals in case of a security breach or extreme market volatility.

## 4. Security Considerations
- **Oracle Dependency:** Accurate pricing for LSTs and ETH is required to calculate the Collateral Ratio.
- **Slippage Protection:** Strict limits on swaps during deposit/withdrawal.
- **Withdrawal Queue:** Since assets are moved to CEXs, withdrawals may require a buffer or a delay to bridge funds back to Base.
