// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { IKerneLSTHook } from "./interfaces/IKerneLSTHook.sol";

/**
 * @title KerneLSTHook
 * @author Kerne Protocol
 * @notice Tracks accrued LST yield (shadow yield) that is not yet reflected in on-chain balances.
 * This contract acts as a verification node for KerneVault to report off-chain/accrued assets.
 */
contract KerneLSTHook is IKerneLSTHook, AccessControl {
    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    /// @notice Mapping of vault => accrued shadow yield (e.g., LST rebases not yet realized)
    mapping(address => uint256) public shadowYield;

    event ShadowYieldUpdated(address indexed vault, uint256 oldAmount, uint256 newAmount);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    /**
     * @notice Updates the shadow yield for a specific vault.
     * @dev Restricted to STRATEGIST_ROLE.
     * @param vault The address of the KerneVault.
     * @param amount The new accrued shadow yield amount.
     */
    function updateShadowYield(address vault, uint256 amount) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAmount = shadowYield[vault];
        shadowYield[vault] = amount;
        emit ShadowYieldUpdated(vault, oldAmount, amount);
    }

    /**
     * @notice Returns the verified assets (shadow yield) for a vault.
     * @dev Called by KerneVault.totalAssets() via staticcall.
     * @param vault The address of the vault to check.
     * @return The amount of shadow yield for the vault.
     */
    function getVerifiedAssets(address vault) external view override returns (uint256) {
        return shadowYield[vault];
    }
}
