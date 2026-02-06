// Created: 2026-02-06
# Kerne Protocol — DeFi Safety Review Packet

> Prepared for independent protocol safety review by DeFi Safety (https://defisafety.com).
> All information accurate as of 2026-02-06.
> This document also serves as a reusable Protocol Facts Sheet for all aggregator submissions.

---

## 1. Protocol Identity

| Field | Value |
|-------|-------|
| **Name** | Kerne Protocol |
| **Website** | https://kerne.ai |
| **Category** | Delta-Neutral Yield Infrastructure |
| **Chains** | Base (Coinbase L2), Arbitrum One |
| **Launch Date** | 2025-06-04 (Base mainnet) |
| **Contact** | kerne.systems@protonmail.com |
| **Twitter** | @KerneProtocol |
| **GitHub** | https://github.com/kerne-protocol |

---

## 2. How It Works

Kerne Protocol enables users to earn stable, market-agnostic yield by combining two uncorrelated revenue streams:

1. **Long Leg (On-Chain):** Users deposit ETH into noncustodial ERC-4626 vaults on Base or Arbitrum.
2. **Short Leg (Off-Chain):** An autonomous hedging engine opens equal-sized short positions on Hyperliquid perpetual futures, neutralizing all price exposure.
3. **Revenue Streams:**
   - Perpetual futures funding rate payments (shorts receive funding when rate > 0)
   - Liquid staking token (LST) yield from wstETH exposure
4. **Result:** Delta-neutral position earning stable yield with zero directional risk.

### Synthetic Dollar (kUSD)
- Yield-bearing synthetic dollar minted against vault collateral
- Maintains 1:1 peg via Peg Stability Module (PSM)
- Cross-chain via LayerZero V2 OFT standard

### ZIN (Zero-Fee Intent Network)
- Intent-based liquidity aggregation layer
- Zero-fee flash loans for atomic arbitrage
- MEV protection via intent batching

---

## 3. Smart Contract Architecture

### 3.1 Core Contracts — Base Network

| Contract | Address | Purpose |
|----------|---------|---------|
| KerneVault | `0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC` | ERC-4626 delta-neutral yield vault |
| KerneTreasury | `0x0067F4957dea17CF76665F6A6585F6a904362106` | Protocol treasury management |
| KerneInsuranceFund | `0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9` | Tail risk coverage fund |
| KerneStaking | `0x032Af1631671126A689614c0c957De774b45D582` | KERNE token staking |
| KerneIntentExecutor | `0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995` | ZIN intent execution engine |
| KerneZINPool | `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7` | ZIN liquidity pool |
| KerneFlashArbBot | `0xaED581A60db89fEe5f1D8f04538c953Cc78A1687` | Automated arbitrage for peg stability |
| KUSDPSM | `0x7286200Ba4C6Ed5041df55965c484a106F4716FD` | kUSD Peg Stability Module |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | Protocol governance token |
| kUSD OFT V2 | `0x257579db2702BAeeBFAC5c19d354f2FF39831299` | Cross-chain kUSD (LayerZero V2) |
| KERNE OFT V2 | `0x4E1ce62F571893eCfD7062937781A766ff64F14e` | Cross-chain KERNE (LayerZero V2) |

### 3.2 Core Contracts — Arbitrum One

| Contract | Address | Purpose |
|----------|---------|---------|
| KerneVault | `0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF` | ERC-4626 yield vault (USDC) |
| KerneIntentExecutor | `0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb` | ZIN intent execution engine |
| KerneZINPool | `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD` | ZIN liquidity pool |
| kUSD OFT | `0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222` | Cross-chain kUSD (LayerZero) |
| KERNE OFT | `0x087365f83caF2E2504c399330F5D15f62Ae7dAC3` | Cross-chain KERNE (LayerZero) |

### 3.3 Verification Status
All contracts are verified on their respective block explorers:
- BaseScan: https://basescan.org/address/[contract_address]
- Arbiscan: https://arbiscan.io/address/[contract_address]

---

## 4. Standards Compliance

| Standard | Status | Details |
|----------|--------|---------|
| **ERC-4626** | Compliant | Vaults implement full tokenized vault standard |
| **ERC-20** | Compliant | KERNE token, kUSD, vault shares |
| **LayerZero V2 OFT** | Compliant | Cross-chain token bridging |
| **EIP-2612 Permit** | Supported | Gasless approvals |

---

## 5. Testing & Quality

### 5.1 Test Suite

- **Total Tests:** 154
- **Pass Rate:** 100% (0 failures)
- **Test Framework:** Foundry (Forge)
- **Test Categories:**
  - Unit tests (contract function correctness)
  - Integration tests (multi-contract interaction flows)
  - Security tests (access control, reentrancy, overflow/underflow)

### 5.2 Test Execution
```bash
forge test --summary
# Result: 154 tests passing, 0 failing, 0 skipped
```

### 5.3 Code Quality
- Written in Solidity 0.8.x with strict compiler settings
- Uses OpenZeppelin v5 audited base contracts
- Foundry-based development and testing pipeline
- Automated CI via GitHub Actions

---

## 6. Security Architecture

### 6.1 Access Control
- **Owner multisig:** Controls protocol parameters (fee rates, circuit breaker thresholds)
- **No upgradeable proxies on core vaults:** Vault logic is immutable after deployment
- **Role-based access:** Separate roles for operators, treasury managers, and admin functions
- **Timelock:** Critical parameter changes subject to time delay

### 6.2 Risk Management — On-Chain
| Feature | Description |
|---------|-------------|
| **Circuit Breakers** | Automated trading halts triggered by depeg > threshold |
| **Oracle Guard** | Cross-references multiple price feeds to prevent oracle manipulation |
| **Insurance Fund** | Protocol revenue allocation for tail risk coverage |
| **Max Deposit Caps** | Per-vault and per-user deposit limits during growth phase |
| **Withdrawal Queuing** | Orderly withdrawal processing prevents bank-run scenarios |

### 6.3 Risk Management — Off-Chain (Hedging Engine)
| Feature | Description |
|---------|-------------|
| **Delta Monitor** | Continuous monitoring of long/short position delta |
| **Auto-Rebalance** | Automatic hedge adjustment when delta drift exceeds threshold |
| **Funding Rate Monitor** | Tracks 8-hour funding rate changes, adjusts positions |
| **Sentinel System** | 24/7 monitoring with webhook alerts |
| **Panic System** | Emergency position closure if anomalies detected |

### 6.4 Custody Architecture
- **Noncustodial vaults:** Users retain withdrawal rights at all times
- **No external custody services:** Protocol holds assets directly in smart contracts
- **Hedge collateral on Hyperliquid:** Exchange-level custody (non-custodial DEX)

---

## 7. Audit Status

| Item | Status |
|------|--------|
| **Formal Audit** | Not yet completed |
| **Internal Security Review** | Completed (154 tests including security-focused tests) |
| **Bug Bounty Program** | Planned |
| **OpenZeppelin Base Contracts** | Audited (v5 — industry standard) |

### Audit Plan
- Formal audit is planned for post-TVL milestone ($500K+)
- Current security relies on:
  - 154 comprehensive tests with security-focused test suite
  - OpenZeppelin audited base contracts
  - Immutable vault contracts (no proxy upgrade risk)
  - Conservative deposit caps during growth phase

---

## 8. Documentation

| Document | Location |
|----------|----------|
| **Technical Whitepaper** | `docs/whitepaper/` |
| **Proof of Solvency Spec** | `docs/proof_of_solvency_technical.md` |
| **Treasury Ledger** | `docs/TREASURY_LEDGER.md` |
| **Deployment Records** | `deployments/` |
| **Operational Runbooks** | `docs/runbooks/` |
| **Architecture Guides** | `docs/specs/` |

---

## 9. Transparency Metrics

| Metric | Value | Source |
|--------|-------|--------|
| **Base Vault TVL** | On-chain (totalAssets()) | `0xDF9a...C695` |
| **Arbitrum Vault TVL** | On-chain (totalAssets()) | `0x503D...41FF` |
| **Funding Rate Revenue** | Hyperliquid API | Real-time |
| **Solvency Status** | Block-by-block verification | Automated |
| **Insurance Fund Balance** | On-chain | `0x3C93...08B9` |

### Real-Time Verification
Anyone can verify protocol solvency by calling:
```
totalAssets() on vault contracts — returns total underlying assets
totalSupply() on vault contracts — returns total vault shares outstanding
```
Share price = totalAssets / totalSupply (should be >= 1.0 for healthy vault)

---

## 10. Team

- Anonymous team with public operational track record
- Multi-signature governance
- Active community engagement via Twitter (@KerneProtocol)
- Responsive to security disclosures via kerne.systems@protonmail.com

---

## 11. Known Risks (Self-Disclosed)

| Risk | Severity | Mitigation |
|------|----------|------------|
| **Funding Rate Reversal** | Medium | Circuit breakers close positions when funding turns negative for extended period |
| **Exchange Risk (Hyperliquid)** | Medium | Hyperliquid is a decentralized exchange; counterparty risk is lower than CEX |
| **Smart Contract Risk** | Medium | 154 tests, OpenZeppelin base contracts, conservative deposit caps |
| **Oracle Manipulation** | Low | Oracle Guard cross-references multiple price feeds |
| **Depeg Risk (kUSD)** | Low | PSM with automated arbitrage bot maintains peg |
| **Liquidity Risk** | Low | Withdrawal queuing prevents bank-run scenarios |

---

## 12. Submission Contact

For questions about this review packet:
- **Email:** kerne.systems@protonmail.com
- **Twitter:** @KerneProtocol
- **Website:** https://kerne.ai