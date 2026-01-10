// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import { IComplianceHook } from "./interfaces/IComplianceHook.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title KerneMockCompliance
 * @author Kerne Protocol
 * @notice A mock compliance hook for testing institutional whitelisting and KYC flows.
 */
contract KerneMockCompliance is IComplianceHook, Ownable {
    mapping(address => mapping(address => bool)) public complianceStatus;

    constructor() Ownable(msg.sender) {}

    /**
     * @notice Sets the compliance status for an account on a specific vault.
     */
    function setComplianceStatus(address vault, address account, bool status) external onlyOwner {
        complianceStatus[vault][account] = status;
    }

    /**
     * @notice Checks if an address is compliant for a specific vault.
     */
    function isCompliant(address vault, address account) external view override returns (bool) {
        return complianceStatus[vault][account];
    }
}
