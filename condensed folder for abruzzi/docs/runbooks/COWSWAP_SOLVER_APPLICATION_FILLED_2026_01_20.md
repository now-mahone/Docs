// Created: 2026-01-20
# CowSwap Solver Application (Filled)
**Date:** 2026-01-20
**Status:** READY_TO_SUBMIT

---

## Title
**Solver Request: Kerne Protocol (ZIN Intent Execution Engine)**

---

## 1. Project Overview
Kerne Protocol is a delta-neutral synthetic dollar protocol on Base that operates the Zero-Fee Intent Network (ZIN). ZIN monitors intent order flow (UniswapX + CowSwap) and fulfills profitable intents using internal flash liquidity, capturing spread as protocol revenue while maintaining institutional-grade safety controls.

---

## 2. Solver Infrastructure
- **Solver Name:** Kerne Protocol (ZIN Solver)
- **Chains:** Base (8453), Arbitrum (42161)
- **Execution Flow:**
  1. Fetch CowSwap auctions
  2. Normalize intents
  3. Quote via Aerodrome / 1inch
  4. Validate profit + guardrails
  5. Execute `fulfillIntent()` using flash liquidity

---

## 3. Contracts
**Base (8453)**
- **ZIN Executor:** `0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995`
- **ZIN Pool:** `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7`

**Arbitrum (42161)**
- **ZIN Executor:** `0xbf039eB5CF2e1d0067C0918462fDd211e252Efdb`
- **ZIN Pool:** `0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD`

---

## 4. Safety & Guardrails
- Minimum profit threshold (bps)
- Gas price ceiling
- Auto-scaling by pool liquidity
- Sentinel risk engine w/ circuit breakers
- Max intent size caps per token

---

## 5. Liquidity & Execution
- Internal pool liquidity (ZIN Pool)
- Flash loan execution, atomic settlement
- Profit routed to protocol treasury

---

## 6. Solver Wallet
- **Solver Wallet:** `0x57D400cED462a01Ed51a5De038F204Df49690A99`

---

## 7. Contact Info
- **Primary Contact:** @KerneProtocol
- **Email:** kerne.systems@protonmail.com

---

## 8. Additional Notes
We are prepared to provide any additional technical details, bonding requirements, or test runs required by CowSwap governance.
