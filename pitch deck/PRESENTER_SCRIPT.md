# Kerne Protocol — Seed Round Presenter Script

> Speaker notes for each slide. Read naturally, not verbatim. Adapt to the audience.

---

## Slide 1 — Title

"Hey everyone, thanks for taking the time to join us. I'm [NAME], founder of Kerne.

So essentially, We're building the omnichain yield-bearing stablecoin. The simplest way to think about it: you deposit capital, and kUSD — our stablecoin — which earns optimized yield automatically. No active management, no chasing farms, no bridging between chains.

We're raising $3 to $8 million at a $40 to $100 million fully diluted valuation. Let me walk you through why this is the single biggest opportunity in DeFi right now."

---

## Slide 2 — The Problem

"There's over $170 billion sitting in stablecoins today. USDC, USDT — and the holders of those tokens earn absolutely nothing. Meanwhile, Circle and Tether are generating over $5 billion a year in Treasury yield from that capital. The users subsidize the issuers.

Now, there are alternatives — but they're all structurally flawed.

Ethena is 100% dependent on a single strategy: the basis trade. When funding rates flip negative — and they do — yield goes to zero or worse. And it's all custodied through centralized entities like Copper and Ceffu. You can't see where the money is, you can't verify the positions, you can't audit the risk in real time. It's completely opaque.

MakerDAO's sDAI is capped at whatever Maker's own lending revenue generates — 3 to 8%. There's a hard ceiling. They can't access external DeFi yield.

And manual farming? That's a full-time job. Dozens of protocols, multiple chains, constant rebalancing, gas costs. It doesn't scale.

The market is screaming for a better solution."

---

## Slide 3 — The Solution

"That solution is kUSD.

Here's how it works: you deposit yield-bearing collateral — stETH, eETH, rETH, sDAI — and mint kUSD at 150% collateralization. Our Yield Routing Engine then autonomously routes that collateral across the highest-yielding strategies in DeFi. kUSD rebases daily, so your balance grows just by holding it.

The target range is 12 to 20% APY — and that's net of fees.

For users, it's dead simple. Deposit, hold kUSD, earn yield. Use it anywhere — Aave, Curve, GMX, payments. We also have a wkUSD wrapper for tax-optimized composability.

For the protocol, we capture value through performance fees on yield — 10 to 20% — plus minting fees, PSM swap fees, and liquidation penalties. Multiple revenue streams, all scaling with TVL."

---

## Slide 4 — Market Opportunity

"Let me frame the opportunity.

We're attacking three of the deepest capital pools in DeFi simultaneously. $170 billion in stablecoins. $80 billion in yield protocols. $10 billion in monthly cross-chain volume.

And here's the key insight: yield-bearing stablecoins currently have less than 6% penetration of the total stablecoin market. Our thesis is that this reaches 30 to 50% within three years. That's $50 to $85 billion.

If Kerne captures just 3 to 5% of that, we're looking at $2.5 to $7.5 billion in TVL. And because of the reflexive flywheel — where growth in one pool compounds the others — the actual trajectory could be much steeper."

---

## Slide 5 — Architecture

"The architecture is a four-layer stack. Each layer is independent but composable.

Layer 1 is the Vault Layer — isolated ERC-4626 vaults per collateral type. stETH vault, eETH vault, rETH vault — each with independent risk parameters. If one collateral type has issues, it doesn't cascade.

Layer 2 is the Yield Routing Engine — this is our core IP. It autonomously optimizes yield across 200+ strategies on 7+ chains. Risk-scored allocation with real-time rebalancing.

Layer 3 is kUSD stability — overcollateralized minting, a Peg Stability Module for 1:1 USDC swaps, protocol-owned liquidity, and a reserve fund backstop.

Layer 4 is KERNE token value capture — 50% of revenue goes to buy-and-burn, 30% to stakers, 20% to treasury. Fixed 1 billion supply, permanently deflationary.

This isn't a single-product protocol. It's a full-stack DeFi primitive."

---

## Slide 6 — Core Technology

"The Yield Routing Engine is the moat.

