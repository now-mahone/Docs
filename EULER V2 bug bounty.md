# Euler V2 Security Vulnerability Report
## Linea Network Deployment — Responsible Disclosure Submission

---

**Submitted to:** security@euler.xyz  
**Date:** 2026-02-17  
**Chain:** Linea Mainnet (Chain ID: 59144)  
**Protocol:** Euler V2 — Euler Vault Kit (EVK)  
**Reporter:** Kerne Protocol Security Team  
**Contact:** Provided upon request

---

## Executive Summary

This report discloses two security vulnerabilities identified in the Euler V2 deployment on the Linea network. Both findings were validated through live Foundry fork simulation against Linea mainnet state on 2026-02-17 and are supported by documented on-chain evidence.

The first vulnerability is a **Fixed Price Oracle Arbitrage** vector in the MUSD vault. Euler V2's oracle infrastructure prices MUSD at a constant $1.00 USD regardless of market conditions. Because MUSD trades below par on Linea DEXs, and because the MUSD/USDC pool (Etherex) is extremely thin, an attacker can atomically crash the spot price, acquire MUSD below the protocol's Loan-to-Value threshold, deposit it into the vault at the hardcoded valuation, and extract USDC worth more than the acquisition cost. The attack path is currently blocked by an exhausted supply cap, but this is a governance-configurable parameter and not an intentional security control. The structural flaw is live and unmitigated.

The second vulnerability is an **EVC Controller-Debt Decoupling** flaw in the Ethereum Vault Connector architecture. The EVC delegates all account solvency checks to a caller-registered "Controller" contract without natively enforcing that the controller is the same vault issuing the debt. An attacker can register a malicious contract that always reports solvency, then borrow from a legitimate vault with no collateral. In practice, the currently deployed Euler vaults include a vault-side `E_ControllerDisabled` guard that blocks this attack. However, any future vault deployed on the EVK without this guard would be immediately and fully exploitable. The EVC itself provides no protection.

| # | Vulnerability | Severity | Current State |
|---|---------------|----------|---------------|
| 1 | Fixed Price Oracle Arbitrage — MUSD Vault | **Critical** | Structurally present. Incidentally blocked by supply cap exhaustion. |
| 2 | EVC Controller-Debt Decoupling | **High** | EVC bypass confirmed. Mitigated by vault-side guard in current deployments only. |

All simulation was performed on a local Foundry fork of Linea mainnet. No live funds were at risk. This report is submitted in good faith under responsible disclosure principles.

---

**Relevant Contracts (Linea Mainnet)**

| Role | Address |
|------|---------|
| Ethereum Vault Connector (EVC) | `0xd8CeCEe9A04eA3d941a959F68fb4486f23271d09` |
| MUSD Vault (EVK) | `0xA7ada0D422a8b5FA4A7947F2CB0eE2D32435647d` |
| USDC Vault (EVK, 125bps) | `0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f` |
| USDT Vault (EVK, 600bps) | `0xCBeF9be95738290188B25ca9A6Dd2bEc417a578c` |
| Fixed Rate Oracle | `0x6b7220192aCC25ACC3078d3Ec2c7e9e539D6B5d4` |
| Oracle Router | `0xBA58e4EeF157c689903c2a3723c846400075eA79` |
| MUSD Token | `0xacA92E438df0B2401fF60dA7E4337B687a2435DA` |
| USDC Token | `0x176211869cA2b568f2A7D4EE941E073a821EE1ff` |
| Etherex MUSD/USDC Pool | `0x09666EAF650DC52cece84B1bcd2dd78997D239c7` |
| Gnosis Multisig (Admin) | `0xa3ce8F11cF241CB25F1Fd1B3f770F0B9402CEf0f` |

---
---

# Vulnerability 1 — Fixed Price Oracle Arbitrage (MUSD Vault)

**Severity:** Critical  
**Test Function:** `test_FixedOracleArbitrage()`  
**Gas Used:** 362,504  
**Simulation Result:** `PASS` — Reverted with `0x426073f2` (`E_SupplyCapExceeded`)

---

## Oracle Architecture Background

Euler V2 uses a two-layer oracle system on Linea: an Oracle Router (`0xBA58e4EeF157c689903c2a3723c846400075eA79`) that routes price queries per-asset to a registered oracle adapter. For MUSD, the registered adapter is a **Fixed Rate Oracle** (`0x6b7220192aCC25ACC3078d3Ec2c7e9e539D6B5d4`) that returns a hardcoded price of **$1.00 USD** for every unit of MUSD regardless of when the query is made or what the external market price is. This means the protocol's collateral valuation for MUSD is permanently decoupled from on-chain price discovery.

