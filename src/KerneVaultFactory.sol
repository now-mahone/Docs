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

    /// @notice Fee required to deploy a vault permissionlessly (in native ETH)
    uint256 public deploymentFee = 0.05 ether;

    /// @notice The address that receives deployment fees
    address public feeRecipient;

    /// @notice Mapping to track vaults deployed by each address
    mapping(address => address[]) public vaultsByDeployer;

    event VaultDeployed(address indexed vault, address indexed admin, string name, string symbol);
    event DeploymentFeeUpdated(uint256 newFee);
    event FeeRecipientUpdated(address newRecipient);

    constructor(
        address _implementation
    ) Ownable(msg.sender) {
        implementation = _implementation;
        feeRecipient = msg.sender;
    }

    /**
     * @notice Deploys a new bespoke vault.
     * @param asset The underlying asset (e.g., USDC, WETH).
     * @param name Name of the vault token.
     * @param symbol Symbol of the vault token.
     * @param admin Admin of the new vault.
     * @param founder Founder address for fee capture.
     * @param founderFeeBps Fee taken by the Kerne founder.
     * @param performanceFeeBps Initial performance fee for the vault.
     * @param whitelistEnabled Whether whitelisting is enabled initially.
     * @param maxTotalAssets Maximum capacity of the vault.
     */
    function deployVault(
        address asset,
        string memory name,
        string memory symbol,
        address admin,
        address founder,
        uint256 founderFeeBps,
        uint256 performanceFeeBps,
        bool whitelistEnabled,
        uint256 maxTotalAssets
    ) external payable returns (address) {
        if (msg.sender != owner()) {
            require(msg.value >= deploymentFee, "Insufficient deployment fee");
            if (msg.value > 0 && feeRecipient != address(0)) {
                (bool success, ) = payable(feeRecipient).call{value: msg.value}("");
                require(success, "Fee transfer failed");
            }
        }

        address clone = Clones.clone(implementation);

        KerneVault(clone).initialize(
            asset, name, symbol, admin, founder, founderFeeBps, performanceFeeBps, whitelistEnabled
        );

        if (maxTotalAssets > 0) {
            KerneVault(clone).setMaxTotalAssets(maxTotalAssets);
        }

        allVaults.push(clone);
        vaultsByDeployer[msg.sender].push(clone);
        
        emit VaultDeployed(clone, admin, name, symbol);

        return clone;
    }

    /**
     * @notice Allows owner to update the deployment fee.
     */
    function setDeploymentFee(uint256 _newFee) external onlyOwner {
        deploymentFee = _newFee;
        emit DeploymentFeeUpdated(_newFee);
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
