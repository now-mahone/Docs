# KERNE Token

The **KERNE** token is the definitive governance and value-capture asset of the protocol.

## Utility

1. **Governance**: Token holders dictate protocol parameters, including fee structures, collateral whitelisting, and AVS (Actively Validated Service) selection.
2. **Revenue Capture**: A significant portion of all protocol revenue (yield splits, ZIN spread capture) is utilized to buy back KERNE from the open market.
3. **Staking Rewards**: Staked KERNE holders receive a direct share of buybacks and "bribe" revenue from AVS projects competing for Kerne's liquidity.
4. **Safety Backstop**: In extreme scenarios, KERNE serves as the final backstop for protocol solvency, ensuring the integrity of the synthetic dollar.

## The Buyback Flywheel

Kerne implements a self-reinforcing economic loop designed for exponential growth:
1. Protocol extracts revenue (ETH/USDC).
2. `KerneTreasury` utilizes revenue to buy back KERNE on Aerodrome.
3. Purchased KERNE is distributed to stakers or burned, reducing circulating supply.
4. Token price appreciation increases the APY for liquidity providers.
5. Higher APY absorbs more TVL, generating more revenue and accelerating the flywheel.

## Supply & Distribution

KERNE follows a "Low Float, High FDV" strategy initially, with the majority of the supply locked in the **Prisoner's Dilemma Airdrop** and long term vesting schedules to ensure price stability during the growth phase.