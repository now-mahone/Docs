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
| kUSD OFT | `0xb50bFec5FF426744b9d195a8C262da376637Cb6A` | kUSD token (LayerZero) |
| KERNE OFT | `0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255` | KERNE token (LayerZero) |
| KERNE Token | `0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340` | Governance token |
| KERNE Staking | `0x032Af1631671126A689614c0c957De774b45D582` | Staking contract |

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

---

## Current Balances (Last Updated: 2026-01-18)

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

## CEX Accounts

### Hyperliquid
- **Deposit Address:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`
- **Balance:** ~$32.82 USDC (as of 2026-01-13)
- **Purpose:** Delta-neutral hedging

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
