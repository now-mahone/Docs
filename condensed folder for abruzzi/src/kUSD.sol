// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { ERC20Permit } from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import { ERC20Burnable } from "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";

/**
 * @title kUSD
 * @author Kerne Protocol
 * @notice The Kerne Synthetic Dollar (kUSD) is a delta-neutral stablecoin.
 *         It is minted against KerneVault shares (kLP).
 */
contract kUSD is ERC20, ERC20Permit, ERC20Burnable, AccessControl {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    constructor(address defaultAdmin) ERC20("Kerne Synthetic Dollar", "kUSD") ERC20Permit("Kerne Synthetic Dollar") {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(MINTER_ROLE, defaultAdmin);
    }

    /**
     * @notice Mints kUSD to a specific address.
     * @param to The address to receive the minted kUSD.
     * @param amount The amount of kUSD to mint.
     */
    function mint(address to, uint256 amount) external onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }
}
