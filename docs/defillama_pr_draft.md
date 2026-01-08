# DefiLlama PR Draft: Add Kerne Protocol

## PR Title
`Add Kerne Protocol (Base)`

## PR Body
### Description
Kerne Protocol is a delta-neutral synthetic dollar protocol on the Base network. It leverages Liquid Staking Tokens (LSTs) as collateral and maintains delta-neutrality through off-chain hedging on centralized exchanges (CEX). This allows for high-yield, capital-efficient synthetic dollars (kUSD) with zero directional exposure to ETH price volatility.

### Methodology
TVL is calculated by calling `totalAssets()` on the `KerneVault` contract. This value includes:
1. On-chain WETH/LST collateral held in the vault.
2. Off-chain assets held on CEX for hedging purposes, reported by the protocol's automated strategist.
3. Institutional hedging reserves maintained for protocol stability.

### Links
- **Website:** https://kerne.ai
- **Twitter:** https://x.com/kerne_protocol
- **Docs:** https://kerne.ai/docs
- **Vault Address (Base):** `0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd`

### Verification
The `totalAssets()` function is publicly callable on Base. The protocol maintains a real-time Solvency Dashboard at https://kerne.ai/terminal showing the breakdown of on-chain and off-chain assets.

---

## Yield Server PR Draft
### PR Title
`Add Kerne Protocol Yield (Base)`

### PR Body
Adding yield tracking for Kerne Protocol's Genesis WETH Vault.
- **Project:** Kerne Protocol
- **Chain:** Base
- **Symbol:** WETH
- **APY:** Variable (Funding rates + LST yield)
- **TVL:** Reported via the Kerne TVL adapter.
