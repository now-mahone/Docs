// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";
import { IKerneLSTSolver } from "./interfaces/IKerneLSTSolver.sol";
import { IAerodromeRouter } from "./interfaces/IAerodromeRouter.sol";
import { IUniswapV3Router } from "./interfaces/IUniswapV3Router.sol";

/**
 * @title KerneLSTSolver
 * @author Kerne Protocol
 * @notice Executes high-frequency LST yield capture and arbitrage using vault flash liquidity.
 */
contract KerneLSTSolver is IKerneLSTSolver, IERC3156FlashBorrower, AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    bytes32 private constant CALLBACK_SUCCESS = keccak256("ERC3156FlashBorrower.onFlashLoan");

    address public immutable vault;
    address public immutable insuranceFund;
    address public immutable aerodromeRouter;
    address public immutable uniswapV3Router;

    uint256 public insuranceFundSplitBps = 2000; // 20%

    event LSTSwapExecuted(address indexed tokenIn, address indexed tokenOut, uint256 amountIn, uint256 amountOut, uint256 profit);
    event ProfitDistributed(address indexed token, uint256 vaultAmount, uint256 insuranceAmount);

    constructor(
        address _admin,
        address _vault,
        address _insuranceFund,
        address _aerodromeRouter,
        address _uniswapV3Router
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(SOLVER_ROLE, _admin);

        vault = _vault;
        insuranceFund = _insuranceFund;
        aerodromeRouter = _aerodromeRouter;
        uniswapV3Router = _uniswapV3Router;
    }

    /**
     * @notice Executes an LST swap/arbitrage using flash loans.
     * @param tokenIn The token to borrow and swap from.
     * @param tokenOut The token to swap to.
     * @param amount The amount of tokenIn to borrow.
     * @param data Encoded swap parameters (router type, path, etc.)
     */
    function executeLSTSwap(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        bytes calldata data
    ) external onlyRole(SOLVER_ROLE) nonReentrant returns (uint256) {
        return _initiateFlashLoan(tokenIn, amount, abi.encode(tokenOut, data));
    }

    function _initiateFlashLoan(address token, uint256 amount, bytes memory data) internal returns (uint256) {
        uint256 balanceBefore = IERC20(token).balanceOf(address(this));
        
        IERC3156FlashLender(vault).flashLoan(this, token, amount, data);
        
        uint256 balanceAfter = IERC20(token).balanceOf(address(this));
        uint256 profit = balanceAfter > balanceBefore ? balanceAfter - balanceBefore : 0;
        
        if (profit > 0) {
            _distributeProfit(token, profit);
        }
        
        return profit;
    }

    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(msg.sender == vault, "Untrusted lender");
        require(initiator == address(this), "Untrusted initiator");

        (address tokenOut, bytes memory swapData) = abi.decode(data, (address, bytes));
        
        _executeSwap(token, tokenOut, amount, swapData);

        uint256 totalRepayment = amount + fee;
        IERC20(token).forceApprove(vault, totalRepayment);

        return CALLBACK_SUCCESS;
    }

    function _executeSwap(address tokenIn, address tokenOut, uint256 amountIn, bytes memory swapData) internal {
        (uint8 routerType, bytes memory pathData) = abi.decode(swapData, (uint8, bytes));

        if (routerType == 0) { // Aerodrome
            IAerodromeRouter.Route[] memory routes = abi.decode(pathData, (IAerodromeRouter.Route[]));
            IERC20(tokenIn).forceApprove(aerodromeRouter, amountIn);
            IAerodromeRouter(aerodromeRouter).swapExactTokensForTokens(
                amountIn,
                0, // Slippage handled by bot
                routes,
                address(this),
                block.timestamp
            );
        } else if (routerType == 1) { // Uniswap V3
            IUniswapV3Router.ExactInputParams memory params = abi.decode(pathData, (IUniswapV3Router.ExactInputParams));
            params.amountIn = amountIn;
            params.recipient = address(this);
            IERC20(tokenIn).forceApprove(uniswapV3Router, amountIn);
            IUniswapV3Router(uniswapV3Router).exactInput(params);
        } else {
            revert("Invalid router type");
        }
    }

    function _distributeProfit(address token, uint256 profit) internal {
        uint256 insuranceAmount = (profit * insuranceFundSplitBps) / 10000;
        uint256 vaultAmount = profit - insuranceAmount;

        if (insuranceAmount > 0 && insuranceFund != address(0)) {
            IERC20(token).safeTransfer(insuranceFund, insuranceAmount);
        }

        if (vaultAmount > 0) {
            IERC20(token).safeTransfer(vault, vaultAmount);
        }

        emit ProfitDistributed(token, vaultAmount, insuranceAmount);
    }

    function setInsuranceFundSplit(uint256 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 5000, "Split too high");
        insuranceFundSplitBps = bps;
    }

    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
    }
}