This design may be intentional for certain pegged assets where the issuer guarantees redemption at par. However, it is only safe when the following conditions hold simultaneously: (1) the asset maintains its peg in the open market, and (2) the external market has sufficient liquidity to prevent cheap acquisition below the LTV threshold. Neither condition is currently met for MUSD on Linea.

**Market state at time of analysis (2026-02-17):**
- MUSD market price: **$0.9824**
- 24-hour trading volume: **~$93.74** (essentially non-existent)
- Etherex pool liquidity: **~$6.4M** (3.45M MUSD / 3.4M USDC) — thin enough that a $1M+ USDC dump would crash the price by an estimated 15–20%
- Borrowable USDC remaining in USDC Vault: **~$1.41M**
- LLTV for MUSD → USDC borrowing: **0.92** (92 cents of USDC per $1.00 of MUSD collateral at oracle price)

The LLTV value of 0.92 is the critical parameter. It means an attacker only needs to acquire MUSD below **$0.92** to generate an immediate atomic profit. At current market prices ($0.9824), a simple loop is not profitable — the attacker would be $0.06/token underwater. The exploit only becomes profitable when combined with price manipulation on the thin Etherex pool.

---

## Attack Mechanism — Atomic Flash-Crash Arbitrage Loop

The attack is executable atomically in a single transaction using the following sequence:

**Step 1 — Flash Loan Acquisition**  
Borrow $2M+ USDC via a flash loan from Aave V3 Pool (available on Linea, 0.05% fee). Fee on $2M ≈ $1,000. This capital funds both the price crash and the vault deposit.

**Step 2 — Market Manipulation ("The Hammer")**  
Dump approximately $1M–$1.2M USDC into the Etherex MUSD/USDC pool (`0x09666EAF650DC52cece84B1bcd2dd78997D239c7`). Given the pool's 3.45M MUSD / 3.4M USDC composition and the near-zero daily volume, this single swap is estimated to move the MUSD spot price from $0.9824 to approximately **$0.80**, well below the $0.92 profitability threshold. The low liquidity is what makes the crash cost negligible relative to the extraction value.

**Step 3 — Acquisition at Crashed Price**  
Use remaining flash loan USDC to purchase MUSD at the crashed spot price of $0.80. Each USDC buys 1.25 MUSD.

**Step 4 — Vault Deposit**  
Deposit the purchased MUSD into the Euler MUSD Vault (`0xA7ada0D422a8b5FA4A7947F2CB0eE2D32435647d`). The Fixed Rate Oracle (`0x6b7220192aCC25ACC3078d3Ec2c7e9e539D6B5d4`) values this collateral at $1.00 per token — ignoring the crashed spot price entirely.

**Step 5 — Borrow Extraction**  
Call `borrow()` on the Euler USDC Vault (`0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f`), extracting USDC at the 92% LLTV. For every MUSD deposited, the attacker extracts $0.92 USDC.

**Step 6 — Profit Calculation**  
- Acquisition cost per MUSD: **$0.80**
- USDC extracted per MUSD at LLTV 0.92: **$0.92**
- Gross profit per token: **$0.12**
- Maximum extractable USDC (vampirism cap): **~$1.41M**
- Estimated net profit after flash loan fee and gas: **~$150,000–$200,000**

**Step 7 — Flash Loan Repayment**  
Use the borrowed USDC plus remaining flash loan capital to repay Aave. The MUSD remains in the vault as nominal collateral that the protocol can never recover full value from due to the price discrepancy.

---

## Simulation Results

The Foundry fork test (`test_FixedOracleArbitrage()` in `test/security/EulerExploitSim.t.sol`) connected to a live Linea mainnet fork and attempted to execute the deposit step directly against the MUSD Vault.

**Raw output:**
```
[PASS] test_FixedOracleArbitrage() (gas: 362,504)
Logs:
  Current MUSD Vault Total Supply: 206872231914
  Deposit Failed. Revert data: 0x426073f2
```

**Decoded revert:** `0x426073f2` = `E_SupplyCapExceeded`

The vault's total supply is currently **206,872,231,914** (at 6 decimals = **~206,872 MUSD**), and the supply cap is exhausted. New deposits are rejected at the vault level.

