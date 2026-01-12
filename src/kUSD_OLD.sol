// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Burnable.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/extensions/ERC20Permit.sol";

/**
 * @title kUSD
 * @author Kerne Protocol
 * @notice The Kerne Synthetic Dollar (kUSD) is a delta-neutral stablecoin.
 * It is minted against KerneVault shares (kLP).
 */
contract kUSD is ERC20, ERC20Burnable, AccessControl, ERC20Permit {
    bytes32 public constant MINTER_ROLE = keccak256("MINTER_ROLE");

    constructor(
        address defaultAdmin
    ) ERC20("Kerne Synthetic Dollar", "kUSD") ERC20Permit("Kerne Synthetic Dollar") {
        _grantRole(DEFAULT_ADMIN_ROLE, defaultAdmin);
    }

    /**
     * @notice Mints kUSD to a specific address.
     * @dev Only addresses with MINTER_ROLE can call this.
     * @param to The address to receive the minted kUSD.
     * @param amount The amount of kUSD to mint.
     */
    function mint(address to, uint256 amount) public onlyRole(MINTER_ROLE) {
        _mint(to, amount);
    }

    /**
     * @notice Flash-mints kUSD.
     * @dev The receiver must repay the amount plus any fees (if applicable) in the same transaction.
     * @param receiver The address to receive the flash-minted kUSD.
     * @param amount The amount of kUSD to flash-mint.
     * @param data Arbitrary data to pass to the receiver's callback.
     */
    function flashMint(address receiver, uint256 amount, bytes calldata data) external onlyRole(MINTER_ROLE) {
        _mint(receiver, amount);

        require(
            IFlashBorrower(receiver).onFlashMint(msg.sender, address(this), amount, 0, data)
                == keccak256("ERC3156FlashBorrower.onFlashMint"),
            "FlashMint: Callback failed"
        );

        _burn(receiver, amount);
    }
}

interface IFlashBorrower {
    function onFlashMint(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32);
}
