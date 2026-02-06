# Kerne Protocol Treasury Ledger

## Overview
This document tracks all capital movements, wallet balances, and protocol-owned funds for Scofield's records.

---

## Wallets & Addresses

### Scofield's Hot Wallet (Deployer / Trezor Root)
- **Address:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Network:** Multi-chain (Base, Ethereum, etc.)
- **Purpose:** Deployment, seeding, and operational transactions
- **Note:** This is the owner of both Gnosis Safes below

### Gnosis Safe: Kerne Treasury Trezor (DEPLOYED)
- **Address:** `0xa29528c5ae6969053CA4560a3608Fb9531D868E5`
- **Network:** Ethereum Mainnet
- **Owner:** Trezor Root (`0x57D4...0A99`)
- **Threshold:** 1 of 1
- **Status:** ✅ Active - CHECK FOR FUNDS
- **Etherscan:** https://etherscan.io/address/0xa29528c5ae6969053CA4560a3608Fb9531D868E5

### Gnosis Safe: Kerne Treasury Metamask (UNDEPLOYED)
- **Address:** `0xcd07236752CaFFC1EBb4cA9ed92b6Cce9CDac086`
- **Network:** Ethereum Mainnet
- **Owner:** Trezor Root (`0x57D4...0A99`)
- **Threshold:** 1 of 1
- **Status:** ⚠️ AWAITING_EXECUTION - Never deployed on-chain, cannot hold funds

### Protocol Contracts (Base Mainnet)

| Contract | Address | Purpose |
|----------|---------|---------|
| KerneVault | `0xDF9a2f5152c533F7fcc3bAdEd41e157C9563C695` | Main yield vault |
| ZIN Pool | `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7` | Intent execution liquidity |
| ZIN Executor | `0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995` | Intent fulfillment contract |
| KerneTreasury | `0xB656440287f8A1112558D3df915b23326e9b89ec` | Protocol treasury |
| InsuranceFund | `0x3C93E231a3b74659ABfCA95dFf2eC9a8525b08B9` | Insurance reserves |
| FlashArbBot | `0xaED581A60db89fEe5f1D8f04538c953Cc78A1687` | Arbitrage executor |
| KUSD PSM | `0x7286200Ba4C6Ed5041df55965c484a106F4716FD` | Peg stability module |
| kUSD OFT V1 ⚠️ | `0xb50bFec5FF426744b9d195a8C262da376637Cb6A` | **DEPRECATED** - LZ V1 incompatible |
| KERNE OFT V1 ⚠️ | `0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255` | **DEPRECATED** - LZ V1 incompatible |
| **kUSD OFT V2** | `0x257579db2702BAeeBFAC5c19d354f2FF39831299` | kUSD token (LayerZero V2) ✅ |
| **KERNE OFT V2** | `0x4E1ce62F571893eCfD7062937781A766ff64F14e` | KERNE token (LayerZero V2) ✅ |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | Governance token |
| KERNE Staking | `0x032Af1631671126A689614c0c957De774b45D582` | Staking contract |

### Protocol Contracts (Arbitrum One) - DEPLOYED 2026-01-20

| Contract | Address | Purpose |
|----------|---------|---------|
| **KerneVault** | `0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF` | Main wstETH vault ✅ |
| ZIN Executor | `0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb` | Intent fulfillment contract |
| ZIN Pool | `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD` | Intent execution liquidity |
| **kUSD OFT V2** | `0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222` | kUSD token (LayerZero V2) ✅ |
| **KERNE OFT V2** | `0x087365f83caF2E2504c399330F5D15f62Ae7dAC3` | KERNE token (LayerZero V2) ✅ |
| | | |

### Protocol Contracts (Optimism Mainnet) - PRE-FLIGHTED 2026-01-27

