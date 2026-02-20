// Created: 2026-02-16

# Witek Radomski Strategic Meeting Notes
**Date:** February 16, 2026
**Duration:** 3 hours
**Attendee:** Witek Radomski (Polymarket co-founder)

---

## Executive Summary

Meeting with Witek Radomski yielded 9 critical strategic insights that significantly impact Kerne's go-to-market strategy, risk communication, and positioning. These recommendations span technical architecture, market positioning, and founder credibility.

---

## Key Strategic Recommendations

### 1. Monte Carlo Risk Simulation (10,000 Scenarios)
**Insight:** Use projection models to simulate 10,000 future scenarios demonstrating Kerne fails only X% of the time.

**Strategic Value:**
- Transforms abstract risk into quantifiable, communicable metrics
- Institutional investors need probabilistic failure analysis
- Differentiates Kerne from protocols that can't articulate risk profile
- Creates powerful marketing: "Kerne has a 99.2% survival probability across all simulated market conditions"

**Action Items:**
- [ ] Build Monte Carlo simulation framework
- [ ] Model key risk variables: collateral depeg, yield compression, liquidation cascades, smart contract failures
- [ ] Generate probability distributions for protocol solvency
- [ ] Create public-facing dashboard showing simulation results
- [ ] Include in investor pitch deck and whitepaper

---

### 2. Philanthropy Initiative for Network Access
**Insight:** Establish a philanthropic cause to create opportunities for interacting with wealthy individuals.

**Strategic Value:**
- High-net-worth individuals are often philanthropically inclined
- Shared causes create authentic relationship-building opportunities
- Positions Kerne founders as values-driven, not just profit-driven
- Opens doors to family offices, institutional capital, and strategic partnerships

**Potential Directions:**
- Financial literacy / DeFi education for underbanked populations
- Crypto-based disaster relief fund
- Blockchain infrastructure for charitable transparency
- Scholarships for blockchain developers from underrepresented regions

**Action Items:**
- [ ] Research philanthropic angles aligned with Kerne's mission
- [ ] Evaluate "Kerne Foundation" structure for philanthropic activities
- [ ] Identify high-impact philanthropic events/communities
- [ ] Draft philanthropy mission statement

---

### 3. Code Simplicity as Security
**Insight:** Make Kerne's code as simple as possible to avoid exploits.

**Strategic Value:**
- Complexity is the enemy of security
- Simpler code = smaller attack surface
- Easier audits, faster reviews, fewer bugs
- More contributors can understand and verify the codebase
- Marketing angle: "Kerne's vault logic is 500 lines. Competitor X is 5,000."

**Implementation Principles:**
- Minimal contract surface area
- Clear, linear logic flows
- Avoid complex inheritance chains
- Prefer battle-tested patterns over novel constructions
- Each contract should do ONE thing well

**Action Items:**
- [ ] Audit existing contracts for unnecessary complexity
- [ ] Establish code simplicity guidelines in engineering standards
- [ ] Track lines of code as a negative metric (fewer = better)
- [ ] Document architectural decisions favoring simplicity

---

### 4. Founder Knowledge Depth for Credibility
**Insight:** Scofield must know every aspect of Kerne to appear credible when speaking with people as the founder.

**Strategic Value:**
- Investors, partners, and users test founder knowledge
- Surface-level understanding destroys credibility instantly
- Deep knowledge enables confident, precise communication
- Allows real-time adaptation in conversations

**Knowledge Domains to Master:**
- **Technical:** Every contract, every function, every parameter
- **Economic:** Tokenomics, yield mechanics, fee structures, incentive curves
- **Competitive:** Every competitor's architecture, strengths, and weaknesses
- **Market:** TAM, SAM, SOM, growth trajectories, market cycles
- **Risk:** Every failure mode, every mitigation, every historical precedent
- **Regulatory:** Jurisdictional landscape, compliance strategies, legal structure

**Action Items:**
- [ ] Create "Founder Knowledge Base" document
- [ ] Schedule weekly deep-dive sessions on each domain
- [ ] Practice explaining complex concepts in simple terms
- [ ] Prepare Q&A flashcards for common investor questions

---

### 5. Comprehensive Spec Document
**Insight:** Create a formal specification document for Kerne.

**Strategic Value:**
- Single source of truth for all stakeholders
- Required reading for new team members, auditors, investors
- Forces rigorous thinking through all edge cases
- Demonstrates professionalism and completeness

**Spec Document Structure:**
1. Protocol Overview
2. Architecture Specification
3. Smart Contract Specifications
4. Economic Parameters
5. Risk Framework
6. Security Model
7. Governance Structure
8. Integration Guidelines
9. Operational Procedures

**Action Items:**
- [ ] Create KERNE_SPEC.md master document
- [ ] Document all contract interfaces
- [ ] Specify all parameters with rationale
- [ ] Include sequence diagrams for key flows
- [ ] Add to public documentation

---

### 6. Canada Stablecoin Market Positioning
**Insight:** Position Kerne to become Canada's predominant/ideal stablecoin, as there's a significant gap in the market.

