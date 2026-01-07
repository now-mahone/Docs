// SPDX-License-Identifier: MIT
// Created: 2026-01-04
pragma solidity 0.8.24;

import { Clones } from "@openzeppelin/contracts/proxy/Clones.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KerneVaultFactory
 * @author Kerne Protocol
 * @notice Factory for deploying bespoke, whitelisted KerneVault instances.
 */
contract KerneVaultFactory is Ownable {
    address public immutable implementation;
    address[] public allVaults;

    event VaultDeployed(address indexed vault, address indexed admin, string name, string symbol);

    constructor(
        address _implementation
    ) Ownable(msg.sender) {
        implementation = _implementation;
    }

    /**
     * @notice Deploys a new bespoke vault.
     * @param name Name of the vault token.
     * @param symbol Symbol of the vault token.
     * @param admin Admin of the new vault.
     * @param founder Founder address for fee capture.
     * @param founderFeeBps Fee taken by the Kerne founder.
     * @param performanceFeeBps Initial performance fee for the vault.
     * @param whitelistEnabled Whether whitelisting is enabled initially.
     */
    function deployVault(
        address asset,
        string memory name,
        string memory symbol,
        address admin,
        address founder,
        uint256 founderFeeBps,
        uint256 performanceFeeBps,
        bool whitelistEnabled
    ) external onlyOwner returns (address) {
        address clone = Clones.clone(implementation);
        KerneVault(clone).initialize(asset, name, symbol, admin, founder, founderFeeBps);

        // Set additional bespoke configurations
        KerneVault(clone).setPerformanceFee(performanceFeeBps);
        KerneVault(clone).setWhitelistEnabled(whitelistEnabled);

        allVaults.push(clone);
        emit VaultDeployed(clone, admin, name, symbol);

        return clone;
    }

    /**
     * @notice Updates the founder fee for a specific vault.
     * @param vault The address of the vault.
     * @param newFeeBps The new founder fee in basis points.
     */
    function setVaultFounderFee(address vault, uint256 newFeeBps) external onlyOwner {
        KerneVault(vault).setFounderFee(newFeeBps);
    }

    function getVaultsCount() external view returns (uint256) {
        return allVaults.length;
    }
}
