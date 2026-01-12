# Kerne Protocol: Cross-Chain Architecture Design

**Created:** 2026-01-06
**Status:** DRAFT

## 1. Objective
To enable kUSD and $KERNE to move seamlessly across Ethereum L2s (Base, Arbitrum, Optimism, Mantle) while maintaining Base as the primary settlement and hedging hub.

## 2. Core Components

### 2.1. Kerne Bridge (OFT Standard)
We have implemented the **LayerZero OFT (Omnichain Fungible Token)** standard via `src/KerneOFT.sol`.
- **Mechanism:** Burn-and-Mint. Tokens are burned on the source chain and minted on the destination chain via cross-chain messaging.
- **Implementation:** Inherits from `OFTV2` for maximum compatibility across L2s.
- **Benefits:** No liquidity fragmentation, unified supply, and institutional-grade security.

### 2.2. Messaging Layer: LayerZero V2
- **Why LayerZero?** Superior developer experience, wide L2 support, and the ability to configure custom Security Stacks (DVNs).
- **Alternative:** Chainlink CCIP (To be evaluated for institutional "Lock-and-Mint" if required by specific partners).

### 2.3. Cross-Chain TVL Aggregator
A backend service (integrated into the bot) that:
1.  Polls `totalAssets()` from KerneVaults on all supported chains.
2.  Aggregates data into a unified "Global TVL" metric.
3.  Serves this data via `/api/stats` for the frontend.

## 3. Deployment Roadmap

### Phase 1: Base (Genesis) - COMPLETE
- Primary Vault, kUSD Minter, and Hedging Engine live on Base.

### Phase 2: Arbitrum Expansion (Week 2)
- Deploy `kUSD_OFT` and `KERNE_OFT` on Arbitrum.
- Deploy Bespoke Arbitrum Vault (LST-collateralized).
- Integrate Arbitrum TVL into the Global Dashboard.

### Phase 3: Optimism & Mantle (Week 3)
- Standardized deployment of OFT contracts.
- Liquidity seeding on Aerodrome (Base) and Velodrome (Optimism).

## 4. Security Considerations
- **DVN Configuration:** Use a 3-of-5 multisig of decentralized verifiers (e.g., LayerZero, Google Cloud, Animoca).
- **Rate Limiting:** Implement per-chain daily bridge limits to mitigate potential exploit impact.
- **Emergency Pause:** Global "Kill Switch" to pause bridging across all chains.

---
**Kerne Core Architecture Team**
*Omnichain. Scalable. Dominant.*
