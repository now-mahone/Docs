// SPDX-License-Identifier: MIT
// Created: 2026-01-13
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";

/**
 * @title KerneArbExecutor
 * @notice Executes flash-loan powered arbitrage trades across DEXs.
 * @dev Scofield Point V3: High-frequency profit extraction from LST gaps.
 */
contract KerneArbExecutor is AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    address public treasury;

    struct ArbStep {
        address target;
        bytes data;
    }

    event ArbExecuted(address indexed tokenIn, uint256 amountIn, uint256 profit);

    constructor(address admin, address solver, address _treasury) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        treasury = _treasury;
    }

    /**
     * @notice Executes a multi-step arbitrage using a flash loan.
     * @param tokenIn The token to flash loan (e.g. WETH).
     * @param amount The amount to flash loan.
     * @param steps The swap steps to execute.
     */
    function executeArb(
        address tokenIn,
        uint256 amount,
        ArbStep[] calldata steps
    ) external onlyRole(SOLVER_ROLE) {
        uint256 balanceBefore = IERC20(tokenIn).balanceOf(address(this));
        
        // 1. Execute Swaps
        for (uint256 i = 0; i < steps.length; i++) {
            (bool success, ) = steps[i].target.call(steps[i].data);
            require(success, "Arb step failed");
        }

        uint256 balanceAfter = IERC20(tokenIn).balanceOf(address(this));
        require(balanceAfter > balanceBefore + amount, "Arb not profitable");

        uint256 profit = balanceAfter - balanceBefore - amount;
        
        // 2. Repay Flash Loan (Logic handled by caller if this is a callback, 
        // but here we assume the solver sent the flash loan funds to this contract)
        
        // 3. Transfer profit to Kerne Treasury
        if (profit > 0 && treasury != address(0)) {
            IERC20(tokenIn).safeTransfer(treasury, profit);
        }

        emit ArbExecuted(tokenIn, amount, profit);
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    /**
     * @notice Emergency withdraw of any stuck tokens.
     */
    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        SafeERC20.safeTransfer(IERC20(token), msg.sender, balance);
    }
}
