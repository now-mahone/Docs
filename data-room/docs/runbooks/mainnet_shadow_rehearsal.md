# Kerne Protocol: Mainnet Shadow Rehearsal Runbook

## Overview
This runbook outlines the steps for a "Mainnet Shadow" rehearsal—a full lifecycle simulation on a local fork to catch integration errors before real capital is deployed.

## 1. Environment Setup
- [ ] **Fork Chain:** `anvil --fork-url $RPC_URL --chain-id 8453` (Base)
- [ ] **Load Secrets:** Ensure `.env` has `STRATEGIST_PRIVATE_KEY` and `ADMIN_PRIVATE_KEY`.
- [ ] **Verify Balances:** Ensure deployer has enough ETH for gas.

## 2. Deployment Sequence
- [ ] **Deploy Oracle:** `forge script script/DeployYieldOracle.s.sol --rpc-url http://localhost:8545 --broadcast`
- [ ] **Deploy Vault:** `forge script script/DeployRegistry.s.sol --rpc-url http://localhost:8545 --broadcast`
- [ ] **Configure Roles:**
    - [ ] Grant `STRATEGIST_ROLE` to the bot address.
    - [ ] Set `YieldOracle` address in the Vault.
    - [ ] Set `InsuranceFund` address.

## 3. Lifecycle Simulation
- [ ] **Initial Deposit:** Simulate a whale deposit (e.g., 100 ETH).
    - `cast send $VAULT "deposit(uint256,address)" 100000000000000000000 $USER --rpc-url http://localhost:8545`
- [ ] **Sweep to Exchange:** Admin sweeps 90% to the exchange deposit address.
    - `cast send $VAULT "sweepToExchange(uint256)" 90000000000000000000 --rpc-url http://localhost:8545`
- [ ] **Bot Rebalance:** Run `bot/main.py` in dry-run mode against the local fork.
    - Verify it detects the deposit and calculates the required short position.
- [ ] **Yield Reporting:**
    - Strategist updates off-chain assets: `cast send $VAULT "updateOffChainAssets(uint256)" $AMOUNT --rpc-url http://localhost:8545`
    - Oracle update: `cast send $ORACLE "updateYield(address)" $VAULT --rpc-url http://localhost:8545`

## 4. Verification & PoR
- [ ] **Run PoR Bot:** `python bot/por_attestation.py`
    - Verify the generated report correctly reflects on-chain + off-chain assets.
- [ ] **Check Solvency Invariant:** Run `test/security/KerneSecuritySuite.t.sol` against the fork state.

## 5. Cleanup & Log
- [ ] Document any reverted transactions or permission errors.
- [ ] Update `mainnet_launch_checklist.md` with findings.