It has three components. First, a Strategy Registry — modular adapters for every yield source in DeFi. Aave, Compound, Morpho, Pendle, Curve, EigenLayer AVS, RWA vaults. We're targeting 30 to 50 at launch, scaling to over 1,000 within a year.

Second, a Risk Scoring Oracle — every strategy gets a real-time 0 to 100 risk score. We factor in audit status, TVL stability, exploit history, oracle dependency, concentration risk.

Third, an Allocation Optimizer — constrained optimization that maximizes yield subject to risk caps, liquidity reserves, cross-chain limits, and gas efficiency. Everything is on-chain and transparent.

And here's the compounding advantage: every day the YRE operates, it accumulates performance data. A competitor launching six months after us starts with zero data and zero track record. The knowledge gap only widens."

---

## Slide 7 — Competitive Landscape

"Let me show you the competitive landscape.

Every major competitor has a structural weakness. Single-strategy protocols are exposed when funding rates go negative. Others have yield ceilings, excessive complexity, or no yield at all.

Kerne is the only protocol that combines 200+ yield strategies, native multi-chain deployment on 7+ chains, and full on-chain transparency. Yes, we're a new protocol — that's the risk. But the architecture is designed to be structurally superior from day one."

---

## Slide 8 — Why Kerne Wins

"Three structural differentiators.

First, yield diversification. We're not dependent on any single strategy. We route across hundreds of sources. When one underperforms, the YRE shifts to lending, restaking, LP positions, and RWAs. The system is always adapting.

Second, omnichain native. kUSD is natively available on 7+ chains via LayerZero V2 OFT. Users don't need to bridge. They mint and use kUSD wherever they are.

Third, radical transparency. Every allocation, every yield source, every rebalance — recorded on-chain. Real-time dashboards. When someone asks 'where does the yield come from?' — we can answer that completely and verifiably. That's a massive trust advantage, especially for institutional capital."

---

## Slide 9 — Traction

"We built this in six weeks. It's live on mainnet.

KerneVault is deployed on Base, Arbitrum, and Optimism. Our delta-neutral basis trade is running on Hyperliquid — backtested at 20.3% APY over 18 months of real Binance data, with a Sharpe ratio of 33.46 and max drawdown of 0.15%.

kUSD, the PSM, Insurance Fund, and Treasury are all deployed. We have the ZIN — Zero-Fee Intent Network — live on Base and Arbitrum. LayerZero V2 OFT bridging across three chains. 154 passing Foundry tests. A completed penetration test. Frontend live at kerne.ai. Documentation. An SDK with 24 tests.

Over 20 smart contracts deployed. This isn't a whitepaper — it's working infrastructure."

---

## Slide 10 — Go-to-Market

"Our go-to-market is a seven-channel growth engine.

Pre-deposit points campaign — Blast-style escrow with referral multipliers. We're targeting $50 million+ committed before mainnet launch.

Tiered liquidity mining — 1.5x to 3x multipliers for 30 to 180 day deposits. 15% of token supply allocated over four years.

Protocol integrations — kUSD listed on Aave, Curve, Pendle, GMX. Each integration comes with co-marketing.

Ecosystem grants — we pay protocols to integrate. A $500K Aave grant can drive millions in TVL.

Content — 3 to 5 tweets daily, 2 to 3 threads weekly, weekly Twitter Spaces, Dune dashboards.

Ambassador program — 50 to 200 community members for content, moderation, and translation.

And targeted airdrops — we snapshot competing stablecoin and LST holders and offer migration incentives. We're fishing in the exact right pond."

---

## Slide 11 — Tokenomics

"KERNE token. 1 billion fixed supply. Never increases.

The allocation: 18% to the core team with standard vesting. 15% to early investors. 20% to liquidity mining over four years. 10% to ecosystem grants. 5% to airdrops. 20% to the protocol treasury. 12% to the DAO governance reserve.

Value accrual runs through three channels. 50% of all protocol revenue buys KERNE on the open market and burns it permanently. This creates deflationary pressure that scales directly with TVL. 30% goes to KERNE stakers as real yield — not inflationary emissions. And 20% goes to the treasury for protocol-owned liquidity, strategic operations, and reserves.

