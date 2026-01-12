// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title KerneVaultRegistry
 * @notice A central registry for all Kerne-powered vaults to enable aggregator discovery.
 */
contract KerneVaultRegistry is Ownable {
    event VaultRegistered(address indexed vault, address indexed asset, string metadata);

    address[] public allVaults;
    mapping(address => bool) public isRegistered;
    mapping(address => address[]) public vaultsByAsset;

    constructor() Ownable(msg.sender) {}

    /**
     * @notice Registers a new vault in the system.
     * @param vault The address of the vault (ERC-4626).
     * @param asset The underlying asset of the vault.
     * @param metadata Additional metadata (e.g., IPFS hash of vault config).
     */
    function registerVault(address vault, address asset, string calldata metadata) external {
        // In a production environment, we might restrict this to the Factory or Admin
        // For the "Trojan Horse" strategy, we allow anyone to register if it meets our interface
        require(!isRegistered[vault], "Already registered");
        
        isRegistered[vault] = true;
        allVaults.push(vault);
        vaultsByAsset[asset].push(vault);

        emit VaultRegistered(vault, asset, metadata);
    }

    function getVaultCount() external view returns (uint256) {
        return allVaults.length;
    }

    function getVaultsByAsset(address asset) external view returns (address[] memory) {
        return vaultsByAsset[asset];
    }
}
