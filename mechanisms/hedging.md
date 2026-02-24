# Delta-Neutral Hedging Engine

The core of Kerne's yield generation is the **Delta-Neutral Hedging Engine**. This off-chain system ensures the protocol remains market-neutral while systematically capturing premium yields.

## Strategy: Funding Rate Optimization

The engine exploits the spread between onchain staking yields and off-chain perpetual funding rates.

1. **Long Position**: Kerne holds physical ETH or LSTs (like stETH) onchain, earning ~3-4% APR from Ethereum consensus.
2. **Short Position**: The engine opens a 1x short position on a Perpetual Exchange (e.g., Hyperliquid) for an equivalent amount of ETH.
3. **Delta Neutrality**: The price movements of the long (onchain) and short (offchain) positions cancel each other out. The net exposure to the price of ETH is zero.
4. **Funding Capture**: In bullish markets, "Longs" pay "Shorts" a funding rate. Kerne's short position captures this rate, which can often exceed 10-20% APR.

## Components

### 1. Exchange Manager
Interfaces with CEX APIs (via CCXT) to execute trades, manage margin, and monitor equity.

### 2. Chain Manager
Monitors the `KerneVault` on multiple chains (Base, Arbitrum) for deposits and withdrawals, ensuring the hedge stays perfectly balanced.

### 3. Sentinel V2
The risk management core. It performs submillisecond VaR (Value at Risk) analysis and monitors LST/ETH pegs to prevent insolvency during black swan events.

## Dynamic Leverage: The Scofield Point

Kerne does not settle for 1:1 hedging. The engine utilizes a proprietary model called the **Scofield Point** to optimize leverage. During periods of elevated funding rates, the engine increases leverage to maximize return on equity, while maintaining a strict safety buffer within the Insurance Fund to ensure protocol survival.
