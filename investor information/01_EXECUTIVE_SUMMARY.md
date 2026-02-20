# KERNE PROTOCOL — Executive Summary
### The Omnichain Yield-Bearing Stablecoin | Seed Round — February 2026

---

## The Opportunity

$170B+ sits in stablecoins earning zero yield. Circle and Tether collect $5B+/year in Treasury income from *your* capital — and pass nothing back. Yield-bearing stablecoins (Ethena's USDe, Maker's sDAI) have proven ravenous demand, but every existing solution has a fatal flaw: single-strategy dependence, yield ceilings, or centralized custody risk.

**Kerne Protocol** is building **kUSD** — a yield-bearing stablecoin that automatically earns optimized, diversified yield through an autonomous **Yield Routing Engine (YRE)** that allocates collateral across hundreds of DeFi strategies on 7+ chains simultaneously.

---

## How It Works

1. **Deposit** yield-bearing collateral (stETH, eETH, rETH, sDAI) into Kerne vaults
2. **Mint** kUSD at 150% collateral ratio — overcollateralized, not algorithmic
3. **YRE routes** underlying yield across 200+ strategies (lending, restaking, LPs, RWAs)
4. **kUSD rebases daily** — holders earn yield just by holding kUSD in their wallet

---

## Why Kerne Wins

| | Kerne (kUSD) | Ethena (USDe) | MakerDAO (sDAI) |
|---|---|---|---|
| **Yield Source** | 200+ diversified strategies | Single basis trade | Own lending only |
| **Validated APY** | **21.78%** (Monte Carlo verified) | 0-35% (volatile) | 3-8% |
| **Multi-Chain** | 7+ chains native | Limited | Ethereum only |
| **Transparency** | Full on-chain | Opaque CeFi custody | On-chain |
| **Bear Market** | RWA yield floor (3-5%) | Can go negative | Yield compresses |

**Core moat:** The YRE accumulates data and strategy optimizations daily. A competitor launching 6 months later starts with zero data, zero adapters, and zero track record.

---

## Validated Performance (Monte Carlo v4 Simulation)

Our architecture has been stress-tested through 10,000 independent simulations spanning a full 365-day horizon:

| Metric | Value |
|---|---|
| **Survival Rate** | **99.73%** (target >99% achieved) |
| **Mean APY** | **21.78%** |
| **Mean Final TVL** | $106.9M (from $100M start) |
| **VaR 99% Floor** | $86.77M (86.77 cents preserved in worst 1% scenarios) |
| **Oracle Manipulation Failures** | **0** (triple-source defense eliminated this vector) |
| **Max Drawdown** | 2.62% |

**9-Layer Protection Architecture:**
1. Triple-Source Oracle (Chainlink + TWAP + Pyth)
2. Oracle Deviation Guard (5% max threshold)
3. TWAP Window Hardening (30-minute window)
4. Tiered Circuit Breaker (Yellow/Red alerts)
5. Dynamic Collateral Ratio Buffer
6. Gradual Liquidation Cap (5% TVL/hour)
7. Protocol Insurance Fund ($3M reserve)
8. Post-Audit Exploit Reduction (73% lower probability)
9. Delta-Neutral Core Architecture

*Full methodology and results: See Monte Carlo v4 Risk Report*

---

## Traction (6 Weeks)

- **Live on mainnet:** KerneVault (ERC-4626) deployed on Base, Arbitrum, Optimism
- **Delta-neutral basis trade** running on Hyperliquid — **21.78% APY validated** through Monte Carlo simulation (Sharpe 33.46)
- **20+ smart contracts** deployed and verified: Vault, kUSD, PSM, Insurance Fund, Treasury, OFT bridges, ZIN intent network
- **154 passing tests**, multiple penetration test rounds remediated
- **Full product:** Frontend (kerne.ai), documentation, TypeScript SDK (24 tests), hedging bot on DigitalOcean
- **LayerZero V2 OFT** bridging wired across 3 chains

---

## Market Size

- **Total stablecoin market:** $170B+ and growing
- **Yield-bearing stablecoins:** <$10B today, projected $50-85B within 3 years (30-50% penetration)
- **Capturing 3-5%** of total stablecoin market = $5-8.5B TVL = $125-210M annual revenue

---

## Revenue Model

Protocol revenue from 4 streams: performance fee on yield (10-20%), minting/redemption fees, PSM swap fees, liquidation penalties. At $1B TVL → $25M annual revenue. At $5B TVL → $125M.

**KERNE token** (1B fixed supply, no inflation): 50% of revenue → buy-and-burn, 30% → staking distribution, 20% → treasury.

---

## The Ask

- **Raising:** $3-8M seed round
- **Valuation:** $40-100M FDV
- **Instrument:** SAFT (Simple Agreement for Future Tokens)
- **Allocation:** 8-10% of total token supply
- **Vesting:** 2-year vest, 6-month cliff
- **Use of funds:** 35% engineering, 20% security (audits), 20% growth, 15% operations, 10% reserve

---

## Why Now

- **Post-halving bull market** accelerating — peak expected Q4 2025 - Q2 2026
- **Fed rate cuts** making DeFi yields relatively more attractive vs. TradFi
- **Yield-bearing stablecoin meta** proven but no dominant winner yet
- **Infrastructure mature:** LayerZero V2, CCTP, EigenLayer, L2s all production-ready
- **Every week of delay** = TVL lost to competitors filling the gap

---

## Team

Three-person founding team that shipped 20+ contracts across 3 chains, a full frontend, SDK, hedging bot, and security suite in 6 weeks. Scaling to 8-12 with seed capital (Senior Solidity Engineer, Security Engineer, Growth Lead, BD Lead).

---

## Key Documents

| Document | Description |
|---|---|
| **Monte Carlo v4 Risk Report** | 10,000 simulation stress test validating 99.73% survival rate |
| **Seed Investor Targets** | 29 curated investors across 4 tiers |
| **Outreach Templates** | Ready-to-send DM templates for investor outreach |

---

**Contact:** kerne.systems@protonmail.com | kerne.ai | @KerneProtocol