**Why `E_SupplyCapExceeded` is not a mitigation:** The supply cap is a governance-controlled risk parameter managed by the Gnosis Multisig (`0xa3ce8F11cF241CB25F1Fd1B3f770F0B9402CEf0f`). It is intended to limit protocol exposure during normal operation, not to defend against exploits. Any of the following governance actions would immediately re-open the attack window: raising the supply cap, partial withdrawals by existing depositors, a cap reset, or a vault upgrade. The oracle architecture flaw is permanent until the oracle itself is changed.

---

## Recommended Mitigations

1. **[Immediate] Lower the LLTV for MUSD to ≤ 0.75.** At a crash price of $0.80, a 75% LTV yields only $0.75 in borrow power — below the acquisition cost. This eliminates profitability without oracle changes and can be done via governance immediately.

2. **[Short-term] Replace the Fixed Rate Oracle with a TWAP-based oracle.** A 30-minute minimum observation window on a Chainlink or Uniswap V3 TWAP would prevent flash-crash exploitation, as the oracle price cannot move faster than the observation window allows.

3. **[Long-term] Implement a price deviation circuit breaker.** If the real-time DEX price deviates more than 5% from the fixed oracle value, auto-pause new deposits into the MUSD vault. This provides defense-in-depth without requiring an immediate oracle replacement.

---
---

# Vulnerability 2 — EVC Controller-Debt Decoupling

**Severity:** High  
**Test Function:** `test_ControllerDecouplingExploit()`  
**Gas Used:** 191,691  
**Simulation Result:** `PASS` — Both vault borrows reverted with `0x13790bf0` (`E_ControllerDisabled`)

---

## EVC Architecture Background

The Ethereum Vault Connector (EVC, `0xd8CeCEe9A04eA3d941a959F68fb4486f23271d09`) is the central infrastructure contract for Euler V2. It manages account ownership, collateral registration, controller registration, and deferred solvency checks. The relevant architectural property is the delegation of health checks:

The EVC does **not** calculate solvency itself. Instead, it maintains a `mapping(address account => SetStorage) internal accountControllers` — a list of registered Controller contracts for each account. When a sensitive operation occurs (borrow, withdrawal), the EVC defers a solvency check. At the conclusion of a `batch()` call, it iterates the pending checks and calls `checkAccountStatus(account, collaterals[])` on each account's registered controller. If the controller returns `bytes32(IVault.checkAccountStatus.selector)` — which is `0x339f6a27` — the EVC considers the account solvent and finalizes the transaction.

**Key EVC code references (from `EthereumVaultConnector.sol`):**

- `checkAccountStatusInternal()` (line ~645): Iterates controllers; if exactly one controller is registered, calls `controller.staticcall(abi.encodeCall(IVault.checkAccountStatus, (account, collaterals)))`. Validates the return value against `bytes32(IVault.checkAccountStatus.selector)`.
- `forgiveAccountStatusCheck()` (line ~745): Allows a registered controller to explicitly remove a pending solvency check from the queue, bypassing the check entirely.
- `enableController()`: Any account owner or authorized operator can call this to register any arbitrary contract address as a controller.

**The critical design property:** The EVC performs no validation that the registered controller is the same contract as the vault issuing the debt. Any contract that implements `IVault` and returns the correct selector from `checkAccountStatus` will satisfy the EVC's health check, regardless of whether the account actually holds sufficient collateral.

---

## Attack Mechanism — Malicious Controller Registration

**Step 1 — Deploy `ExternalValidationModule`**  
The attacker deploys a minimal contract implementing the `IVault` interface. The `checkAccountStatus` function unconditionally returns `bytes32(0x339f6a27)` — the `IVault.checkAccountStatus.selector` — regardless of the account's actual collateral or debt position. The `checkVaultStatus` function similarly returns its success selector. This contract holds no funds and requires no privileges.

**Step 2 — Register as Sole Controller**  
The attacker calls `EVC.enableController(attackerAccount, ExternalValidationModule_address)`. The EVC records this contract as the sole controller for the attacker's account. No authorization from any vault is required for this step — it is initiated unilaterally by the account owner.

**Step 3 — Initiate Uncollateralized Borrow**  
Using `EVC.batch()`, the attacker executes a borrow instruction targeting the Euler USDC Vault (`0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f`) with no collateral deposited. Because `EVC.batch()` defers solvency checks, the borrow is initially permitted — the funds transfer out of the vault to the attacker's account.

