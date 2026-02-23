// Created: 2026-02-09
# Base Builder Grant — SUBMISSION EXECUTION GUIDE

## STATUS: READY TO SUBMIT

---

## STEP 1: Find the Application Portal

Base's grant program has multiple entry points. Execute in this order until you find an active application form:

### Option A: Base Builds (Primary)
1. Go to: **https://base.org/ecosystem** → look for "Grants" or "Builder Grants" link
2. Or try: **https://paragraph.xyz/@grants.base.eth** (Base Grants blog — check for latest round announcements and application links)

### Option B: Base Discord
1. Join Base Discord: **https://discord.gg/buildonbase**
2. There is NO dedicated #grants channel — instead, search for "grant" in the server search bar
3. Check **#announcements** and **#general** for any grant round announcements
4. Ask in **#general** or **#dev-support** if there's an active grant application link
5. DM a Base team member or moderator if needed

### Option C: Direct Email
1. Email: **builders@base.org**
2. Subject: `Builder Grant Application — Kerne Protocol (DeFi Infrastructure)`
3. Use the email body from Section 3 below

### Option D: Base Governance Forum
1. Go to: **https://gov.base.org** or **https://forum.base.org**
2. Look for active grant proposals or application threads

---

## STEP 2: Account Setup

If the portal requires an account:
- **Email:** kerne.systems@protonmail.com
- **Wallet:** 0x57D400cED462a01Ed51a5De038F204Df49690A99 (deployer)
- **GitHub:** https://github.com/kerne-protocol

---

## STEP 3: Application Content (Copy-Paste Ready)

### Project Name
```
Kerne Protocol
```

### One-Liner
```
Delta-neutral yield infrastructure built natively on Base — ERC-4626 vaults that earn stable yield from funding rates and LST staking with zero directional risk.
```

### Category
```
DeFi Infrastructure / Yield
```

### Website
```
https://kerne.ai
```

### Documentation
```
https://docs.kerne.ai
```

### Twitter
```
https://twitter.com/KerneProtocol
```

### Contact Email
```
kerne.systems@protonmail.com
```

### Team Size
```
2 core contributors
```

### Project Description (Short — under 300 chars)
```
Kerne is delta-neutral yield infrastructure on Base. Users deposit ETH into ERC-4626 vaults. An autonomous hedging engine opens matching short positions on Hyperliquid, neutralizing price exposure. Users earn yield from funding rates plus staking rewards.
```

### Project Description (Full)
```
Kerne Protocol is delta-neutral yield infrastructure built natively on Base. The protocol enables users to earn stable, market-agnostic yield by combining two uncorrelated revenue streams: liquid staking token rewards and perpetual futures funding rate capture via Hyperliquid.

How It Works:
1. Users deposit ETH into noncustodial ERC-4626 vaults on Base
2. The autonomous hedging engine opens equal-sized short positions on Hyperliquid perpetual futures, neutralizing all ETH price exposure
3. Users earn yield from funding rates plus staking rewards, reflected as vault share appreciation

What We've Built:
- KerneVault (ERC-4626) deployed and verified on Base mainnet
- 35+ smart contracts across Base and Arbitrum, all verified on BaseScan/Arbiscan
- 150+ Foundry tests (unit, integration, fuzzing, invariant testing)
- Autonomous hedging engine running 24/7 on cloud infrastructure (8 Docker services)
- Live basis trade generating real yield from Hyperliquid funding rates
- ZIN (Zero-Fee Intent Network) for intent-based liquidity aggregation on Base
- Cross-chain kUSD and KERNE tokens via LayerZero V2 OFT (Base + Arbitrum + Optimism)
- Full documentation site, transparency dashboard, and terminal interface

Key Features:
- Delta-Neutral Architecture: Zero directional market risk
- ERC-4626 Standard: Composable with the entire Base DeFi ecosystem
- Real-Time Solvency Verification: Block-by-block proof of reserves
- Automated Circuit Breakers: Sub-second risk management and depeg protection
- Insurance Fund: Protocol revenue allocation for tail risk coverage
- 7-Day Withdrawal Queue: Managed liquidity for institutional-grade operations
```

### Smart Contract Addresses
```
Base Mainnet:
- KerneVault (ERC-4626): 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
- ZIN Pool: 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7
- ZIN Executor: 0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995
- KERNE Token: 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340
- kUSD OFT V2: 0x257579db2702BAeeBFAC5c19d354f2FF39831299
- KERNE OFT V2: 0x4E1ce62F571893eCfD7062937781A766ff64F14e
- KerneTreasury: 0xB656440287f8A1112558D3df915b23326e9b89ec
- InsuranceFund: 0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9

Arbitrum One:
- KerneVault: 0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
- ZIN Executor: 0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb
- ZIN Pool: 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD

All contracts verified on BaseScan and Arbiscan.
```

### How does this benefit the Base ecosystem?
```
Kerne benefits Base in four ways:

1. Sticky TVL: Delta-neutral vaults attract capital that stays long-term because depositors earn yield regardless of market direction. Unlike directional protocols where users leave during downturns, Kerne's TVL is market-agnostic.

2. Composability: Our ERC-4626 vaults are composable with every protocol on Base. Other Base DeFi protocols can integrate Kerne vault shares as collateral, yield sources, or building blocks — expanding the Base DeFi ecosystem.

3. Cross-Chain Liquidity Inflow: Our LayerZero V2 bridges bring capital FROM Arbitrum and Optimism TO Base. Every cross-chain deposit increases Base's total TVL.

4. Infrastructure: ZIN (Zero-Fee Intent Network) provides gasless intent-based execution for Base users, and our open SDK enables other developers to build on Kerne's infrastructure.
```

