# Peg Stability Module (PSM)

The **Peg Stability Module** is the protocol's primary mechanism for maintaining the $1.00 peg of kUSD through deterministic arbitrage.

## How It Works

The PSM allows users to swap between kUSD and approved reserve assets (USDC, USDT) at a fixed 1:1 ratio, minus a small fee.

### Minting (USDC → kUSD)
1. User sends USDC to the PSM contract.
2. PSM mints an equivalent amount of kUSD.
3. USDC is deposited into the protocol's Insurance Fund as backing.

### Redeeming (kUSD → USDC)
1. User sends kUSD to the PSM contract.
2. PSM burns the kUSD.
3. USDC is released from the Insurance Fund to the user.

## Fee Structure

| Operation | Fee |
|-----------|-----|
| Mint (USDC → kUSD) | 0.05% |
| Redeem (kUSD → USDC) | 0.05% |

Fees are adjustable via governance to manage demand side pressure on the peg.

## Arbitrage Mechanics

The PSM creates a hard price floor and ceiling for kUSD:

- **If kUSD > $1.00**: Arbitrageurs mint kUSD via PSM (at $1.00) and sell on secondary markets for profit, pushing the price back down.
- **If kUSD < $1.00**: Arbitrageurs buy kUSD on secondary markets and redeem via PSM (at $1.00) for profit, pushing the price back up.

This creates a tight **$0.999 – $1.001** trading range under normal conditions.

## Reserve Management

The PSM reserves are managed conservatively:
- Only Tier 1 stablecoins (USDC, USDT) are accepted as reserve assets.
- Reserve composition is viewable onchain via the Transparency Dashboard.
- The `PAUSER_ROLE` can halt the PSM in emergency conditions (e.g., USDC depeg event).

## Integration with Sentinel V2

Sentinel continuously monitors the PSM's reserve ratio and secondary market prices. If kUSD deviates beyond 0.5% from peg, Sentinel can dynamically adjust PSM fees or trigger emergency measures.