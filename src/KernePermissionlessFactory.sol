// SPDX-License-Identifier: MIT
// Created: 2026-01-09
pragma solidity 0.8.24;

import { Clones } from "@openzeppelin/contracts/proxy/Clones.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KernePermissionlessFactory
 * @author Kerne Protocol
 * @notice Permissionless factory for deploying bespoke KerneVault instances.
 * @dev Allows anyone to launch a hedge fund with a standardized fee structure.
 */
contract KernePermissionlessFactory is Ownable {
    using SafeERC20 for IERC20;

    address public immutable implementation;
    address public protocolTreasury;
    uint256 public deploymentFee; // Fee in native ETH to deploy a vault
    
    address[] public allVaults;
    mapping(address => address[]) public userVaults;

    event VaultDeployed(address indexed vault, address indexed admin, string name, string symbol);
    event DeploymentFeeUpdated(uint256 newFee);
    event TreasuryUpdated(address newTreasury);

    constructor(
        address _implementation,
        address _protocolTreasury,
        uint256 _deploymentFee
    ) Ownable(msg.sender) {
        implementation = _implementation;
        protocolTreasury = _protocolTreasury;
        deploymentFee = _deploymentFee;
    }

    /**
     * @notice Deploys a new bespoke vault permissionlessly.
     * @param asset The underlying asset for the vault.
     * @param name Name of the vault token.
     * @param symbol Symbol of the vault token.
     * @param performanceFeeBps Initial performance fee for the vault (max 20%).
     * @param whitelistEnabled Whether whitelisting is enabled initially.
     */
    function deployVault(
        address asset,
        string memory name,
        string memory symbol,
        uint256 performanceFeeBps,
        bool whitelistEnabled
    ) external payable returns (address) {
        require(msg.value >= deploymentFee, "Insufficient deployment fee");
        require(performanceFeeBps <= 2000, "Performance fee too high");

        address clone = Clones.clone(implementation);

        // Initialize the vault
        // msg.sender becomes the admin
        // protocolTreasury becomes the founder for fee capture
        // Default founder fee is 10% of performance fee (100 bps of gross yield if perf fee is 1000)
        KerneVault(clone).initialize(
            asset, 
            name, 
            symbol, 
            msg.sender, 
            protocolTreasury, 
            1000, // 10% of performance fee goes to Kerne Protocol
            performanceFeeBps, 
            whitelistEnabled
        );

        allVaults.push(clone);
        userVaults[msg.sender].push(clone);

        // Transfer deployment fee to treasury
        if (msg.value > 0) {
            (bool success, ) = protocolTreasury.call{value: msg.value}("");
            require(success, "Fee transfer failed");
        }

        emit VaultDeployed(clone, msg.sender, name, symbol);

        return clone;
    }

    // --- Admin Functions ---

    function setDeploymentFee(uint256 _newFee) external onlyOwner {
        deploymentFee = _newFee;
        emit DeploymentFeeUpdated(_newFee);
    }

    function setTreasury(address _newTreasury) external onlyOwner {
        require(_newTreasury != address(0), "Invalid treasury");
        protocolTreasury = _newTreasury;
        emit TreasuryUpdated(_newTreasury);
    }

    // --- View Functions ---

    function getVaultsCount() external view returns (uint256) {
        return allVaults.length;
    }

    function getUserVaults(address user) external view returns (address[] memory) {
        return userVaults[user];
    }
}
