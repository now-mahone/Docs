// Created: 2026-02-05
# ZIN Seeding & Multi-Chain Activation Strategy

This document outlines the plan to activate the Zero-Fee Intent Network (ZIN) across Base and Arbitrum by seeding liquidity and ensuring operational readiness.

## 1. Current Status
- **Base ZIN Pool**: ~$39.77 USDC liquidity.
- **Arbitrum ZIN Pool**: $0 liquidity.
- **Bot Wallet**: Low gas (~0.004 ETH on Base, ~0.0006 ETH on Arbitrum).
- **Hyperliquid**: $32.2 withdrawable.

## 2. Seeding Plan

### Step 1: Capital Extraction
- **Action**: Withdraw $32.2 USDC from Hyperliquid to the bot wallet (`0x57D400cED462a01Ed51a5De038F204Df49690A99`).
- **Tool**: Use `bot/exchanges/hyperliquid.py` or the HL UI.

### Step 2: Liquidity Distribution
- **Base**: Keep ~$20 USDC in the Base ZIN Pool to maintain existing flow.
- **Arbitrum**: Seed the Arbitrum ZIN Pool with ~$12 USDC to enable initial intent fulfillment.
- **Execution**:
    ```bash
    # Seed Arbitrum ZIN Pool (once USDC is in wallet)
    forge script script/SeedZINPool.s.sol --rpc-url https://arb1.arbitrum.io/rpc --broadcast
    ```

### Step 3: Gas Management
- **Action**: Bridge 0.01 ETH to Arbitrum to ensure the solver can execute transactions.
- **Tool**: Use a bridge (e.g., Bungee, Jumper) or transfer from a CEX.

## 3. Multi-Chain Activation
- **Solver Config**: `bot/.env` is already set to `ZIN_CHAINS=base,arbitrum`.
- **Verification**:
    - `SOLVER_ROLE` is granted on both chains.
    - Tokens (USDC, WETH, wstETH) are whitelisted on both chains.
- **Monitoring**: Run `python bot/profit_telemetry.py --metrics-only` to verify liquidity and order flow.

## 4. Expected Gains
- **Increased Volume**: Arbitrum typically has 3-5x higher intent volume than Base.
- **Spread Capture**: Capturing 5-10 bps on every fill across two chains.
- **Organic Awareness**: "Filled by Kerne" appearing on Arbiscan and Basescan.