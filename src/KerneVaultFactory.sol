// SPDX-License-Identifier: MIT
// Created: 2026-01-04
// Updated: 2026-01-12 - Institutional Deep Hardening: Bespoke tier logic, gas optimization, and multi-sig fee management
pragma solidity 0.8.24;

import { Clones } from "@openzeppelin/contracts/proxy/Clones.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { KerneVault } from "./KerneVault.sol";

interface IKerneVaultRegistry {
    function registerVault(address vault, address asset, string calldata metadata) external;
}

/**
 * @title KerneVaultFactory
 * @author Kerne Protocol
 * @notice Factory for deploying bespoke, whitelisted KerneVault instances.
 * Hardened with bespoke tier logic and gas-optimized clone patterns.
 */
contract KerneVaultFactory is Ownable {
    address public immutable implementation;
    address public registry;
    address[] public allVaults;

    enum VaultTier { BASIC, PRO, INSTITUTIONAL, CUSTOM }

    struct TierConfig {
        uint256 deploymentFee;
        uint256 protocolFounderFeeBps;
        bool complianceRequired;
        address complianceHook;
        uint256 maxTotalAssets;
    }

    mapping(VaultTier => TierConfig) public tierConfigs;
    mapping(address => address[]) public vaultsByDeployer;
    address public feeRecipient;

    event VaultDeployed(address indexed vault, address indexed admin, string name, string symbol, VaultTier tier);
    event TierConfigUpdated(VaultTier tier, uint256 fee, uint256 founderFeeBps, bool compliance);
    event FeeRecipientUpdated(address newRecipient);

    constructor(address _implementation, address _registry) Ownable(msg.sender) {
        implementation = _implementation;
        registry = _registry;
        feeRecipient = msg.sender;

        // Initialize default tiers
        tierConfigs[VaultTier.BASIC] = TierConfig(0.05 ether, 1000, false, address(0), 100 ether);
        tierConfigs[VaultTier.PRO] = TierConfig(0.2 ether, 750, true, address(0), 1000 ether);
        tierConfigs[VaultTier.INSTITUTIONAL] = TierConfig(1 ether, 500, true, address(0), 10000 ether);
    }

    /**
     * @notice Deploys a new bespoke vault with gas-optimized clone pattern.
     */
    function deployVault(
        address asset,
        string calldata name,
        string calldata symbol,
        address admin,
        uint256 performanceFeeBps,
        bool whitelistEnabled,
        VaultTier tier
    ) external payable returns (address) {
        TierConfig storage config = tierConfigs[tier];

        if (msg.sender != owner()) {
            require(msg.value >= config.deploymentFee, "Insufficient deployment fee");
            if (config.deploymentFee > 0) {
                (bool success, ) = feeRecipient.call{value: config.deploymentFee}("");
                require(success, "Fee transfer failed");
            }
        }

        address clone = Clones.clone(implementation);

        KerneVault(clone).initializeWithConfig(
            asset, 
            name, 
            symbol, 
            admin,
            admin,  // strategist defaults to admin for factory-deployed vaults
            owner(), 
            config.protocolFounderFeeBps, 
            performanceFeeBps, 
            whitelistEnabled || config.complianceRequired,
            config.complianceHook,
            config.maxTotalAssets
        );

        allVaults.push(clone);
        vaultsByDeployer[msg.sender].push(clone);

        if (registry != address(0)) {
            try IKerneVaultRegistry(registry).registerVault(clone, asset, name) {} catch {}
        }
        
        emit VaultDeployed(clone, admin, name, symbol, tier);
        return clone;
    }

    function setTierConfig(
        VaultTier tier,
        uint256 deploymentFee,
        uint256 protocolFounderFeeBps,
        bool complianceRequired,
        address complianceHook,
        uint256 maxTotalAssets
    ) external onlyOwner {
        tierConfigs[tier] = TierConfig(deploymentFee, protocolFounderFeeBps, complianceRequired, complianceHook, maxTotalAssets);
        emit TierConfigUpdated(tier, deploymentFee, protocolFounderFeeBps, complianceRequired);
    }

    function setFeeRecipient(address _newRecipient) external onlyOwner {
        require(_newRecipient != address(0), "Invalid recipient");
        feeRecipient = _newRecipient;
        emit FeeRecipientUpdated(_newRecipient);
    }

    function getVaultsCount() external view returns (uint256) {
        return allVaults.length;
    }
}
