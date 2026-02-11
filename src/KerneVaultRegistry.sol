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

    /// @notice Addresses authorized to register vaults (factory, admin)
    mapping(address => bool) public authorizedRegistrars;

    event RegistrarUpdated(address indexed registrar, bool authorized);

    /**
     * @notice Sets whether an address is authorized to register vaults.
     * @dev SECURITY FIX: Prevents registry spam/poisoning with malicious fake vaults.
     */
    function setAuthorizedRegistrar(address registrar, bool authorized) external onlyOwner {
        authorizedRegistrars[registrar] = authorized;
        emit RegistrarUpdated(registrar, authorized);
    }

    /**
     * @notice Registers a new vault in the system.
     * @param vault The address of the vault (ERC-4626).
     * @param asset The underlying asset of the vault.
     * @param metadata Additional metadata (e.g., IPFS hash of vault config).
     * @dev SECURITY FIX: Restricted to owner or authorized registrars (e.g., VaultFactory).
     */
    function registerVault(address vault, address asset, string calldata metadata) external {
        require(msg.sender == owner() || authorizedRegistrars[msg.sender], "Not authorized to register");
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