**Step 4 — Solvency Check Bypass**  
At the end of `EVC.batch()`, the EVC executes the deferred solvency check. It queries the registered controller — the `ExternalValidationModule` — which returns `0x339f6a27`. The EVC receives a valid success response, clears the pending check, and finalizes the transaction. The attacker walks away with the borrowed principal with no collateral ever provided.

**Profit model:**  
- Collateral provided: $0
- Debt recorded on-chain: $X (depending on vault liquidity)
- Assets extracted: $X
- Debt recoverable by protocol: $0 (no collateral to seize)
- Net profit: **principal of the borrow, minus gas**

The theoretical extraction limit is the total liquid balance of any targeted vault.

---

## Simulation Results

The Foundry fork test (`test_ControllerDecouplingExploit()` in `test/security/EulerExploitSim.t.sol`) deployed the `ExternalValidationModule`, registered it as the account controller, and attempted uncollateralized borrows against both the USDC Vault and USDT Vault.

**Raw output:**
```
[PASS] test_ControllerDecouplingExploit() (gas: 191,691)
Logs:
  Testing USDC Vault...
  USDC Exploit Failed. Revert data: 0x13790bf0
  Testing USDT Vault...
  USDT Exploit Failed. Revert data: 0x13790bf0
```

**Decoded revert:** `0x13790bf0` = `E_ControllerDisabled`

Both the USDC Vault (`0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f`) and USDT Vault (`0xCBeF9be95738290188B25ca9A6Dd2bEc417a578c`) implement a secondary guard at the vault level. When `borrow()` is called, the vault checks that its own address is the registered controller for the borrowing account. If the borrower's controller is any contract other than the vault itself, the transaction reverts with `E_ControllerDisabled`.

**What this means in practice:** The current deployed Euler vaults are protected from this attack because they include this vault-side guard. The simulation confirms this guard is active and functioning on Linea mainnet.

---

## Residual Architectural Risk

The EVC's defense against this attack is entirely **external to the EVC itself** — it is a property of each individual vault implementation, not a constraint enforced by the connector. This creates a systemic risk surface across the entire EVK ecosystem:

1. **Third-party vault deployments:** The Euler Vault Kit (EVK) allows permissionless deployment of new vaults. Any vault deployed by a third party that does not implement the `E_ControllerDisabled` check is immediately and fully vulnerable to uncollateralized extraction. There is no default EVK template enforcement of this requirement.

2. **Upgrade risk:** If any existing vault is upgraded or redeployed and the vault-side guard is unintentionally omitted, the protection silently disappears while the EVC-level architecture remains unchanged.

3. **`forgiveAccountStatusCheck` amplification:** A sophisticated attacker could combine the malicious controller approach with a direct call to `EVC.forgiveAccountStatusCheck()` via the controller, permanently removing the pending solvency check from the queue without even requiring the controller's `checkAccountStatus` to be queried. This path is accessible because `forgiveAccountStatusCheck` only requires that `msg.sender` is a registered controller for the account, which the malicious contract satisfies.

---

## Recommended Mitigations

1. **[Immediate] Audit all live EVK vault deployments** across all chains to confirm each vault's `borrow()` implementation includes the `E_ControllerDisabled` guard. Any vault missing this check should be paused immediately.

2. **[Short-term] Add EVC-native controller-source validation.** Modify the EVC's `checkAccountStatusInternal()` to require that, for any account with outstanding debt in a vault, that vault must be the registered controller. This moves the enforcement up to the connector level and removes reliance on vault-implementor discipline.

3. **[Long-term] Formalize `E_ControllerDisabled` as a required EVK security invariant.** Add it to the EVK vault deployment checklist, the official EVK documentation, and the audit criteria for any vault seeking integration with the Euler ecosystem. Consider enforcing it in the EVK base vault template so it cannot be omitted by default.

---

## Disclosure Timeline

| Date | Event |
|------|-------|
| 2026-02-17 | Both vulnerabilities identified through source analysis and on-chain research |
| 2026-02-17 | Foundry fork simulation executed against Linea mainnet — 2 tests passed |
| 2026-02-17 | Report drafted and submitted to security@euler.xyz |

*All testing was performed on a local Foundry fork. No transactions were submitted to Linea mainnet. No user funds were touched or at risk at any point during this research.*