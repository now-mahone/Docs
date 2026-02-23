# Arbitrum ZIN Deployment - Ready to Execute
**Date:** 2026-01-20
**Status:** AWAITING_FUNDING

## Summary
The ZIN deployment to Arbitrum has been simulated and is ready to execute. The only blocker is funding the deployer wallet with ETH on Arbitrum.

## Deployment Details

### Estimated Costs
| Metric | Value |
|--------|-------|
| Gas Required | ~4,021,706 gas |
| Gas Price | 0.04 gwei |
| **Total Cost** | **~0.00016 ETH (~$0.53)** |
| Recommended Funding | 0.0005 ETH (~$1.65) |

### Deployer Wallet
- **Address:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Current Arbitrum Balance:** 0 ETH ❌
- **Current Ethereum Balance:** 0.00076 ETH (~$2.50) ✅

### Contracts to Deploy
| Contract | Simulated Address |
|----------|-------------------|
| KerneIntentExecutorV2 | `0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb` |
| KerneZINPool | `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD` |

### Tokens to Support
- USDC (native): `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
- USDC.e (bridged): `0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8`
- WETH: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`
- wstETH: `0x5979D7b546E38E414F7E9822514be443A4800529`

## Funding Options

### Option A: Bridge from Ethereum (via Arbitrum Bridge)
1. Go to https://bridge.arbitrum.io/
2. Connect wallet with deployer address
3. Bridge 0.0005 ETH from Ethereum to Arbitrum
4. Wait ~10 minutes for confirmation
5. **Note:** Ethereum gas may cost $1-3

### Option B: Bridge via Across Protocol (Cheaper)
1. Go to https://across.to/
2. Bridge 0.0005 ETH from Ethereum to Arbitrum
3. Fees typically $0.50-1.00

### Option C: Direct Exchange Withdrawal (Recommended)
1. From any exchange (Binance, Coinbase, Kraken)
2. Withdraw 0.001 ETH to `0x57D400cED462a01Ed51a5De038F204Df49690A99`
3. Select **Arbitrum One** network
4. Wait for confirmation (~1 minute)

## Deployment Command
Once funded, execute:
```bash
forge script script/DeployZINArbitrum.s.sol:DeployZINArbitrum \
    --rpc-url https://arb1.arbitrum.io/rpc \
    --broadcast \
    --verify \
    --etherscan-api-key $ARBISCAN_API_KEY
```

## Post-Deployment Steps
1. Grant SOLVER_ROLE to bot wallet
2. Seed ZIN Pool with initial liquidity (USDC/WETH)
3. Update `bot/.env` with new Arbitrum addresses
4. Configure solver for multi-chain operation

## Why Arbitrum?
- **3-5x higher intent volume** than Base via UniswapX Dutch_V2 orders
- Lower gas costs than Ethereum mainnet
- Large DeFi ecosystem with significant trading activity
- Diversifies revenue across multiple chains

---
*Generated: 2026-01-20 15:15 MST*
