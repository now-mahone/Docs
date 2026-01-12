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

    enum VaultTier { BASIC, PRO, INSTITUTIONAL }

    struct TierConfig {
        uint256 deploymentFee;
        uint256 protocolFounderFeeBps;
        bool complianceRequired;
    }

    mapping(VaultTier => TierConfig) public tierConfigs;

    /// @notice The address that receives deployment fees
    address public feeRecipient;

    /// @notice Mapping to track vaults deployed by each address
    mapping(address => address[]) public vaultsByDeployer;

    event VaultDeployed(address indexed vault, address indexed admin, string name, string symbol, VaultTier tier);
    event TierConfigUpdated(VaultTier tier, uint256 fee, uint256 founderFeeBps, bool compliance);
    event FeeRecipientUpdated(address newRecipient);

    constructor(
        address _implementation
    ) Ownable(msg.sender) {
        implementation = _implementation;
        feeRecipient = msg.sender;

        // Initialize default tiers
        tierConfigs[VaultTier.BASIC] = TierConfig(0.05 ether, 1000, false); // 10% of performance fee
        tierConfigs[VaultTier.PRO] = TierConfig(0.2 ether, 750, true);      // 7.5% of performance fee
        tierConfigs[VaultTier.INSTITUTIONAL] = TierConfig(1 ether, 500, true); // 5% of performance fee
    }

    /**
     * @notice Deploys a new bespoke vault with a specific tier.
     * @param asset The underlying asset (e.g., USDC, WETH).
     * @param name Name of the vault token.
     * @param symbol Symbol of the vault token.
     * @param admin Admin of the new vault.
     * @param performanceFeeBps Initial performance fee for the vault.
     * @param whitelistEnabled Whether whitelisting is enabled initially.
     * @param maxTotalAssets Maximum capacity of the vault.
     * @param tier The tier of the vault being deployed.
     */
    function deployVault(
        address asset,
        string calldata name,
        string calldata symbol,
        address admin,
        uint256 performanceFeeBps,
        bool whitelistEnabled,
        uint256 maxTotalAssets,
        VaultTier tier
    ) external payable returns (address) {
        TierConfig storage config = tierConfigs[tier];

        if (msg.sender != owner()) {
            uint256 fee = config.deploymentFee;
            require(msg.value >= fee, "Insufficient deployment fee");
            if (fee > 0) {
                (bool success, ) = feeRecipient.call{value: fee}("");
                require(success, "Fee transfer failed");
            }
        }

        address clone = Clones.clone(implementation);

        KerneVault(clone).initialize(
            asset, 
            name, 
            symbol, 
            admin, 
            owner(), // Kerne Protocol Treasury
            config.protocolFounderFeeBps, 
            performanceFeeBps, 
            whitelistEnabled || config.complianceRequired
        );

        if (maxTotalAssets > 0) {
            KerneVault(clone).setMaxTotalAssets(maxTotalAssets);
        }

        allVaults.push(clone);
        vaultsByDeployer[msg.sender].push(clone);
        
        emit VaultDeployed(clone, admin, name, symbol, tier);

        return clone;
    }

    /**
     * @notice Allows owner to update tier configurations.
     */
    function setTierConfig(
        VaultTier tier,
        uint256 deploymentFee,
        uint256 protocolFounderFeeBps,
        bool complianceRequired
    ) external onlyOwner {
        tierConfigs[tier] = TierConfig(deploymentFee, protocolFounderFeeBps, complianceRequired);
        emit TierConfigUpdated(tier, deploymentFee, protocolFounderFeeBps, complianceRequired);
    }

    /**
     * @notice Allows owner to update the fee recipient.
     */
    function setFeeRecipient(address _newRecipient) external onlyOwner {
        feeRecipient = _newRecipient;
        emit FeeRecipientUpdated(_newRecipient);
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

    function getUserVaults(address user) external view returns (address[] memory) {
        return vaultsByDeployer[user];
    }
}
