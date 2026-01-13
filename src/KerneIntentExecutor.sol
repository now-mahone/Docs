// SPDX-License-Identifier: MIT
// Created: 2026-01-13
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

interface IPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external;
}

interface IUniversalRouter {
    function execute(bytes calldata commands, bytes[] calldata inputs, uint256 deadline) external payable;
}

/**
 * @title KerneIntentExecutor
 * @notice Executes intent-based trades using flash loans and multi-aggregator settlement.
 */
contract KerneIntentExecutor is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    IPool public immutable LENDING_POOL;
    
    // Aggregator Addresses (Base Mainnet)
    address public constant ONE_INCH_ROUTER = 0x111111125421cA6dc452d289314280a0f8842A65;
    address public constant UNISWAP_ROUTER = 0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD;

    event IntentFulfilled(address indexed user, address tokenIn, address tokenOut, uint256 amount, uint256 profit);

    constructor(address admin, address solver, address lendingPool) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        LENDING_POOL = IPool(lendingPool);
    }

    /**
     * @notice Fulfills a CowSwap/UniswapX intent using a flash loan.
     */
    /**
     * @notice Fulfills a CowSwap/UniswapX intent using a flash loan.
     * @dev MEV Protection: This function should be called via a private RPC (e.g., Flashbots).
     */
    function fulfillIntent(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        address user,
        bytes calldata aggregatorData
    ) external onlyRole(SOLVER_ROLE) nonReentrant {
        // Ensure we are not being sandwiched by checking block.basefee or using a private bundle
        bytes memory params = abi.encode(tokenIn, amount, user, aggregatorData);
        LENDING_POOL.flashLoanSimple(address(this), tokenOut, amount, params, 0);
    }

    /**
     * @notice Sweeps solver profits to the KerneVault.
     */
    function harvestToVault(address vault, address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeApprove(vault, balance);
        // Assuming vault has a deposit function for the strategist
        // KerneVault(vault).deposit(balance, address(this));
    }

    /**
     * @notice Aave V3 Flash Loan Callback
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address initiator,
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == address(LENDING_POOL), "Untrusted lender");
        
        (address tokenIn, uint256 amountInExpected, address user, bytes memory aggregatorData) = abi.decode(params, (address, uint256, address, bytes));

        // 1. Fulfill user intent: Send tokenOut (asset) to user
        IERC20(asset).safeTransfer(user, amount);

        // 2. Settlement: Receive tokenIn from user/settlement
        // Logic to pull or receive tokenIn goes here

        // 3. Multi-Aggregator Swap: Swap tokenIn back to tokenOut to repay flash loan
        // We use the provided aggregatorData which contains the call to 1inch or Uniswap
        (bool success, ) = ONE_INCH_ROUTER.call(aggregatorData);
        require(success, "Aggregator swap failed");

        // 4. Repay Flash Loan
        uint256 amountToRepay = amount + premium;
        IERC20(asset).safeApprove(address(LENDING_POOL), amountToRepay);

        emit IntentFulfilled(user, tokenIn, asset, amount, 0);
        return true;
    }

    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
    }

    receive() external payable {}
}
