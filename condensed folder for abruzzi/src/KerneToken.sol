// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Pausable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Votes.sol";

/**
 * @title KerneToken
 * @author Kerne Protocol
 * @notice The native governance token for the Kerne ecosystem.
 */
contract KerneToken is ERC20, ERC20Burnable, ERC20Pausable, AccessControl, ERC20Permit, ERC20Votes {
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    constructor(
        address defaultAdmin
    ) ERC20("Kerne", "KERNE") ERC20Permit("Kerne") {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
        _grantRole(PAUSER_ROLE, defaultAdmin);
        _mint(msg.sender, 100_000_000 * 10 ** decimals()); // 100M Initial Supply
    }

    function pause() public onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() public onlyRole(PAUSER_ROLE) {
        _unpause();
    }

    function mint(address to, uint256 amount) public onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /**
     * @notice Reflexive Buyback: Burns tokens to increase scarcity.
     * @dev Can be called by the protocol using captured fees.
     */
    function reflexiveBurn(
        uint256 amount
    ) external {
        _burn(msg.sender, amount);
    }

    // The following functions are overrides required by Solidity.

    function _update(address from, address to, uint256 value) internal override(ERC20, ERC20Pausable, ERC20Votes) {
        super._update(from, to, value);
    }

    function nonces(
        address owner
    ) public view override(ERC20Permit, Nonces) returns (uint256) {
        return super.nonces(owner);
    }
}
