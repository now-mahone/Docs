// Created: 2026-02-03
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title skUSD (Staked kUSD)
 * @author Kerne Protocol
 * @notice skUSD is an ERC-4626 vault that earns the basis yield from Kerne's delta-neutral strategy.
 *         It replicates Ethena's sUSDe model but for the Kerne ecosystem.
 */
contract skUSD is ERC4626, AccessControl {
    using SafeERC20 for ERC20;

    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    /**
     * @notice Constructor for skUSD.
     * @param _asset The kUSD token address.
     * @param _admin The default admin address.
     */
    constructor(ERC20 _asset, address _admin) 
        ERC4626(_asset) 
        ERC20("Staked Kerne Synthetic Dollar", "skUSD") 
    {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(STRATEGIST_ROLE, _admin);
    }

    /**
     * @notice Distributes yield to skUSD holders.
     * @dev This function is called by the bot/strategist to push captured basis yield into the vault.
     * @param amount The amount of kUSD to distribute as yield.
     */
    function distributeYield(uint256 amount) external onlyRole(STRATEGIST_ROLE) {
        ERC20(asset()).safeTransferFrom(msg.sender, address(this), amount);
        // The totalAssets() increases, raising the share price for all skUSD holders.
    }

    /**
     * @dev Overrides totalAssets to include the kUSD held in this contract.
     */
    function totalAssets() public view override returns (uint256) {
        return ERC20(asset()).balanceOf(address(this));
    }
}