The key insight: as TVL grows, revenue grows, burn rate increases, supply decreases, and token value compounds. It's a reflexive loop."

---

## Slide 12 — Revenue Model

"Revenue scales linearly with TVL.

At $1 billion TVL, we generate approximately $25 million in annual revenue. At $3 billion, $75 million. At $5 billion, $125 million. At $10 billion, $250 million.

The primary revenue source is a 10 to 20% performance fee on all yield generated. Plus minting and redemption fees, PSM swap fees, and liquidation penalties. At a blended 2.5% fee rate on TVL, the math is straightforward.

These aren't speculative numbers. They're based on the same fee structures that Lido, Maker, and other top protocols use today."

---

## Slide 13 — Roadmap

"The roadmap to $1 billion+ TVL.

Q1 2026 — where we are now. Core contracts deployed. Basis trade live. Seed round. First audit engagement. Pre-deposit campaign launch.

Q2 2026 — mainnet launch. kUSD minting goes live. PSM activated. Liquidity mining begins. First integrations with Aave, Curve, and Pendle.

Q3 2026 — multi-chain expansion. 5 to 7 chains live. 50+ YRE strategies. Token generation event. CEX listings. $500 million+ TVL target.

Q4 2026 — escape velocity. Governance transition. RWA collateral. V2 of the YRE with ML optimization. $1 billion+ TVL. Category dominance.

For precedent: Ethena reached $3.6 billion TVL in about five months. Blast reached $2 billion+ in three months pre-launch. With superior architecture and the same execution intensity, $1 billion within 12 months is very achievable."

---

## Slide 14 — Team

"The team.

I handle strategy, architecture, and protocol design. I've spent years deep in DeFi — understanding how yield works across dozens of protocols and chains. I designed the four-layer architecture and the go-to-market from first principles.

My co-founder owns the product end-to-end — frontend, branding, terminal dashboard, user experience. The reason Kerne looks and feels different from every other DeFi protocol is because of him.

The output speaks for itself: 20+ smart contracts across three chains, a full frontend, an SDK, a hedging bot, and a completed penetration test — all shipped in six weeks. That's the execution speed we operate at.

We're scaling aggressively with seed capital: Senior Solidity Engineer, Full-Stack Developer, Growth Lead, Security Engineer, and BD Lead. Target is 8 to 12 people by month nine."

---

## Slide 15 — The Ask

"We're raising $3 to $8 million at a $40 to $100 million fully diluted valuation.

The instrument is a SAFT — Simple Agreement for Future Tokens. 8 to 10% of total supply allocated to seed investors. Two-year vesting with a six-month cliff. We're targeting a Q1 2026 close and seeking a $1 to $3 million lead check.

Use of funds: 35% to engineering — salaries and contractors. 20% to security — audits, bug bounties, and insurance. 20% to growth — incentives, protocol-owned liquidity, and marketing. 15% to operations — legal, infrastructure, and travel. 10% held as a reserve buffer.

Why now? The post-halving bull market is accelerating. The yield-bearing stablecoin meta is proven but there's no dominant winner yet. The infrastructure is mature. The regulatory window is open. Every week of delay means TVL lost to competitors and one step closer to the cycle peak.

This is the window. We're ready to execute."

---

## Slide 16 — Thank You

"That's Kerne. The omnichain yield-bearing stablecoin, built for the next $100 billion in DeFi capital.

I'd love to dive deeper into any section — the architecture, the YRE, the competitive dynamics, the tokenomics. What questions do you have?"

---

## General Tips

- **Pace:** ~2 minutes per slide = ~32 minutes total. Leave 15-20 minutes for Q&A.
- **Energy:** Start strong on slides 1-3 (hook them), maintain through 4-8 (build conviction), accelerate on 9-12 (show momentum), close hard on 14-15 (create urgency).
- **Objection handling:** The #1 objection will be "you're a new protocol with no TVL." Counter: "Ethena had zero TVL 6 months before hitting $3.6B. The infrastructure is built. We need capital to ignite the flywheel."
- **Key phrases to emphasize:** "live on mainnet," "20.3% APY backtest," "154 passing tests," "full on-chain transparency," "every week of delay."