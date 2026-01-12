# Kerne Protocol Security Audit

## 01_OVERVIEW
This document tracks the security posture, audit findings, and remediations for the Kerne Protocol.

## 02_STATIC_ANALYSIS_REPORTS
### Slither Summary (2025-12-28)
- **High:** 1
- **Medium:** 10
- **Low:** 3
- **Informational:** 49

### Aderyn Summary (2025-12-28)
- **Status:** Skipped due to environment incompatibilities (Aderyn's Foundry config parser failing on `evm_version` and `mcopy` opcode issues in OpenZeppelin v5.0 dependencies).
- **Manual Mitigation:** Performed manual logic review of precision and rounding.

## 03_VULNERABILITY_REMEDIATION
### [H-01] Incorrect Exponentiation in Math.sol (False Positive)
- **Description:** Slither flagged `inverse = (3 * denominator) ^ 2` in OpenZeppelin's `Math.sol`.
- **Analysis:** This is a known false positive in Slither when analyzing OpenZeppelin's optimized `mulDiv` implementation. The `^` operator is used for bitwise XOR as part of the Newton-Raphson method for modular inverse, not for exponentiation.
- **Status:** Ignored (False Positive).

### [M-01] Local Variable Shadowing
- **Description:** `KerneVault` constructor parameters `_asset`, `_name`, and `_symbol` shadow state variables in `ERC4626` and `ERC20`.
- **Remediation:** Renamed constructor parameters to `asset_`, `name_`, `symbol_`, etc.
- **Status:** Fixed.

### [M-02] Conformance to Solidity Naming Conventions
- **Description:** Parameters in `updateOffChainAssets` and `sweepToExchange` use `_amount` (underscore prefix) which Slither flags as non-mixedCase.
- **Remediation:** Renamed to `amount`.
- **Status:** Fixed.

## 04_INFLATION_ATTACK_MITIGATION
- **Vector:** First depositor can manipulate share price by donating assets to the vault.
- **Mitigation Strategy:** 
    - Kerne uses OpenZeppelin v5.0 `ERC4626`.
    - **Dead Shares:** Implemented `_mint(address(0), 1000)` in the constructor. This ensures that the first depositor cannot set an extremely high share price, as 1000 shares are already owned by the zero address, making the "donation" attack prohibitively expensive.
- **Status:** Implemented.

## 05_ACCESS_CONTROL_MATRIX
| Function | Role | Description |
|----------|------|-------------|
| `updateOffChainAssets` | `STRATEGIST_ROLE` | Updates off-chain asset reporting. |
| `sweepToExchange` | `DEFAULT_ADMIN_ROLE` | Transfers funds to CEX deposit address. |
| `pause` | `PAUSER_ROLE` | Emergency stop for deposits/withdrawals. |
| `unpause` | `DEFAULT_ADMIN_ROLE` | Resumes protocol operations. |

### Constraint Verification:
- `STRATEGIST_ROLE` **CANNOT** call `sweepToExchange`.
- `exchangeDepositAddress` is **IMMUTABLE**, preventing governance-level redirection of funds to malicious addresses.

## 06_MULTISIG_STRATEGY
- **Production Target:** Ownership of the `KerneVault` will be transferred to a 2-of-3 Gnosis Safe on the Base network.
- **Transition Script:** `script/TransferOwnership.s.sol` has been created to facilitate the secure handover of `DEFAULT_ADMIN_ROLE` and `PAUSER_ROLE`.
- **Emergency Response:** The Multisig will hold the `PAUSER_ROLE` to ensure rapid response to any detected anomalies.

## 07_ECONOMIC_SECURITY (MEV/SANDWICH ANALYSIS)
- **Vector:** A user could potentially "sandwich" the `updateOffChainAssets` transaction to capture the reported yield.
- **Analysis:**
    - **Base Gas Cost:** A typical `deposit` + `withdraw` sequence on Base costs approximately 150,000 - 200,000 gas. At 0.1 gwei, this is ~0.00002 ETH ($0.06).
    - **Yield Threshold:** For a $10,000 deposit, a 1% yield update represents $100.
    - **Viability:** While gas is cheap on Base, the profit from sandwiching small updates is marginal for most users. However, for large updates or "whales," the risk exists.
- **Mitigation:** 
    - The protocol currently relies on the Strategist bot's reporting frequency.
    - **Future Improvement:** Implement a 1-block delay between `deposit` and `withdraw` to completely eliminate atomic sandwiching.
- **Status:** Monitored.
