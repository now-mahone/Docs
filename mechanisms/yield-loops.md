# Leveraged Yield Loops

Kerne implements a **One-Click Recursive Leverage Strategy** directly into the protocol's interface, allowing users to maximize their capital efficiency without complex manual operations.

## How it Works

In a standard DeFi interaction, a user deposits 10 ETH and earns yield on 10 ETH. In Kerne, the protocol can automate a "looping" process:

1. **Initial Deposit**: User deposits 10 ETH.
2. **Flash Loan**: The protocol takes a flash loan of 40 ETH.
3. **Staking**: The total 50 ETH is staked into LSTs (e.g., wstETH).
4. **Collateralization**: The 50 ETH worth of LSTs is deposited into the KerneVault as collateral.
5. **Borrowing**: The protocol borrows ETH against the LST collateral.
6. **Repayment**: The flash loan is repaid using the borrowed ETH.

The result is a **5x leveraged position** (50 ETH position backed by 10 ETH principal).

## Benefits

- **Boosted Yields**: Users earn 5x the staking rewards and 5x the points.
- **Minimal Liquidation Risk**: Because the collateral (LST) and the debt (ETH) are highly correlated assets, the risk of liquidation is significantly lower than traditional cross-asset leverage.
- **TVL Bloating**: This mechanism artificially inflates the protocol's Total Value Locked (TVL) metrics, which is a primary driver for valuation and institutional interest.

## Risks

- **Depeg Risk**: If the LST loses its peg significantly against ETH, the position could face liquidation. Kerne's **Sentinel V2** monitors these ratios in real-time to trigger emergency deleveraging if necessary.
- **Cost of Leverage**: The cost of borrowing ETH must be lower than the staking yield + points value for the loop to remain profitable.

---