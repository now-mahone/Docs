# KERNE Token

The **KERNE** token is the core governance and value capture asset of the protocol.

## Utility

1. **Governance**: Token holders vote on protocol parameters, including fee structures, supported LSTs, and AVS (Actively Validated Service) selection in the restaking layer.
2. **Fee Capture**: A portion of all protocol revenue (yield splits, withdrawal fees, spread capture from ZIN) is used to buy back KERNE from the market.
3. **Staking Rewards**: Staked KERNE holders receive a share of the buybacks and "bribe" revenue from AVS projects seeking to access Kerne's liquidity.
4. **Safety Backstop**: In extreme cases, KERNE may be used as a final backstop for protocol solvency.

## The Buyback Flywheel

Kerne implements a self reinforcing economic loop:
1. Protocol generates revenue (in ETH/USDC).
2. `KerneTreasury` uses revenue to buy back KERNE on Aerodrome.
3. Purchased KERNE is distributed to stakers or burned.
4. Token price rises, increasing the APY for liquidity providers (who earn KERNE).
5. Higher APY attracts more TVL, generating more revenue and completing the loop.

## Supply & Distribution

KERNE follows a "Low Float, High FDV" strategy initially, with the majority of the supply locked in the **Prisoner's Dilemma Airdrop** and long term vesting schedules to ensure price stability during the growth phase.