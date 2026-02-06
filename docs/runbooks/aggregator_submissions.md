# Aggregator Platform Submissions Guide
// Created: 2026-02-05
// Purpose: Practice listing submissions on comparable platforms before re-attempting DefiLlama
// Strategy: Complete successful submission(s) with comparable aggregators first

---

## Strategic Context

DefiLlama PR #17645 was closed by reviewer without merge (2026-02-04). Per Scofield's directive:
> "We will not engage with DefiLlama until we first complete a successful submission with a different company comparable to DefiLlama, so that when we attempt DefiLlama again, we know the process will work and the risk of being blocked or banned is minimized."

This document provides ready-to-submit information for multiple aggregator platforms.

---

## Protocol Information (Common Across All Submissions)

### Basic Info
- **Protocol Name:** Kerne Protocol
- **Website:** https://kerne.ai
- **Category:** DeFi
- **Subcategory:** Yield / Synthetic Dollar / Delta-Neutral
- **Contact Email:** kerne.systems@protonmail.com
- **Twitter:** @KerneProtocol (or backup handle per TWITTER_SETUP_GUIDE.md)
- **GitHub:** https://github.com/kerne-protocol/kerne-main (private) / public repo TBD

### Chains Deployed
1. **Base** (Chain ID: 8453)
2. **Arbitrum One** (Chain ID: 42161)
3. **Optimism** (Chain ID: 10) — deployed but secondary

### Short Description (160 chars)
```
Delta-neutral yield protocol. Deposit ETH, earn stable yield from funding rates and LST staking. Zero directional risk. Built on Base.
```

### Medium Description (500 chars)
```
Kerne Protocol is a delta-neutral synthetic dollar protocol built on Base. Users deposit ETH into ERC-4626 vaults that automatically hedge via perpetual futures on Hyperliquid, eliminating price exposure while capturing funding rate yield and LST staking rewards. The protocol features noncustodial architecture, real-time solvency verification, automated circuit breakers, and cross-chain expansion via LayerZero V2 OFT to Arbitrum and Optimism. Institutional-grade infrastructure for the onchain economy.
```

### Full Description
```
Kerne Protocol is a decentralized delta-neutral yield infrastructure protocol built natively on Base (Coinbase L2). The protocol enables users to earn stable, market-agnostic yield by combining two uncorrelated revenue streams: liquid staking token (LST) rewards and perpetual futures funding rate capture.

How It Works:
1. Users deposit ETH into Kerne's noncustodial ERC-4626 vaults
2. The autonomous hedging engine opens equal-sized short positions on perpetual futures (Hyperliquid), neutralizing all price exposure
3. Users earn yield from funding rates + LST staking rewards, autocompounded as vault share appreciation

Key Features:
- Delta-Neutral Architecture: Zero directional market risk
- ERC-4626 Vaults: Standard composable vault interface on Base and Arbitrum
- kUSD Synthetic Dollar: Yield-bearing stable asset minted against vault collateral
- ZIN (Zero-Fee Intent Network): Intent-based liquidity aggregation with zero-fee flash loans
- Cross-Chain via LayerZero V2: Seamless asset movement between Base, Arbitrum, and Optimism
- Real-Time Solvency: Block-by-block proof of reserves verification
- Automated Circuit Breakers: Sub-second depeg protection and risk management
- Insurance Fund: Protocol revenue allocation for tail risk coverage

The protocol is designed for institutional-grade capital preservation with automated risk management, including Oracle Guard monitoring, dynamic circuit breakers, and multi-layered custody architecture.
```

### Logo Assets
- **Logo PNG:** `frontend/public/kerne-logo.png`
- **Logo SVG:** `frontend/public/kerne-lockup.svg`
- Minimum 256x256px for most platforms

---

## Deployed Contract Addresses

