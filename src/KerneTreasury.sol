// Created: 2026-01-04
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title KerneTreasury
 * @notice Handles automated wealth extraction, founder payouts, and $KERNE buybacks.
 * @dev Routes 80% of performance fees to the founder and 20% to $KERNE buyback/staking.
 */
contract KerneTreasury is Ownable, ReentrancyGuard {
    address public founder;
    address public kerneToken;
    address public stakingContract;

    uint256 public constant FOUNDER_SHARE = 8000; // 80%
    uint256 public constant BUYBACK_SHARE = 2000; // 20%
    uint256 public constant BPS_DENOMINATOR = 10000;

    event FeesDistributed(address indexed token, uint256 founderAmount, uint256 buybackAmount);
    event FounderUpdated(address indexed newFounder);
    event BuybackExecuted(uint256 amountIn, uint256 amountOut);

    constructor(address _founder, address _kerneToken, address _stakingContract) Ownable(msg.sender) {
        founder = _founder;
        kerneToken = _kerneToken;
        stakingContract = _stakingContract;
    }

    /**
     * @notice Distributes accumulated tokens between founder and buyback pool.
     * @param token The token to distribute (usually WETH or kUSD).
     */
    function distribute(
        address token
    ) external nonReentrant {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No balance to distribute");

        uint256 founderAmount = (balance * FOUNDER_SHARE) / BPS_DENOMINATOR;
        uint256 buybackAmount = balance - founderAmount;

        // Transfer to founder
        IERC20(token).transfer(founder, founderAmount);

        // Transfer to staking/buyback
        // In a production environment, this would trigger an Aerodrome swap
        // For now, we transfer to the staking contract which handles distribution
        IERC20(token).transfer(stakingContract, buybackAmount);

        emit FeesDistributed(token, founderAmount, buybackAmount);
    }

    /**
     * @notice Executes a buyback of $KERNE using accumulated fees.
     * @dev This is a placeholder for the actual swap logic (e.g., via Aerodrome).
     */
    function executeBuyback(address token, uint256 amount, uint256 minKerne) external onlyOwner {
        // Logic for swapping 'token' for 'kerneToken' on Aerodrome
        // This increases buy pressure and founder wealth (via their KERNE holdings)
        emit BuybackExecuted(amount, minKerne);
    }

    /**
     * @notice Emergency withdraw for any stuck tokens.
     */
    function emergencyWithdraw(
        address token
    ) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).transfer(owner(), balance);
    }

    function updateFounder(
        address _newFounder
    ) external {
        require(msg.sender == founder || msg.sender == owner(), "Unauthorized");
        founder = _newFounder;
        emit FounderUpdated(_newFounder);
    }
}
