# Created: 2026-02-07
# Kerne Protocol — Aggregator Submissions (READY TO EXECUTE)

This document contains EVERYTHING needed to submit Kerne to 3 aggregator platforms.
All text fields are copy-paste ready. Execute in order.

---

## SUBMISSION 1: DappRadar (PRIORITY)
**URL:** https://dappradar.com/dashboard/submit-dapp
**Time:** ~10 minutes
**Difficulty:** Low (self-service form)
**Expected Review:** 3-7 business days

### Step 1: Create Account
1. Go to https://dappradar.com/dashboard/submit-dapp
2. Sign up with: kerne.systems@protonmail.com
3. Verify email

### Step 2: Fill Form (Copy-Paste Values)

**DApp Name:**
```
Kerne Protocol
```

**Website URL:**
```
https://kerne.ai
```

**Category:** `DeFi`

**Subcategory:** `Yield` (or `Staking` if Yield not available)

**Short Description (under 160 chars):**
```
Delta-neutral yield infrastructure. Deposit ETH into ERC-4626 vaults, earn stable yield from funding rates and staking. Zero directional risk.
```

**Full Description:**
```
Kerne Protocol is delta-neutral yield infrastructure built natively on Base. The protocol enables users to earn stable, market-agnostic yield by combining two uncorrelated revenue streams: liquid staking token rewards and perpetual futures funding rate capture via Hyperliquid.

How It Works:
1. Users deposit ETH into noncustodial ERC-4626 vaults on Base
2. The autonomous hedging engine opens equal-sized short positions on Hyperliquid perpetual futures, neutralizing all ETH price exposure
3. Users earn yield from funding rates plus staking rewards, reflected as vault share appreciation

Key Features:
• Delta-Neutral Architecture — Zero directional market risk
• ERC-4626 Vaults — Standard composable vault interface on Base and Arbitrum
• Cross-Chain via LayerZero V2 — Seamless asset bridging between Base, Arbitrum, and Optimism
• Real-Time Solvency Verification — Block-by-block proof of reserves
• Automated Circuit Breakers — Sub-second risk management and depeg protection
• Insurance Fund — Protocol revenue allocation for tail risk coverage
• ZIN (Zero-Fee Intent Network) — Intent-based liquidity aggregation

Deployed and verified on Base mainnet. 150+ passing smart contract tests.
```

**Blockchain(s):** Select `Base` and `Arbitrum One`

**Smart Contract Address (Base):**
```
0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
```

**Smart Contract Address (Arbitrum):**
```
0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF
```

**Social Media — Twitter/X:**
```
https://twitter.com/KerneProtocol
```

**Social Media — Discord:** (leave blank or add if created)

**Contact Email:**
```
kerne.systems@protonmail.com
```

**Logo:** Upload `frontend/public/kerne-logo.png` (256x256+)

**Screenshots:** Upload screenshots from kerne.ai (Terminal, Vault interface, Transparency page)
- If the site isn't live yet (Mahone fixing Vercel), use the locally built version or wait until Vercel is fixed

### Step 3: Submit and Record
- Note the submission/tracking ID
- Expected: 3-7 business days for review
- Check DappRadar dashboard for status updates

---

## SUBMISSION 2: DeBank
**Method:** Email to protocol-listing@debank.com
**Time:** ~5 minutes (email)
**Difficulty:** Low
**Expected Review:** 1-2 weeks

### Email Template (Copy-Paste)

**To:** protocol-listing@debank.com
**Subject:** Protocol Listing Request — Kerne Protocol (Base + Arbitrum)

