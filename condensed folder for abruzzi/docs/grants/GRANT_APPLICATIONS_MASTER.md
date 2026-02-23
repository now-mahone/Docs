// Created: 2026-02-08
# Kerne Protocol — Grant Applications Master Document

## Overview
This document ranks ALL viable grant programs from best to worst for Kerne Protocol, with application-ready materials for each. Programs are ranked by: (1) likelihood of approval, (2) grant size, (3) strategic value beyond money, (4) application effort, and (5) timeline to funding.

**Protocol Summary for All Applications:**
- Delta-neutral yield infrastructure on Base + Arbitrum (+ Optimism pending)
- ERC-4626 vaults, LayerZero V2 cross-chain, Hyperliquid hedging
- 35+ verified smart contracts, 150+ Foundry tests
- Live basis trade generating real yield
- 8 Docker services running 24/7 on cloud infrastructure
- Team: 2 core contributors

---

## RANKED GRANT PROGRAMS

---

### #1. Base Builder Grants (Coinbase / Base)
**Rank Justification:** Kerne is NATIVELY built on Base. We already submitted PR #2956 to the Base Ecosystem Directory. Base actively funds DeFi infrastructure that brings TVL and users to their chain. This is the highest-probability grant.

**Program Details:**
- **URL:** https://base.org/grants (or via Prop House / Base Discord)
- **Grant Size:** $5,000 – $250,000 (in ETH or USDC)
- **Review Time:** 2–6 weeks
- **Requirements:** Deployed on Base, open-source or verified contracts, active development
- **Contact:** Base Discord #grants channel, or builders@base.org