### What do you need funding for?
```
Total Request: $50,000

Breakdown:
1. External Security Audit — $30,000 (60%)
   Top-tier audit firm (Cyfrin, Sherlock, or Code4rena community audit) to verify all 35+ contracts. This is the #1 blocker for institutional adoption and TVL growth.

2. Liquidity Bootstrapping — $10,000 (20%)
   Seed vault TVL on Base to demonstrate the delta-neutral mechanism at scale. Current TVL is seed-stage; $10k in vault liquidity proves the mechanism generates real yield.

3. Operational Infrastructure — $5,000 (10%)
   Cloud hosting (DigitalOcean), RPC endpoints, monitoring, and domains for 6 months of 24/7 operation.

4. User Acquisition — $5,000 (10%)
   Deposit incentives and gas subsidies for Base-native users to onboard into the vault.
```

### Milestones
```
Month 1: Complete external security audit. Reach $100k TVL on Base vault.
Month 2: Launch deposit incentive program. Integrate with Aerodrome. Reach $500k TVL.
Month 3: SDK release for Base developers. Reach $1M TVL. 500+ unique depositors.
Month 6: $5M+ TVL. Listed on 3+ aggregators. 1,000+ unique depositors on Base.
```

### Team Background
```
Two core contributors building full-time since January 2026. Deep expertise in:
- Solidity (0.8.24, Foundry, OpenZeppelin v5, ERC-4626)
- Python (autonomous hedging engine, MEV, CCXT)
- TypeScript (Next.js frontend, SDK, Viem/Wagmi)
- DeFi mechanism design (delta-neutral strategies, funding rate capture, intent-based execution)
- Infrastructure (Docker, cloud deployment, CI/CD)
```

### Links
```
Website: https://kerne.ai
Documentation: https://docs.kerne.ai
Twitter: https://twitter.com/KerneProtocol
Base Vault (BaseScan): https://basescan.org/address/0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
Base Ecosystem PR: https://github.com/base/web/pull/2956
Contact: kerne.systems@protonmail.com
```

### Logo
```
Upload: frontend/public/kerne-logo-512.png (512x512 PNG)
Backup: frontend/public/kerne-logo-square.png (441x441 PNG)
```

---

## STEP 4: Email Version (If Using Option C)

**To:** builders@base.org
**Subject:** Builder Grant Application — Kerne Protocol (DeFi Infrastructure on Base)

**Body:**
```
Hi Base Team,

I'm writing to apply for the Base Builder Grants program. Kerne Protocol is delta-neutral yield infrastructure built natively on Base.

PROJECT SUMMARY
Kerne enables users to earn stable, market-agnostic yield by depositing ETH into noncustodial ERC-4626 vaults on Base. Our autonomous hedging engine opens matching short positions on Hyperliquid perpetual futures, neutralizing all price exposure. Users earn yield from funding rates plus LST staking rewards.

WHAT WE'VE BUILT (ALL ON BASE)
- KerneVault (ERC-4626): 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
- 35+ verified smart contracts on BaseScan
- 150+ Foundry tests (unit, integration, fuzzing, invariant)
- Autonomous hedging engine running 24/7 (8 Docker services)
- Live basis trade generating real yield
- ZIN (Zero-Fee Intent Network) for intent-based execution
- Cross-chain via LayerZero V2 OFT (Base + Arbitrum + Optimism)
- Full docs, transparency dashboard, and terminal at kerne.ai

HOW KERNE BENEFITS BASE
1. Sticky TVL — Delta-neutral vaults attract capital that stays regardless of market direction
2. Composability — ERC-4626 standard integrates with the entire Base DeFi ecosystem
3. Cross-chain inflow — LayerZero V2 bridges bring capital FROM other L2s TO Base
4. Infrastructure — ZIN provides gasless intent execution for Base users

FUNDING REQUEST: $50,000
- External Security Audit: $30,000 (top-tier firm — #1 blocker for institutional adoption)
- Liquidity Bootstrapping: $10,000 (seed vault TVL to demonstrate mechanism at scale)
- Operational Infrastructure: $5,000 (cloud hosting, RPCs, monitoring for 6 months)
- User Acquisition: $5,000 (deposit incentives for Base-native users)

MILESTONES
- Month 1: Complete audit, reach $100k TVL
- Month 2: Aerodrome integration, $500k TVL
- Month 3: SDK release, $1M TVL, 500+ depositors
- Month 6: $5M+ TVL, 1,000+ depositors on Base

LINKS
- Website: https://kerne.ai
- Docs: https://docs.kerne.ai
- Twitter: @KerneProtocol
- BaseScan: https://basescan.org/address/0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
- Base Ecosystem PR: https://github.com/base/web/pull/2956

We're two full-time contributors with deep Solidity, Python, and DeFi infrastructure experience. Happy to provide any additional information or schedule a call.

Best regards,
Kerne Protocol Team
kerne.systems@protonmail.com
```

---

## STEP 5: Post-Submission

After submitting:
1. Record the date and any confirmation/tracking ID below
2. Set a calendar reminder for 7 days to check status
3. Update project_state.md
4. If no response in 14 days, follow up via Base Discord or email builders@base.org

### Submission Record
| Field | Value |
|-------|-------|
| Date Submitted | |
| Method Used | (Form / Email / Discord) |
| Confirmation ID | |
| Status | |
| Follow-up Date | |
| Notes | |

---

*Document created: 2026-02-09*
*Ready for immediate execution*