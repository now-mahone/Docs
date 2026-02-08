# kUSD Synthetic Dollar

**kUSD** is Kerne's native synthetic dollar—a delta-neutral, yield-bearing stablecoin designed for the Ethereum ecosystem.

## Mechanism

kUSD is minted against LST collateral (like stETH) at a 1:1 ratio. The protocol maintains the $1 peg through:
1. **Delta-Neutral Hedging**: Every kUSD minted is backed by an equivalent short position on a CEX, ensuring the underlying collateral value remains stable in dollar terms.
2. **Peg Stability Module (PSM)**: Allows 1:1 swaps between kUSD and other stablecoins (like USDC), providing a hard arbitrage floor and ceiling.
3. **Variable Interest Rates**: The protocol can adjust the yield paid to kUSD holders to incentivize minting or burning, maintaining the peg through demand-side management.

## Yield-Bearing

Unlike traditional stablecoins, kUSD is natively yield-bearing. The yield generated from the hedging engine (funding rates) and LST staking is funneled directly to kUSD holders, making it a superior alternative to non-yield-bearing assets.

## The Synthetic Pivot

As Kerne scales, kUSD will transition from a simple derivative to a **Collateralized Debt Position (CDP)** asset. Users will be able to lock their yield-bearing KerneVault shares to mint kUSD, unlocking liquid capital while continuing to earn staking rewards and protocol points.

---