**Why Kerne Qualifies:**
- Natively built on Base mainnet with verified contracts
- ERC-4626 standard vault (composable with Base DeFi ecosystem)
- Brings TVL to Base (delta-neutral vaults attract sticky capital)
- Cross-chain bridge to Arbitrum/Optimism via LayerZero V2 (brings liquidity TO Base)
- Already in Base Ecosystem Directory review (PR #2956)
- Real-time solvency API and transparency dashboard

**Application Pitch:**
```
Project: Kerne Protocol
Category: DeFi Infrastructure / Yield
Chain: Base (primary), Arbitrum, Optimism

Summary:
Kerne is delta-neutral yield infrastructure built natively on Base. Users deposit ETH into noncustodial ERC-4626 vaults and earn stable yield from funding rate capture and LST staking — with zero directional market risk. The protocol features an autonomous hedging engine, real-time solvency verification, automated circuit breakers, and cross-chain expansion via LayerZero V2.

What We've Built:
• KerneVault (ERC-4626) deployed and verified on Base: 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
• 35+ smart contracts across Base and Arbitrum, all verified on BaseScan/Arbiscan
• 150+ Foundry tests (unit, integration, fuzzing, invariant)
• Autonomous hedging engine running 24/7 on cloud infrastructure (8 Docker services)
• Live basis trade generating real yield from Hyperliquid funding rates
• ZIN (Zero-Fee Intent Network) for gasless intent-based execution
• Cross-chain kUSD and KERNE tokens via LayerZero V2 OFT
• Full documentation site, transparency dashboard, and terminal interface at kerne.ai

What We Need Funding For:
1. External Security Audit ($30,000–$50,000) — Top priority for institutional trust
2. Liquidity Bootstrapping ($10,000–$25,000) — Seed vault TVL to demonstrate mechanism at scale
3. Operational Costs ($5,000–$10,000) — Cloud infrastructure, domains, tooling for 6 months
4. User Acquisition ($5,000–$10,000) — Incentive programs for Base-native depositors

Milestones:
• Month 1: Complete external audit, reach $100k TVL
• Month 2: Launch liquidity mining program on Base, reach $500k TVL
• Month 3: Integrate with Base-native DEXs (Aerodrome), reach $1M TVL
• Month 6: $5M+ TVL, 1,000+ unique depositors on Base

Team:
2 core contributors with deep Solidity, Python, and DeFi infrastructure experience. Building full-time since January 2026.

Links:
• Website: https://kerne.ai
• Docs: https://docs.kerne.ai
• Twitter: @KerneProtocol
• Base Vault: https://basescan.org/address/0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
• Base Ecosystem PR: https://github.com/base/web/pull/2956
```

**Worst Case:** Rejected due to low TVL. Reapply after reaching $10k+ TVL.

---

### #2. Optimism RetroPGF (Retroactive Public Goods Funding)
**Rank Justification:** Optimism's RetroPGF is one of the largest grant programs in crypto ($10M+ per round). Kerne's cross-chain infrastructure and open-source tooling qualify as "public goods." We have pre-flighted contracts on Optimism already.

**Program Details:**
- **URL:** https://app.optimism.io/retropgf / https://community.optimism.io/
- **Grant Size:** $1,000 – $500,000+ (in OP tokens)
- **Review Time:** Rounds occur periodically (check current round status)
- **Requirements:** Must demonstrate impact to the Optimism ecosystem
- **Contact:** Optimism Discord, Optimism Governance Forum

**Why Kerne Qualifies:**
- Pre-flighted contracts on Optimism (5 contracts awaiting gas)
- LayerZero V2 OFT bridges bring liquidity to Optimism
- ERC-4626 standard benefits the entire Optimism DeFi ecosystem
- Delta-neutral vaults provide stable yield infrastructure (public good)
- Open-source verified contracts on-chain

**Application Pitch:**
```
Project: Kerne Protocol
Impact Area: DeFi Infrastructure on Optimism

Kerne provides delta-neutral yield infrastructure that benefits the Optimism ecosystem by:
1. Bringing stable, market-agnostic yield to Optimism users (no directional risk)
2. Deploying ERC-4626 composable vaults that other Optimism protocols can integrate
3. Bridging liquidity from Base and Arbitrum TO Optimism via LayerZero V2
4. Providing open-source, verified smart contract infrastructure

We have 5 contracts pre-flighted on Optimism mainnet ready for deployment:
- KerneVault, ZIN Executor, ZIN Pool, kUSD OFT V2, KERNE OFT V2

Funding would be used for:
- Completing Optimism deployment and seeding initial liquidity
- External security audit covering Optimism contracts
- User acquisition incentives for Optimism-native depositors
```

**Worst Case:** RetroPGF round timing doesn't align. We apply to the next available round.

---

### #3. Arbitrum Foundation Grants (LTIPP / STIP)
**Rank Justification:** Kerne is already deployed on Arbitrum with verified contracts. Arbitrum has the largest L2 TVL and runs active grant programs (LTIPP — Long-Term Incentives Pilot Program, and STIP — Short-Term Incentives Program).

**Program Details:**
- **URL:** https://arbitrum.foundation/grants / https://forum.arbitrum.foundation/
- **Grant Size:** $50,000 – $2,000,000 (in ARB tokens)
- **Review Time:** 4–12 weeks (depends on program cycle)
- **Requirements:** Deployed on Arbitrum, demonstrable TVL or user activity
- **Contact:** Arbitrum Discord, Arbitrum Governance Forum

**Why Kerne Qualifies:**
- KerneVault deployed and verified on Arbitrum: 0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
- ZIN infrastructure live on Arbitrum (Executor + Pool)
- kUSD and KERNE OFT V2 tokens deployed on Arbitrum
- Cross-chain bridge from Base brings new liquidity to Arbitrum
- ERC-4626 composable with Arbitrum DeFi ecosystem

**Application Pitch:**
```
Project: Kerne Protocol
Category: DeFi / Yield Infrastructure
Arbitrum Contracts:
- KerneVault: 0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
- ZIN Executor: 0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb
- ZIN Pool: 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD
- kUSD OFT V2: 0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222
- KERNE OFT V2: 0x087365f83caF2E2504c399330F5D15f62Ae7dAC3

Request: ARB tokens for liquidity incentives and audit funding

How Kerne Benefits Arbitrum:
1. Brings stable yield infrastructure that attracts sticky TVL
2. ERC-4626 vaults composable with GMX, Aave, Pendle on Arbitrum
3. ZIN intent network provides zero-fee execution for Arbitrum users
4. Cross-chain bridge from Base/Optimism brings new capital to Arbitrum
5. Delta-neutral architecture means deposited capital stays on Arbitrum long-term

Milestones:
- Month 1: $100k TVL on Arbitrum vault
- Month 3: Integration with 2+ Arbitrum-native protocols
- Month 6: $1M+ TVL, 500+ unique Arbitrum depositors
```

**Worst Case:** LTIPP/STIP cycle has ended. We apply to the next cycle or the general grants program.

---

### #4. LayerZero Ecosystem Grants
**Rank Justification:** Kerne uses LayerZero V2 OFT standard for cross-chain kUSD and KERNE tokens. LayerZero has an ecosystem fund and actively supports protocols building on their infrastructure.

**Program Details:**
- **URL:** https://layerzero.network/ecosystem / Contact via Discord or partnerships@layerzero.network
- **Grant Size:** $10,000 – $100,000 (varies)
- **Review Time:** 2–8 weeks
- **Requirements:** Active use of LayerZero infrastructure
- **Contact:** LayerZero Discord, Bryan Pellegrino (CEO) on Twitter

**Why Kerne Qualifies:**
- 4 LayerZero V2 OFT contracts deployed (kUSD + KERNE on Base + Arbitrum)
- Optimism OFTs pre-flighted (expanding to 6 total)
- Active cross-chain messaging between Base ↔ Arbitrum
- Demonstrates real utility of LayerZero V2 OFT standard for DeFi

**Application Pitch:**
```
Project: Kerne Protocol
LayerZero Integration: V2 OFT Standard

We use LayerZero V2 OFT for cross-chain kUSD (synthetic dollar) and KERNE (governance token) across Base, Arbitrum, and Optimism. Our deployment demonstrates the OFT standard's utility for DeFi yield infrastructure — enabling seamless cross-chain deposits and unified liquidity.

Deployed OFT Contracts:
- Base kUSD OFT V2: 0x257579db2702BAeeBFAC5c19d354f2FF39831299
- Base KERNE OFT V2: 0x4E1ce62F571893eCfD7062937781A766ff64F14e
- Arbitrum kUSD OFT V2: 0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222
- Arbitrum KERNE OFT V2: 0x087365f83caF2E2504c399330F5D15f62Ae7dAC3

Funding would support:
- Completing 3-way peer wiring (Base ↔ Arbitrum ↔ Optimism)
- Building a cross-chain yield aggregation layer using LayerZero messaging
- Case study / documentation showcasing OFT V2 for DeFi infrastructure
```

**Worst Case:** LayerZero doesn't have an active grant program. We build the relationship for future opportunities.

---

### #5. Hyperliquid Ecosystem / Builder Program
**Rank Justification:** Kerne uses Hyperliquid as its PRIMARY hedging venue. The entire delta-neutral mechanism depends on Hyperliquid perpetual futures. Hyperliquid has been growing rapidly and may have builder incentives.

**Program Details:**
- **URL:** https://hyperliquid.xyz / Check Discord for builder programs
- **Grant Size:** Unknown (potentially HYPE tokens or fee rebates)
- **Review Time:** Variable
- **Requirements:** Active use of Hyperliquid infrastructure
- **Contact:** Hyperliquid Discord, Twitter DM

**Why Kerne Qualifies:**
- Active short positions on Hyperliquid ETH-PERP
- Generates trading volume and open interest for Hyperliquid
- Demonstrates institutional use case for Hyperliquid perpetuals
- Could bring significant volume as TVL scales ($1M TVL = ~$1M in perpetual positions)

**Application Pitch:**
```
Project: Kerne Protocol
Hyperliquid Usage: Primary hedging venue for delta-neutral yield

Kerne deposits ETH into on-chain vaults and opens matching short positions on Hyperliquid ETH-PERP to create delta-neutral yield. As our TVL grows, we bring proportional trading volume and open interest to Hyperliquid.

Current: ~$119 short position (seed stage)
Target: $1M+ in perpetual positions within 6 months

We would welcome:
- Fee rebates or maker incentives for our hedging volume
- HYPE token allocation for liquidity bootstrapping
- Co-marketing as a showcase of institutional Hyperliquid usage
- API priority access for our autonomous hedging engine
```

**Worst Case:** Hyperliquid doesn't have a formal grant program. We still benefit from the relationship and potential fee rebates.

---

### #6. Gitcoin Grants (GG rounds)
**Rank Justification:** Gitcoin runs quarterly grant rounds with quadratic funding. DeFi infrastructure projects can receive significant funding through community matching. Low barrier to entry.

**Program Details:**
- **URL:** https://grants.gitcoin.co/
- **Grant Size:** $500 – $50,000+ (depends on community support + matching pool)
- **Review Time:** Rounds are periodic (check current round dates)
- **Requirements:** Open-source or public good component, active project
- **Contact:** Gitcoin Discord

**Why Kerne Qualifies:**
- Verified open-source contracts on BaseScan/Arbiscan
- ERC-4626 standard benefits the broader DeFi ecosystem
- ZIN (Zero-Fee Intent Network) is a public good for gasless execution
- Documentation and SDK are open resources

**Application Pitch:**
```
Project: Kerne Protocol — Delta-Neutral Yield Infrastructure

Kerne provides open, composable yield infrastructure for the Ethereum ecosystem:
- ERC-4626 vaults that any protocol can integrate
- ZIN: Zero-fee intent execution network (public good)
- Cross-chain infrastructure via LayerZero V2
- Open documentation and SDK for developers

Funding supports: audit costs, infrastructure, and continued open development.
```

**Worst Case:** Low community support results in minimal matching. We still get visibility and a Gitcoin profile.

---

### #7. Questbook DeFi Grants
**Rank Justification:** Questbook runs domain-specific grant programs, including DeFi-focused rounds often funded by L2 foundations. Lower competition than direct foundation grants.

**Program Details:**
- **URL:** https://questbook.app/
- **Grant Size:** $2,000 – $50,000
- **Review Time:** 2–4 weeks
- **Requirements:** Working product, clear milestones
- **Contact:** Questbook platform (apply directly)

**Why Kerne Qualifies:**
- Working product deployed on multiple chains
- Clear milestones (audit, TVL targets, integrations)
- DeFi infrastructure category

**Application Pitch:**
```
Same as Base Builder Grants pitch, adapted for Questbook format.
Focus on milestones and deliverables.
```

**Worst Case:** Application rejected. Minimal time investment.

---

### #8. Chainlink BUILD Program
**Rank Justification:** Kerne uses Chainlink price feeds for solvency reporting. The BUILD program provides grants, technical support, and co-marketing to projects integrating Chainlink.

**Program Details:**
- **URL:** https://chain.link/economics/build
- **Grant Size:** Technical support + LINK tokens + co-marketing
- **Review Time:** 4–8 weeks
- **Requirements:** Active Chainlink integration
- **Contact:** build@chain.link

**Why Kerne Qualifies:**
- Uses Chainlink price feeds for solvency verification
- Potential to integrate Chainlink CCIP for cross-chain messaging
- Chainlink Proof of Reserve integration for institutional trust

**Application Pitch:**
```
Project: Kerne Protocol
Chainlink Integration: Price feeds for real-time solvency verification

We use Chainlink ETH/USD price feeds to calculate and verify protocol solvency ratios in real-time. We plan to expand integration to:
1. Chainlink Proof of Reserve for institutional-grade attestation
2. Chainlink CCIP as an alternative cross-chain messaging layer
3. Chainlink Automation for scheduled vault rebalancing

BUILD program benefits we seek:
- Technical support for PoR integration
- LINK tokens for oracle gas costs
- Co-marketing as a Chainlink-powered DeFi protocol
```

**Worst Case:** Not accepted into BUILD. We continue using Chainlink independently.

---

### #9. Ethereum Foundation Ecosystem Support Program (ESP)
**Rank Justification:** The EF ESP funds projects that benefit the Ethereum ecosystem. Kerne's ERC-4626 infrastructure and delta-neutral yield mechanism are ecosystem-level contributions. However, EF grants are highly competitive.

**Program Details:**
- **URL:** https://esp.ethereum.foundation/
- **Grant Size:** $5,000 – $500,000
- **Review Time:** 4–12 weeks
- **Requirements:** Benefit to Ethereum ecosystem, open-source component
- **Contact:** esp@ethereum.foundation

**Why Kerne Qualifies:**
- ERC-4626 standard implementation benefits Ethereum DeFi composability
- Delta-neutral yield infrastructure reduces systemic risk in DeFi
- Cross-chain architecture demonstrates Ethereum L2 interoperability
- Open-source verified contracts

**Application Pitch:**
```
Project: Kerne Protocol
Category: DeFi Infrastructure / Standards

Kerne contributes to the Ethereum ecosystem by:
1. Implementing ERC-4626 standard vaults that demonstrate composability across L2s
2. Providing delta-neutral yield infrastructure that reduces systemic directional risk
3. Building cross-chain infrastructure (Base + Arbitrum + Optimism) via LayerZero V2
4. Publishing open documentation and SDK for developer adoption

Funding supports: security audit, continued development, and ecosystem integration.
```

**Worst Case:** Rejected due to high competition. We gain visibility with the EF team.

---

### #10. Uniswap Foundation Grants
**Rank Justification:** Kerne's ZIN intent network and vault infrastructure interact with Uniswap liquidity. The Uniswap Foundation funds projects that enhance the Uniswap ecosystem.

**Program Details:**
- **URL:** https://www.uniswapfoundation.org/grants
- **Grant Size:** $10,000 – $250,000
- **Review Time:** 4–8 weeks
- **Requirements:** Enhancement to Uniswap ecosystem
- **Contact:** grants@uniswapfoundation.org

**Why Kerne Qualifies:**
- ZIN intent network routes through Uniswap V3 pools
- Vault deposits/withdrawals use Uniswap for swaps
- Flash-arb bot detects and captures arbitrage across Uniswap pools

**Worst Case:** Rejected — our Uniswap integration is not deep enough. Low effort to apply.

---

### #11. Aave Grants DAO
**Rank Justification:** Kerne's vault architecture is inspired by Aave's lending model. Integration with Aave for leverage or collateral could qualify for grants.

**Program Details:**
- **URL:** https://aavegrants.org/
- **Grant Size:** $5,000 – $100,000
- **Review Time:** 4–8 weeks
- **Requirements:** Enhancement to Aave ecosystem

**Why Kerne Qualifies:**
- ERC-4626 vaults could be listed as Aave collateral
- Delta-neutral yield provides stable collateral for Aave borrowers
- Potential integration: deposit Kerne vault shares as Aave collateral

**Worst Case:** Rejected — integration is theoretical. Apply after building Aave integration.

---

### #12. Safe (Gnosis Safe) Ecosystem Grants
**Rank Justification:** Kerne plans to migrate to Gnosis Safe multisig. Safe has a grants program for projects building on their infrastructure.

**Program Details:**
- **URL:** https://safe.global/grants
- **Grant Size:** $5,000 – $50,000
- **Review Time:** 2–6 weeks
- **Requirements:** Integration with Safe infrastructure

**Why Kerne Qualifies:**
- Planning multisig migration to Gnosis Safe
- Institutional vaults designed for Safe integration
- Could build Safe modules for vault management

**Worst Case:** Rejected — integration not yet implemented. Apply after multisig migration.

---

### #13. Lido Ecosystem Grants (LEGO)
**Rank Justification:** Kerne uses wstETH as its primary LST collateral. Lido's LEGO program funds projects that increase wstETH utility and adoption.

**Program Details:**
- **URL:** https://lido.fi/lego
- **Grant Size:** $5,000 – $100,000 (in LDO or stablecoins)
- **Review Time:** 2–6 weeks
- **Requirements:** Increase wstETH utility/adoption
- **Contact:** lego@lido.fi

**Why Kerne Qualifies:**
- Vault accepts wstETH as primary collateral
- Delta-neutral strategy captures wstETH staking yield
- Increases wstETH demand and utility on Base/Arbitrum

**Application Pitch:**
```
Project: Kerne Protocol
wstETH Integration: Primary vault collateral

Kerne vaults accept wstETH and capture both staking yield AND funding rate income through delta-neutral hedging. This creates the highest-yield use case for wstETH on Base and Arbitrum, driving demand and adoption.

Funding supports: wstETH liquidity bootstrapping on Base, audit of wstETH integration.
```

**Worst Case:** Rejected. We continue using wstETH independently.

---

### #14. Compound Grants Program
**Rank Justification:** Lower priority — Kerne doesn't directly integrate with Compound, but the grant program funds general DeFi infrastructure.

**Program Details:**
- **URL:** https://compoundgrants.org/
- **Grant Size:** $5,000 – $50,000
- **Review Time:** 4–8 weeks

**Worst Case:** Rejected. Minimal effort to apply.

---

### #15. Protocol Guild
**Rank Justification:** Protocol Guild funds Ethereum core contributors. Kerne could contribute a portion of protocol revenue to Protocol Guild in exchange for visibility and community goodwill. This is more of a "give to get" strategy than a traditional grant.

**Program Details:**
- **URL:** https://protocol-guild.readthedocs.io/
- **Type:** Pledge (not a grant — we donate, they promote)

**Why Consider:** The Genesis Strategy mentions pledging to public goods as a "Legacy Philanthropic Pivot." Early commitment builds credibility.

**Worst Case:** We donate and get minimal visibility. The donation itself is small.

---

### #16. Alchemy University / Growth Grants
**Rank Justification:** Alchemy provides infrastructure grants and growth programs for projects using their RPC services.

**Program Details:**
- **URL:** https://www.alchemy.com/developer-grant-program
- **Grant Size:** Free infrastructure credits + potential cash grants
- **Review Time:** 1–4 weeks

**Why Kerne Qualifies:**
- Uses RPC infrastructure for on-chain interactions
- Could migrate to Alchemy for enhanced monitoring

**Worst Case:** Only receive infrastructure credits (still valuable — saves operational costs).

---

### #17. Thirdweb Startup Program
**Rank Justification:** Thirdweb offers startup credits and support for Web3 projects. Lower priority but easy to apply.

**Program Details:**
- **URL:** https://thirdweb.com/community/startup-program
- **Grant Size:** Infrastructure credits + mentorship
- **Review Time:** 1–2 weeks

**Worst Case:** Receive credits only. Minimal effort.

---

### #18. CowSwap / CoW DAO Grants
**Rank Justification:** We already have a solver registration pending with CowSwap. CoW DAO has a grants program for solver development and ecosystem projects.

**Program Details:**
- **URL:** https://forum.cow.fi/ (governance forum)
- **Grant Size:** $5,000 – $50,000 (in COW tokens)
- **Review Time:** 4–8 weeks
- **Requirements:** Enhancement to CoW Protocol ecosystem

**Why Kerne Qualifies:**
- Active solver registration pending
- ZIN intent network complements CowSwap's intent-based architecture
- Solver API live at https://kerne-solver.onrender.com/solve

**Worst Case:** Rejected. We continue solver development independently.

---

### #19. Aerodrome / Velodrome Ecosystem Grants
**Rank Justification:** Kerne's treasury buyback mechanism uses Aerodrome on Base. Aerodrome/Velodrome may have ecosystem incentives for protocols that drive volume.

**Program Details:**
- **URL:** Check Aerodrome Discord / governance forum
- **Grant Size:** AERO/VELO token incentives
- **Review Time:** Variable

**Why Kerne Qualifies:**
- Treasury buyback routes through Aerodrome
- KERNE/WETH pool planned on Aerodrome
- Drives trading volume on Aerodrome

**Worst Case:** No formal program exists. We build the relationship for future incentives.

---

## EXECUTION PRIORITY ORDER

| # | Program | Est. Grant Size | Effort | Probability | Action |
|---|---------|----------------|--------|-------------|--------|
| 1 | Base Builder Grants | $25k–$100k | Medium | HIGH | Apply immediately |
| 2 | Optimism RetroPGF | $5k–$100k | Medium | MEDIUM | Apply when round opens |
| 3 | Arbitrum LTIPP/STIP | $50k–$500k | High | MEDIUM | Apply to next cycle |
| 4 | LayerZero Ecosystem | $10k–$50k | Low | MEDIUM | Email + Discord outreach |
| 5 | Hyperliquid Builder | Fee rebates + tokens | Low | MEDIUM | Discord outreach |
| 6 | Gitcoin Grants | $1k–$20k | Low | HIGH | Apply to next round |
| 7 | Questbook DeFi | $5k–$25k | Low | MEDIUM | Apply on platform |
| 8 | Chainlink BUILD | Tech support + LINK | Medium | MEDIUM | Apply via form |
| 9 | Ethereum Foundation ESP | $10k–$100k | High | LOW | Apply via form |
| 10 | Uniswap Foundation | $10k–$50k | Medium | LOW | Apply via form |
| 11 | Aave Grants DAO | $5k–$50k | Medium | LOW | Apply after integration |
| 12 | Safe Ecosystem | $5k–$25k | Low | LOW | Apply after multisig |
| 13 | Lido LEGO | $5k–$50k | Medium | MEDIUM | Apply via email |
| 14 | Compound Grants | $5k–$25k | Low | LOW | Apply via form |
| 15 | Protocol Guild | Visibility | Low | N/A | Pledge when revenue exists |
| 16 | Alchemy Growth | Credits | Low | HIGH | Apply via form |
| 17 | Thirdweb Startup | Credits | Low | HIGH | Apply via form |
| 18 | CoW DAO Grants | $5k–$25k | Medium | MEDIUM | Apply via forum |
| 19 | Aerodrome/Velodrome | Token incentives | Low | LOW | Discord outreach |

---

## IMMEDIATE ACTION ITEMS

### Week 1 (Now):
1. **Base Builder Grants** — Submit full application (highest priority)
2. **Gitcoin Grants** — Create project profile, prepare for next round
3. **Alchemy Growth** — Apply for infrastructure credits (quick win)
4. **LayerZero** — Send outreach email to partnerships@layerzero.network
5. **Hyperliquid** — Post in Discord builder channel

### Week 2:
6. **Lido LEGO** — Submit wstETH integration grant
7. **Chainlink BUILD** — Submit application
8. **Questbook** — Submit to active DeFi rounds
9. **CoW DAO** — Post grant proposal on forum

### Week 3–4:
10. **Arbitrum Foundation** — Prepare and submit LTIPP application
11. **Optimism RetroPGF** — Prepare application for next round
12. **Ethereum Foundation ESP** — Submit application
13. **Uniswap Foundation** — Submit application

---

## UNIVERSAL GRANT APPLICATION ASSETS

### One-Liner:
```
Kerne Protocol is delta-neutral yield infrastructure that enables users to earn stable, market-agnostic yield from funding rates and LST staking with zero directional risk.
```

### 100-Word Description:
```
Kerne Protocol is delta-neutral yield infrastructure built on Base and Arbitrum. Users deposit ETH into noncustodial ERC-4626 vaults. The autonomous hedging engine opens matching short positions on Hyperliquid perpetual futures, neutralizing all price exposure. Users earn yield from two uncorrelated streams: perpetual funding rate payments and liquid staking token rewards. The protocol features real-time solvency verification, automated circuit breakers, cross-chain expansion via LayerZero V2, and a Zero-Fee Intent Network (ZIN) for gasless execution. 35+ verified smart contracts, 150+ Foundry tests, and 8 Docker services running 24/7.
```

### Key Metrics:
```
- Contracts: 35+ deployed and verified (Base + Arbitrum)
- Tests: 150+ Foundry tests (unit, integration, fuzzing, invariant)
- Infrastructure: 8 Docker services on cloud (24/7 operation)
- Chains: Base (primary), Arbitrum, Optimism (pending)
- Standards: ERC-4626, LayerZero V2 OFT, Chainlink price feeds
- Status: Live basis trade generating real yield
```

### Team Description:
```
Two core contributors building full-time since January 2026. Deep expertise in Solidity (0.8.24, Foundry), Python (hedging engine, MEV), TypeScript (Next.js frontend, SDK), and DeFi mechanism design. Background in quantitative finance and systems engineering.
```

### Budget Template (Adapt per program):
```
Total Request: $50,000

Breakdown:
- External Security Audit: $30,000 (60%)
  Top-tier firm (Cyfrin, Sherlock, or Code4rena community audit)
- Liquidity Bootstrapping: $10,000 (20%)
  Seed vault TVL on [CHAIN] to demonstrate mechanism at scale
- Operational Infrastructure: $5,000 (10%)
  Cloud hosting (DigitalOcean), domains, RPC endpoints, monitoring for 6 months
- User Acquisition & Incentives: $5,000 (10%)
  Deposit incentives, gas subsidies, and community rewards for [CHAIN]-native users
```

### Logo & Visual Assets:
```
- Square Logo (512x512 PNG): frontend/public/kerne-logo-512.png
- Square Logo (441x441 PNG): frontend/public/kerne-logo-square.png
- Banner: Available at kerne.ai
```

### Contract Addresses (Copy-Paste Ready):

**Base Mainnet:**
```
KerneVault (ERC-4626): 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
ZIN Pool: 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7
ZIN Executor: 0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995
KERNE Token: 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340
kUSD OFT V2: 0x257579db2702BAeeBFAC5c19d354f2FF39831299
KERNE OFT V2: 0x4E1ce62F571893eCfD7062937781A766ff64F14e
KerneTreasury: 0xB656440287f8A1112558D3df915b23326e9b89ec
InsuranceFund: 0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9
```

**Arbitrum One:**
```
KerneVault: 0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
ZIN Executor: 0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb
ZIN Pool: 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD
kUSD OFT V2: 0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222
KERNE OFT V2: 0x087365f83caF2E2504c399330F5D15f62Ae7dAC3
```

### Links (Copy-Paste Ready):
```
Website: https://kerne.ai
Documentation: https://docs.kerne.ai
Twitter: https://twitter.com/KerneProtocol
GitHub (Ecosystem PR): https://github.com/base/web/pull/2956
Base Vault (BaseScan): https://basescan.org/address/0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
Arbitrum Vault (Arbiscan): https://arbiscan.io/address/0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
Contact: kerne.systems@protonmail.com
```

---

## TRACKING TABLE

| # | Program | Date Applied | Status | Grant Amount | Notes |
|---|---------|-------------|--------|-------------|-------|
| 1 | Base Builder Grants | | NOT STARTED | | |
| 2 | Optimism RetroPGF | | NOT STARTED | | |
| 3 | Arbitrum LTIPP/STIP | | NOT STARTED | | |
| 4 | LayerZero Ecosystem | | NOT STARTED | | |
| 5 | Hyperliquid Builder | | NOT STARTED | | |
| 6 | Gitcoin Grants | | NOT STARTED | | |
| 7 | Questbook DeFi | | NOT STARTED | | |
| 8 | Chainlink BUILD | | NOT STARTED | | |
| 9 | Ethereum Foundation ESP | | NOT STARTED | | |
| 10 | Uniswap Foundation | | NOT STARTED | | |
| 11 | Aave Grants DAO | | NOT STARTED | | |
| 12 | Safe Ecosystem | | NOT STARTED | | |
| 13 | Lido LEGO | | NOT STARTED | | |
| 14 | Compound Grants | | NOT STARTED | | |
| 15 | Protocol Guild | | NOT STARTED | | |
| 16 | Alchemy Growth | | NOT STARTED | | |
| 17 | Thirdweb Startup | | NOT STARTED | | |
| 18 | CoW DAO Grants | | NOT STARTED | | |
| 19 | Aerodrome/Velodrome | | NOT STARTED | | |

---

## AGGREGATE POTENTIAL

**If all 19 programs approve (best case):**
- Cash/Token Grants: $200,000 – $1,500,000+
- Infrastructure Credits: $5,000 – $20,000/year
- Co-marketing & Visibility: Priceless

**Realistic scenario (30% approval rate on top 10):**
- 3 grants approved averaging $30,000 each = $90,000
- This covers: 1 external audit + 6 months operational runway + liquidity seeding

**Minimum viable outcome (1 grant approved):**
- Base Builder Grant at $25,000 = covers external audit
- This single outcome transforms the protocol's credibility trajectory

---

*Document created: 2026-02-08*
*Awaiting authorization to begin Week 1 submissions*