**Body:**
```
Hi DeBank Team,

I would like to request listing Kerne Protocol on DeBank's protocol tracking dashboard.

Protocol Details:
- Name: Kerne Protocol
- Website: https://kerne.ai
- Category: DeFi — Yield / Delta-Neutral
- Twitter: @KerneProtocol
- Contact: kerne.systems@protonmail.com

Chains Deployed:
1. Base (Chain ID: 8453)
2. Arbitrum One (Chain ID: 42161)

Primary Contracts:
- Base Vault (ERC-4626): 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
- Arbitrum Vault (ERC-4626): 0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF

Protocol Description:
Kerne Protocol is delta-neutral yield infrastructure built on Base. Users deposit ETH into noncustodial ERC-4626 vaults. The protocol's autonomous hedging engine opens equal-sized short positions on Hyperliquid perpetual futures, neutralizing all price exposure, and users earn yield from funding rate income and LST staking rewards.

The protocol features real-time solvency verification, automated circuit breakers, cross-chain expansion via LayerZero V2 OFT to Arbitrum and Optimism, and 150+ passing smart contract tests.

Additional Contracts (Base):
- ZIN Pool: 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7
- ZIN Executor: 0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995
- KERNE Token: 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340
- kUSD OFT V2: 0x257579db2702BAeeBFAC5c19d354f2FF39831299

All contracts are verified on BaseScan and Arbiscan. Happy to provide any additional information needed.

Best regards,
Kerne Protocol Team
```

---

## SUBMISSION 3: DeFi Safety
**Method:** Submit protocol for independent safety review
**URL:** https://defisafety.com/submit
**Time:** ~10 minutes
**Difficulty:** Medium (detailed questionnaire)
**Expected Review:** 2-4 weeks

### Why DeFi Safety
- Independent safety ratings used by institutional investors
- Having a rating adds significant credibility for outreach
- Our 150+ tests and ERC-4626 compliance are strong signals

### Information to Provide

**Protocol Name:**
```
Kerne Protocol
```

**Website:**
```
https://kerne.ai
```

**Documentation:**
```
https://kerne.ai (Litepaper available on-site)
```

**Smart Contracts (GitHub):**
The contracts are in a private repository. If DeFi Safety requires public source access, we can provide:
- Verified source code on BaseScan: https://basescan.org/address/0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC#code
- All contracts verified with full source

**Testing:**
```
150+ passing tests across unit, integration, and security test suites. 
Built with Foundry (Solidity 0.8.24). Test coverage includes:
- Unit tests for all vault, PSM, and token logic
- Integration tests for full deposit-hedge-yield-withdraw cycle
- Security tests including fuzzing and invariant testing
- Access control and circuit breaker verification
```

**Chains:**
```
Base (ERC-4626 Vault), Arbitrum One (ERC-4626 Vault)
```

**Admin Keys / Multisig:**
```
Protocol controlled by deployer address (0x57D4...0A99) with plans to migrate to Gnosis Safe multisig. 
Vault has STRATEGIST_ROLE and PAUSER_ROLE for operational safety.
Emergency pause functionality available to PAUSER_ROLE holders.
```

**Oracle Dependencies:**
```
No direct oracle dependency for core vault operations. 
Vault uses ERC-4626 standard totalAssets() for NAV calculation.
Chainlink price feeds used optionally for solvency reporting.
```

**Audit Status:**
```
Internal security review completed. External audit planned.
150+ Foundry tests including fuzzing and invariant tests.
Verified source code on BaseScan and Arbiscan.
```

---

## SUBMISSION 4: Base Ecosystem Directory (BONUS)
**Method:** Submit to Base ecosystem page
**URL:** https://base.org/ecosystem (check for submission link)
**Note:** Base ecosystem listings drive organic discovery from Coinbase-adjacent users

### Information to Provide
Same as DappRadar submission above. Emphasize:
- Built natively on Base
- ERC-4626 standard vault
- Uses Coinbase-native infrastructure
- Cross-chain to Arbitrum and Optimism via LayerZero V2

---

## EXECUTION ORDER

| # | Platform | Method | Status |
|---|----------|--------|--------|
| 1 | DappRadar | Web Form | [ ] Ready to submit |
| 2 | DeBank | Email | [ ] Ready to send |
| 3 | DeFi Safety | Web Form | [ ] Ready to submit |
| 4 | Base Ecosystem | TBD | [ ] Check submission process |

---

## POST-SUBMISSION TRACKING

After each submission:
1. Record the date and confirmation ID in this document
2. Set a calendar reminder for 7 days to check status
3. If approved, update project_state.md
4. Once 1+ platforms list us, prepare DefiLlama re-submission

| Platform | Date Submitted | Status | Listed Date | Notes |
|----------|---------------|--------|-------------|-------|
| DappRadar | | | | |
| DeBank | | | | |
| DeFi Safety | | | | |
| Base Ecosystem | | | | |