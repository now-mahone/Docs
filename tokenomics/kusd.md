# kUSD: The Liquid Standard

**kUSD** is Kerne's native synthetic dollar—a delta-neutral, yield-bearing asset engineered for the Base ecosystem. It is the liquid standard for onchain capital.

## Mechanism

kUSD is minted against LST collateral at a 1:1 ratio. The protocol enforces the $1 peg through:
1. **Industrialized Hedging**: Every kUSD is backed by a matched short position on a Tier 1 exchange, neutralizing volatility and ensuring 100% collateralization in dollar terms.
2. **Peg Stability Module (PSM)**: Facilitates 1:1 swaps between kUSD and USDC, providing a hard arbitrage floor and ceiling.
3. **Dynamic Yield Management**: The protocol adjusts yield distribution to kUSD holders to manage demand and maintain peg stability with mathematical precision.

## Native Yield

Unlike legacy stablecoins, kUSD is natively yield-bearing. The yield extracted from the hedging engine (funding rates) and LST staking is funneled directly to kUSD holders, making it the superior unit of account for the decentralized economy.

## The Synthetic Pivot

As Kerne scales, kUSD will transition from a simple derivative to a **Collateralized Debt Position (CDP)** asset. Users will be able to lock their yield bearing KerneVault shares to mint kUSD, unlocking liquid capital while continuing to earn staking rewards and protocol points.