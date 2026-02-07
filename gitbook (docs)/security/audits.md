// Created: 2026-02-07

# Audits & Invariants

Kerne maintains the highest security standards through formal verification, continuous auditing, and mathematically enforced invariants.

## Audit Program

### Smart Contract Audits
All core contracts undergo rigorous third-party audits before mainnet deployment:

| Contract | Auditor | Status |
|----------|---------|--------|
| KerneVault (ERC-4626) | Pending | Scheduled Q1 2026 |
| KernePSM | Pending | Scheduled Q1 2026 |
| KerneZINPool | Pending | Scheduled Q2 2026 |
| KerneIntentExecutor | Pending | Scheduled Q2 2026 |
| KerneTreasury | Pending | Scheduled Q1 2026 |

### Bug Bounty Program
Kerne operates a tiered bug bounty program for responsible disclosure:

| Severity | Reward |
|----------|--------|
| Critical (fund loss) | Up to $250,000 |
| High (protocol disruption) | Up to $50,000 |
| Medium (logic errors) | Up to $10,000 |
| Low (informational) | Up to $1,000 |

## Core Invariants

The protocol enforces the following mathematical invariants at the smart contract level. These are checked on every state-changing transaction:

### 1. Solvency Invariant
```
totalAssets() >= totalSupply() * sharePrice
```
The vault must always hold enough assets to cover all outstanding shares at the current share price.

### 2. Hedge Ratio Invariant
```
abs(onChainPosition - offChainShort) / onChainPosition <= 0.02
```
The hedge ratio must remain within 2% of perfect neutrality. Sentinel triggers rebalancing if this threshold is approached.

### 3. PSM Reserve Invariant
```
PSM_USDC_Balance >= PSM_kUSD_Outstanding
```
The PSM must always hold sufficient reserves to cover all kUSD minted through the stability module.

### 4. Insurance Fund Minimum
```
insuranceFundBalance >= totalHedgedNotional * 0.05
```
The Insurance Fund must maintain a minimum 5% buffer relative to total hedged notional to absorb adverse funding rate periods.

## Testing Infrastructure

### Foundry Test Suite
- **Unit Tests**: Every public function has dedicated test coverage with both happy-path and revert cases.
- **Fuzz Testing**: Critical functions are fuzz-tested with randomized inputs to discover edge cases.
- **Fork Testing**: Integration tests run against live Base mainnet forks to ensure compatibility with real protocol state.
- **Gas Snapshots**: `forge snapshot` is run on every commit to detect gas regressions.

### Invariant Testing
Foundry's invariant testing framework is used to continuously verify that core protocol invariants hold across thousands of randomized transaction sequences.

```solidity
function invariant_solvency() public {
    assertGe(vault.totalAssets(), vault.totalSupply());
}
```

## Incident Response

In the event of a detected vulnerability:
1. **Sentinel** automatically pauses affected contracts.
2. The core team is alerted via the on-call notification system.
3. A post-mortem is published within 72 hours of resolution.
4. Affected users are made whole from the Insurance Fund.

---
*Created: 2026-02-07*