| Contract | Address | Purpose | Status |
|----------|---------|---------|--------|
| **KerneVault** | `0x5FD0F7eA40984a6a8E9c6f6BDfd297e7dB4448Bd` | Main wstETH vault | ⚠️ AWAITING_GAS |
| ZIN Executor | `0xb3AD51979bB7B03F0Be43d36350428170d87EF08` | Intent fulfillment contract | ⚠️ AWAITING_GAS |
| ZIN Pool | `0x6b8c81d40F5Fb94d2156BCe053DC162f9b265564` | Intent execution liquidity | ⚠️ AWAITING_GAS |
| **kUSD OFT V2** | `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD` | kUSD token (LayerZero V2) | ⚠️ AWAITING_GAS |
| **KERNE OFT V2** | `0x924Dc3a2a40FFEaC98634E5a6360ad424b0B0d49` | KERNE token (LayerZero V2) | ⚠️ AWAITING_GAS |

---

## Capital Movements Log

### Format
```
[DATE] | [TYPE] | [FROM] | [TO] | [AMOUNT] | [TOKEN] | [NETWORK] | [TX HASH] | [NOTES]
```

### Transactions

| Date | Type | From | To | Amount | Token | Network | TX Hash | Notes |
|------|------|------|-----|--------|-------|---------|---------|-------|
| 2026-01-17 | PLANNED | Hot Wallet | ZIN Pool | $80 | USDC/WETH | Base | - | ZIN Pool seeding (planned) |
| 2026-01-18 | SEED | Trezor Hot Wallet | ZIN Pool | 39.772851 | USDC | Base | - | ZIN Pool seed (from Trezor) |
| 2026-01-18 | SEED | Trezor Hot Wallet | ZIN Pool | 0.01178582 | WETH | Base | - | ZIN Pool seed (from Trezor) |
| 2026-02-04 | ONRAMP | BMO | Burner Wallet | 362 | USDC | Polygon | - | Shadow Onramp Phase 1 Complete (Trezor) |

---

## Current Balances (Last Updated: 2026-02-04)

### Burner Wallet (Trezor - `0x14f0...3946`)
| Token | Amount | USD Value | Network |
|-------|--------|-----------|---------|
| USDC | 362 | $362 | Polygon |

### Hot Wallet (`0x57D4...0A99`)
| Token | Amount | USD Value | Network |
|-------|--------|-----------|---------|
| ETH | ~ | ~$140 | Trezor (Primary) |
| ETH | ~ | ~$40 | Base (A99) |

### Gnosis Safe: Kerne Treasury Trezor (`0xa295...68E5`)
| Token | Amount | USD Value | Network |
|-------|--------|-----------|---------|
| ETH | ~ | ~$35 | Ethereum |

### ZIN Pool (`0xB9Bd...d0c7`)
| Token | Amount | USD Value | Network |
|-------|--------|-----------|---------|
| USDC | 39.772851 | ~$39.76 | Base |
| WETH | 0.01178582 | ~$39.58 | Base |

### KerneVault (`0xDF9a...c695`)
| Token | Amount | USD Value | Network |
|-------|--------|-----------|---------|
| WETH | TBD | TBD | Base |

---

## CEX & Fiat Accounts

### Hyperliquid
- **Deposit Address:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Balance:** ~$32.82 USDC (as of 2026-01-13)
- **Purpose:** Delta-neutral hedging

### PayTrie (Fiat On-Ramp)
- **Account Email:** ProtonMail (Primary)
- **Purpose:** CAD to USDC bridge

---

## Summary Totals

| Category | USD Value | Notes |
|----------|-----------|-------|
| Hot Wallet | ~$180 | Trezor + Base A99 |
| Protocol Contracts | ~$79.34 | ZIN Pool seed (USDC + WETH) |
| Gnosis Safe | ~$35 | Treasury safe |
| CEX (Hyperliquid) | ~$33 | Hedging collateral |
| **TOTAL** | ~$327.34 | Approximate |

---

## Notes
- Always verify addresses before sending
- Use BaseScan to confirm transactions: https://basescan.org
- Update this ledger after every capital movement
- Keep TX hashes for audit trail

---

## Update Instructions
After any transaction:
1. Add a new row to the "Capital Movements Log" table
2. Update the "Current Balances" section
3. Update the "Summary Totals"
4. Commit changes to git with message: `[YYYY-MM-DD] treasury: <description>`
