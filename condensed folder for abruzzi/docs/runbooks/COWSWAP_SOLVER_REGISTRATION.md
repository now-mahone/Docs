# CowSwap Solver Registration Runbook
**Created:** 2026-01-20
**Priority:** #5 Strategic Priority
**Status:** READY_FOR_EXECUTION

## Objective
Register Kerne Protocol as an official CowSwap solver to unlock access to CowSwap auction order flow and expand ZIN intent fulfillment beyond UniswapX.

## Why This Matters
CowSwap’s solver network is gated. Without registration, the CowSwap auction endpoint returns HTTP 403. Becoming an approved solver provides:
- Access to CowSwap batch auctions and order flow
- Additional spread capture opportunities for ZIN
- Increased intent volume and diversification beyond UniswapX

## Current Status
- CowSwap endpoint access: **Blocked (403)**
- ZIN Solver: **Operational on UniswapX only**
- Registration: **Not yet submitted**

---

## Prerequisites

### 1. Technical Requirements
- Operational solver infrastructure (`bot/solver/zin_solver.py`)
- Live execution contract (KerneIntentExecutorV2)
- Available liquidity in ZIN Pool

### 2. Business Requirements
- Solver reputation (track record preferred, not mandatory)
- Optional bonding or stake (may be required by CowSwap)

### 3. Documentation Required
- Protocol overview
- Solver architecture description
- Smart contract addresses
- Security and safety controls

---

## Registration Steps

### Step 1: Prepare Application Materials
Create the following materials:

1. **Protocol Summary**
   - 2-3 sentence overview of Kerne and ZIN
   - Include delta-neutral execution edge and safety systems

2. **Solver Architecture Description**
   - CowSwap auction fetch -> profitability check -> fulfillIntent() via flash liquidity
   - Key guardrails: min_profit_bps, max gas, intent caps, liquidity checks

3. **Smart Contract References**
   - ZIN Executor (Base): `0x04F52F9F4dAb1ba2330841Af85dAeeB8eaC9E995`
   - ZIN Pool (Base): `0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7`

4. **Security Controls**
   - Sentinel risk engine
   - Auto-scaling by liquidity depth
   - Circuit breakers & gas ceilings

---

### Step 2: Submit Solver Application
CowSwap accepts solver applications via governance forum or direct contact.

**Primary Method:**
- CowSwap Governance Forum: https://forum.cow.fi
- Post under “Solver Requests” category

**Backup Method:**
- Reach out to CowSwap core team (e.g., @cowprotocol on Twitter or Discord)

---

### Step 3: Provide Required Technical Info
Include these details:

- Solver name: **Kerne Protocol**
- Operating chain(s): Base (8453), Arbitrum (42161)
- Executor contract address
- Wallet address for solver
- Safety mechanisms
- Willingness to post bond (if required)

---

### Step 4: Await Approval
- CowSwap review cycles can take 1–2 weeks
- Be ready to answer follow-up questions

---

### Step 5: Enable CowSwap in ZIN Solver
Once approved:

1. Remove CowSwap 403 guardrails (already implemented but blocked)
2. Set CowSwap API base URL (already configured)
3. Restart solver

---

## Post-Approval Validation

### Test 1: Confirm Auction Access
Run:
```bash
python bot/solver/zin_solver.py --metrics-only
```
Expected:
```
CowSwap: API reachable (endpoint=https://api.cow.fi/base/api/v1)
```

### Test 2: Execute Micro-Intent
- Fill a minimal CowSwap order in dry-run
- Verify no 403 errors

---

## Success Criteria
- [ ] CowSwap application submitted
- [ ] CowSwap approved Kerne as solver
- [ ] CowSwap auction API accessible (200)
- [ ] ZIN solver fills at least 1 CowSwap intent

---

## Contacts
- CowSwap Governance Forum: https://forum.cow.fi
- CowSwap Discord: https://discord.gg/cowprotocol
- CowSwap Docs: https://docs.cow.fi