### Base Network (Primary)
| Contract | Address | Verified |
|----------|---------|----------|
| KerneVault (ERC-4626) | `0xDF9a2f5152c533F7fcc3bAdEd41e157C9563C695` | Yes |
| KerneIntentExecutor (ZIN) | `0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995` | Yes |
| KerneZINPool | `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7` | Yes |
| KerneTreasury | `0x0067F4957dea17CF76665F6A6585F6a904362106` | Yes |
| KerneFlashArbBot | `0xaED581A60db89fEe5f1D8f04538c953Cc78A1687` | Yes |
| KerneInsuranceFund | `0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9` | Yes |
| KUSDPSM | `0x7286200Ba4C6Ed5041df55965c484a106F4716FD` | Yes |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | Yes |
| KerneStaking | `0x032Af1631671126A689614c0c957De774b45D582` | Yes |
| kUSD OFT V2 (LayerZero) | `0x257579db2702BAeeBFAC5c19d354f2FF39831299` | Yes |
| KERNE OFT V2 (LayerZero) | `0x4E1ce62F571893eCfD7062937781A766ff64F14e` | Yes |

### Arbitrum One
| Contract | Address | Verified |
|----------|---------|----------|
| KerneVault (ERC-4626) | `0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF` | Yes |
| KerneIntentExecutor (ZIN) | `0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb` | Yes |
| KerneZINPool | `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD` | Yes |
| kUSD OFT (LayerZero) | `0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222` | Yes |
| KERNE OFT (LayerZero) | `0x087365f83caF2E2504c399330F5D15f62Ae7dAC3` | Yes |

### Primary Contract for Tracking (TVL Source)
- **Base Vault:** `0xDF9a2f5152c533F7fcc3bAdEd41e157C9563C695`
- **Arbitrum Vault:** `0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF`

---

## PLATFORM 1: DappRadar (PRIORITY — Strongest Comparable)

### Why DappRadar First
- Self-service "Submit a DApp" form (low rejection risk)
- Tracks DApps across Base, Arbitrum, Optimism (all our chains)
- Comparable in scope and visibility to DefiLlama
- Getting listed here validates our submission process before re-attempting DefiLlama
- URL: https://dappradar.com/dashboard/submit-dapp

### DappRadar Form Fields

| Field | Value |
|-------|-------|
| DApp Name | Kerne Protocol |
| Website | https://kerne.ai |
| Category | DeFi |
| Subcategory | Yield Aggregator / Staking |
| Short Description | Delta-neutral yield protocol. Deposit ETH, earn stable yield from funding rates and LST staking. Zero directional risk. Built on Base. |
| Full Description | (Use Full Description from above) |
| Logo | Upload `kerne-logo.png` (256x256+) |
| Screenshots | Screenshots of the Terminal dashboard |
| Blockchain(s) | Base, Arbitrum One |
| Smart Contract (Base) | `0xDF9a2f5152c533F7fcc3bAdEd41e157C9563C695` |
| Smart Contract (Arbitrum) | `0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF` |
| Twitter | @KerneProtocol |
| Email | kerne.systems@protonmail.com |

### Submission Steps
1. Go to https://dappradar.com/dashboard/submit-dapp
2. Create DappRadar developer account (if needed)
3. Fill in all fields per table above
4. Upload logo and screenshots
5. Submit and await review (typically 3-7 business days)
6. Track submission status in DappRadar dashboard

---

## PLATFORM 2: DeBank (Portfolio Tracker with Protocol Listing)

### Why DeBank
- Major portfolio tracker used by whales and institutions
- Lists protocols with TVL and user metrics
- Open protocol submission via GitHub
- URL: https://debank.com

### DeBank Submission Process
DeBank accepts protocol submissions via their GitHub repository:
- Repository: https://github.com/ApeironCreation/debank-open-api
- Or contact: protocol-listing@debank.com

### Information Needed
| Field | Value |
|-------|-------|
| Protocol ID | kerne |
| Protocol Name | Kerne Protocol |
| Website | https://kerne.ai |
| Logo | 128x128 PNG |
| Chains | Base (8453), Arbitrum (42161) |
| TVL Contracts | Vault addresses (see above) |
| Category | Yield |

---

## PLATFORM 3: GeckoTerminal / CoinGecko (Token + Pool Tracking)

### Why GeckoTerminal
- Tracks on-chain liquidity pools and tokens
- Automatic detection if pools have activity
- CoinGecko token listing adds credibility
- URL: https://www.geckoterminal.com

### GeckoTerminal
GeckoTerminal auto-indexes DEX pools. If there are active Aerodrome/Uniswap pools for KERNE or kUSD on Base, they should appear automatically. Check:
- https://www.geckoterminal.com/base/tokens/0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340 (KERNE)
- https://www.geckoterminal.com/base/tokens/0x257579db2702BAeeBFAC5c19d354f2FF39831299 (kUSD)

