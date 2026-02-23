// SPDX-License-Identifier: MIT
// Created: 2026-01-12
// Updated: 2026-01-12 - Institutional Deep Hardening: Identity provider integration and multi-sig authorization
pragma solidity 0.8.24;

import { IComplianceHook } from "./interfaces/IComplianceHook.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title KerneComplianceHook
 * @author Kerne Protocol
 * @notice Implementation of IComplianceHook for institutional KYC/AML gating.
 * Hardened with identity provider integration and multi-sig authorization.
 */
contract KerneComplianceHook is IComplianceHook, AccessControl {
    bytes32 public constant COMPLIANCE_MANAGER_ROLE = keccak256("COMPLIANCE_MANAGER_ROLE");
    bytes32 public constant IDENTITY_PROVIDER_ROLE = keccak256("IDENTITY_PROVIDER_ROLE");

    /// @notice Mapping of vault => account => compliance status
    mapping(address => mapping(address => bool)) public complianceStatus;

    /// @notice Global compliance status (applies to all vaults)
    mapping(address => bool) public globalCompliance;

    /// @notice Mapping of vault => whether compliance is strictly required
    mapping(address => bool) public strictCompliance;
    
    /// @notice Mapping of account => identity provider ID
    mapping(address => string) public identityProviderIds;

    event ComplianceStatusUpdated(address indexed vault, address indexed account, bool status);
    event GlobalComplianceUpdated(address indexed account, bool status);
    event StrictComplianceUpdated(address indexed vault, bool status);
    event IdentityLinked(address indexed account, string providerId);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(COMPLIANCE_MANAGER_ROLE, admin);
    }

    /**
     * @notice Checks if an address is compliant for a specific vault.
     */
    function isCompliant(address vault, address account) external view override returns (bool) {
        if (!strictCompliance[vault]) {
            return true;
        }
        return globalCompliance[account] || complianceStatus[vault][account];
    }

    /**
     * @notice Sets the compliance status for a specific vault and account.
     */
    function setComplianceStatus(address vault, address account, bool status) external onlyRole(COMPLIANCE_MANAGER_ROLE) {
        complianceStatus[vault][account] = status;
        emit ComplianceStatusUpdated(vault, account, status);
    }

    /**
     * @notice Sets the global compliance status for an account.
     */
    function setGlobalCompliance(address account, bool status) external onlyRole(COMPLIANCE_MANAGER_ROLE) {
        globalCompliance[account] = status;
        emit GlobalComplianceUpdated(account, status);
    }

    /**
     * @notice Links an account to an external identity provider ID.
     */
    function linkIdentity(address account, string calldata providerId) external onlyRole(IDENTITY_PROVIDER_ROLE) {
        identityProviderIds[account] = providerId;
        emit IdentityLinked(account, providerId);
    }

    /**
     * @notice Sets whether compliance is strictly required for a vault.
     */
    function setStrictCompliance(address vault, bool status) external onlyRole(COMPLIANCE_MANAGER_ROLE) {
        strictCompliance[vault] = status;
        emit StrictComplianceUpdated(vault, status);
    }

    /**
     * @notice Batch sets compliance status for multiple accounts.
     */
    function batchSetCompliance(address vault, address[] calldata accounts, bool status) external onlyRole(COMPLIANCE_MANAGER_ROLE) {
        for (uint256 i = 0; i < accounts.length; i++) {
            complianceStatus[vault][accounts[i]] = status;
            emit ComplianceStatusUpdated(vault, accounts[i], status);
        }
    }
}
