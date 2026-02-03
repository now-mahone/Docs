// Created: 2026-02-03
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title KerneYieldStripper
 * @author Kerne Protocol
 * @notice Replicates Pendle's yield stripping for Kerne Vault shares (kLP).
 *         Allows users to split kLP into Principal Tokens (PT) and Yield Tokens (YT).
 */
contract KerneYieldStripper is AccessControl {
    using SafeERC20 for IERC20;

    struct Lockup {
        uint256 amount;
        uint256 maturity;
        address owner;
    }

    IERC20 public immutable kLP;
    mapping(uint256 => Lockup) public lockups;
    uint256 public nextLockupId;

    // PT and YT would ideally be separate ERC20s, but for this MVP we'll use a registry model.
    event YieldStripped(uint256 indexed lockupId, address indexed owner, uint256 amount, uint256 maturity);

    constructor(IERC20 _kLP, address _admin) {
        kLP = _kLP;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /**
     * @notice Strips yield from kLP.
     * @param amount The amount of kLP to lock.
     * @param duration The duration of the lock (in seconds).
     */
    function stripYield(uint256 amount, uint256 duration) external returns (uint256 lockupId) {
        kLP.safeTransferFrom(msg.sender, address(this), amount);
        
        lockupId = nextLockupId++;
        uint256 maturity = block.timestamp + duration;
        
        lockups[lockupId] = Lockup({
            amount: amount,
            maturity: maturity,
            owner: msg.sender
        });

        emit YieldStripped(lockupId, msg.sender, amount, maturity);
        
        // In a full implementation, we would mint PT and YT ERC20s here.
        // For now, we record the lockup state.
    }

    /**
     * @notice Redeems the principal after maturity.
     * @param lockupId The ID of the lockup to redeem.
     */
    function redeemPrincipal(uint256 lockupId) external {
        Lockup storage lock = lockups[lockupId];
        require(block.timestamp >= lock.maturity, "Not matured");
        require(msg.sender == lock.owner, "Not owner");

        uint256 amount = lock.amount;
        delete lockups[lockupId];
        
        kLP.safeTransfer(msg.sender, amount);
    }
}