**Strategic Value:**
- Canada lacks a homegrown stablecoin champion
- Regulatory environment is relatively clear (vs. US uncertainty)
- First-mover advantage in a G7 economy
- Canadian banks and institutions need non-US alternatives
- CAD-pegged variant could capture significant market

**Market Analysis:**
- No major Canadian stablecoin exists
- USDC/USDT dominate but are US-centric
- Canadian institutions may prefer non-US jurisdiction
- CAD-denominated kUSD variant could be unique

**Action Items:**
- [ ] Research Canadian regulatory requirements for stablecoins
- [ ] Evaluate CAD-pegged kUSD variant (kCAD)
- [ ] Identify Canadian institutional partners
- [ ] Engage Canadian crypto associations
- [ ] Explore Canadian bank partnerships

---

### 7. Multi-Token and Multi-Chain Support
**Insight:** Support more tokens and chains so users can deposit easier into Kerne.

**Strategic Value:**
- Reduces friction for user onboarding
- Meets users where they already hold assets
- Expands addressable market
- Reduces bridge/swap costs for depositors

**Priority Expansions:**
- **Tokens:** WBTC, tBTC, sBTC, weETH, rsETH, pufETH, ezETH, USDT, DAI, FRAX
- **Chains:** Solana, Sui, Aptos (non-EVM); Polygon, zkSync, Scroll, Linea (EVM L2s)

**Action Items:**
- [ ] Prioritize token/chain additions by user demand
- [ ] Build chain abstraction layer for deposits
- [ ] Create cross-chain deposit infrastructure
- [ ] Partner with bridges for seamless onboarding

---

### 8. SAT Street Toronto Connection
**Insight:** SAT Street Toronto is a potential funding source or entry point for opportunities.

**Strategic Value:**
- Toronto-based crypto/finance network
- Access to Canadian capital and institutional connections
- Potential strategic investor or partner
- Gateway to Canadian financial ecosystem

**Background:**
- SAT Street is a Toronto-based organization with crypto/finance focus
- Could provide introductions to Canadian VCs, family offices, institutions
- May have regulatory insights for Canadian market entry

**Action Items:**
- [ ] Research SAT Street Toronto thoroughly
- [ ] Identify key contacts and decision-makers
- [ ] Prepare tailored outreach strategy
- [ ] Explore partnership/investment opportunities

---

### 9. USD Depreciation as Core Selling Point
**Insight:** The US dollar is depreciating ~9% globally compared to other currencies. USDC, while stable to dollars, devalues in real terms. This is the "idle stablecoin conundrum" - a massive selling point.

**Strategic Value:**
- Frames the problem in terms users intuitively understand
- Creates urgency: holding USDC = losing 9% annually vs. global purchasing power
- Positions kUSD as the solution to a real, measurable problem
- Appeals to international users who feel USD depreciation acutely

**The Idle Stablecoin Conundrum:**
```
User holds $100,000 USDC for one year:
- USDC maintains $1.00 peg ✓
- USD depreciates 9% vs. basket of currencies
- Real purchasing power: $91,000
- User lost $9,000 by "holding stable"

With kUSD:
- kUSD maintains $1.00 peg ✓
- kUSD earns 10% APY
- Real purchasing power: $100,000 + yield offset
- User preserved wealth by holding yield-bearing stable
```

**Marketing Framing:**
- "USDC is stable to dollars. Dollars aren't stable to the world."
- "The stablecoin that actually stays stable."
- "Your USDC loses 9% annually. kUSD earns 10%+. The math is simple."

**Action Items:**
- [ ] Create "Idle Stablecoin Conundrum" whitepaper section
- [ ] Build USD depreciation tracker dashboard
- [ ] Develop marketing campaign around this insight
- [ ] Include in all investor pitch materials
- [ ] Create comparison calculator (USDC vs kUSD over time)

---

## Immediate Priorities (Next 7 Days)

1. **Spec Document** - Create comprehensive KERNE_SPEC.md
2. **Monte Carlo Framework** - Begin simulation model design
3. **USD Depreciation Campaign** - Draft marketing materials
4. **Founder Knowledge Base** - Begin systematic documentation
5. **SAT Street Research** - Identify and approach contacts

---

## Long-Term Strategic Implications

This meeting fundamentally shifts Kerne's positioning:
- From "yield-bearing stablecoin" to "solution to the idle stablecoin conundrum"
- From "DeFi protocol" to "Canada's stablecoin champion"
- From "complex yield routing" to "simple, secure, transparent"
- From "another crypto project" to "philanthropically-connected institution"

The Canada angle is particularly significant - it provides a clear geographic market to dominate before expanding globally, with regulatory clarity that the US lacks.

---

## Follow-Up Required

- [ ] Schedule follow-up meeting with Witek
- [ ] Send progress update on action items
- [ ] Explore Witek's network for Canadian connections
- [ ] Request introductions to SAT Street contacts if available

---

*Document created: 2026-02-16*
*Last updated: 2026-02-16*