### CoinGecko Token Listing
- URL: https://www.coingecko.com/en/coins/token-request
- Requires: Active trading pairs, minimum liquidity, project info
- Timeline: 2-4 weeks review

---

## PLATFORM 4: DeFi Safety (Protocol Review/Rating)

### Why DeFi Safety
- Independent protocol safety ratings
- Institutional investors check DeFi Safety scores
- Having a rating adds credibility
- URL: https://defisafety.com

### Submission
- Submit via their website or email
- They perform an independent review of:
  - Smart contract quality
  - Documentation quality
  - Team transparency
  - Oracles and admin keys
  - Testing coverage (we have 154 tests — strong signal)

---

## PLATFORM 5: L2Beat (L2 Ecosystem Tracker)

### Why L2Beat
- Tracks TVL across all L2s
- High credibility with institutional audience
- URL: https://l2beat.com

### Submission
- GitHub: https://github.com/l2beat/l2beat
- Submit PR adding Kerne to their project tracking
- Requires TVL tracking adapter (similar to DefiLlama)

---

## Submission Priority Order

| Priority | Platform | Difficulty | Timeline | Impact |
|----------|----------|------------|----------|--------|
| 1 | **DappRadar** | Low (self-service form) | 3-7 days | High |
| 2 | **GeckoTerminal** | Auto (if pools active) | Immediate | Medium |
| 3 | **DeBank** | Medium (GitHub PR or email) | 1-2 weeks | High |
| 4 | **DeFi Safety** | Medium (review process) | 2-4 weeks | High (institutional) |
| 5 | **L2Beat** | High (GitHub PR + adapter) | 2-4 weeks | High |

---

## Post-Submission Tracking

| Platform | Submitted | Status | Listed | Notes |
|----------|-----------|--------|--------|-------|
| DappRadar | [ ] | — | [ ] | |
| GeckoTerminal | [ ] | — | [ ] | Auto-indexed? |
| DeBank | [ ] | — | [ ] | |
| DeFi Safety | [ ] | — | [ ] | |
| L2Beat | [ ] | — | [ ] | |
| DefiLlama (PAUSED) | PR closed | Blocked | [ ] | Re-attempt AFTER 1+ successful listing above |

---

## Action Items for Scofield

### Immediate (Today)
1. **Create DappRadar account** at https://dappradar.com/dashboard/submit-dapp
2. **Fill in the form** using the exact values from the DappRadar section above
3. **Upload logo** from `frontend/public/kerne-logo.png`
4. **Take screenshots** of the Terminal dashboard at kerne.ai for the submission
5. **Submit** and note the confirmation/tracking ID

### This Week
6. Check GeckoTerminal for auto-indexed KERNE/kUSD token pages
7. Submit to DeBank via email (protocol-listing@debank.com)

### Next Week
8. Submit to DeFi Safety for independent review
9. Prepare L2Beat GitHub PR

### After First Successful Listing
10. Document the submission process that worked
11. Adapt learnings to prepare improved DefiLlama re-submission
12. Re-submit to DefiLlama with confidence

---

## Screenshots Needed

For the DappRadar submission, take screenshots of:
1. **Main Terminal Dashboard** — showing vault metrics, funding rate, strategy status
2. **Vault Interaction** — deposit/withdraw interface
3. **Transparency Page** — solvency metrics and proof of reserves
4. **Bridge Interface** — LayerZero V2 omnichain bridge
5. **kUSD Minter** — synthetic dollar minting interface

### Screenshot Checklist
- [ ] Terminal dashboard (main view)
- [ ] Vault deposit interface
- [ ] Transparency/solvency page
- [ ] Bridge interface
- [ ] kUSD minter

---

## Notes

- All contract addresses above are verified on their respective block explorers
- Logo is at `frontend/public/kerne-logo.png` (PNG) and `frontend/public/kerne-lockup.svg` (SVG)
- The protocol has 154 passing tests with 0 failures (strong testing signal for DeFi Safety)
- ERC-4626 vault standard compliance is a strong trust signal for aggregators
- LayerZero V2 OFT cross-chain architecture demonstrates production readiness