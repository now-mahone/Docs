// SPDX-License-Identifier: MIT
// Created: 2026-01-13
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";

/**
 * @title KerneArbExecutor
 * @notice Executes flash-loan powered arbitrage trades across DEXs.
 * @dev Scofield Point V3: High-frequency profit extraction from LST gaps.
 */
contract KerneArbExecutor is AccessControl, IERC3156FlashBorrower {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    bytes32 public constant SENTINEL_ROLE = keccak256("SENTINEL_ROLE");

    address public treasury;
    address public insuranceFund;
    address public vault;

    uint256 public profitSplitBps = 2000; // 20% to Insurance Fund
    uint256 public minProfitBps = 5;      // 0.05% min profit check
    bool public sentinelActive = true;
    uint256 public minSolvencyThreshold = 10100; // 101%

    struct ArbStep {
        address target;
        bytes data;
    }

    event ArbExecuted(address indexed tokenIn, uint256 amountIn, uint256 profit);
    event ProfitSplit(uint256 treasuryAmount, uint256 insuranceAmount);
    event SentinelToggled(bool active);

    constructor(address admin, address solver, address _treasury, address _insuranceFund, address _vault) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        _grantRole(SENTINEL_ROLE, admin);
        treasury = _treasury;
        insuranceFund = _insuranceFund;
        vault = _vault;
    }

    /**
     * @notice Checks protocol solvency before execution.
     */
    function _checkSolvency() internal view {
        if (!sentinelActive || vault == address(0)) return;
        (bool success, bytes memory data) = vault.staticcall(abi.encodeWithSignature("getSolvencyRatio()"));
        if (success && data.length == 32) {
            uint256 ratio = abi.decode(data, (uint256));
            require(ratio >= minSolvencyThreshold, "Sentinel: Protocol insolvency detected");
        }
    }

    /**
     * @notice Initiates an arbitrage with a flash loan.
     */
    function executeArbWithFlashLoan(
        address lender,
        address token,
        uint256 amount,
        ArbStep[] calldata steps
    ) external onlyRole(SOLVER_ROLE) {
        _checkSolvency();
        bytes memory data = abi.encode(steps);
        IERC3156FlashLender(lender).flashLoan(this, token, amount, data);
    }

    /**
     * @notice IERC3156 Callback
     */
    function onFlashLoan(
        address,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(hasRole(SOLVER_ROLE, tx.origin) || hasRole(DEFAULT_ADMIN_ROLE, tx.origin), "Unauthorized origin");
        
        uint256 balanceBefore = IERC20(token).balanceOf(address(this));
        
        ArbStep[] memory steps = abi.decode(data, (ArbStep[]));
        
        // 1. Execute Swaps
        for (uint256 i = 0; i < steps.length; i++) {
            (bool success, ) = steps[i].target.call(steps[i].data);
            require(success, "Arb step failed");
        }

        uint256 balanceAfter = IERC20(token).balanceOf(address(this));
        uint256 amountToRepay = amount + fee;
        
        require(balanceAfter >= balanceBefore + fee, "Arb not profitable (Fee not covered)");
        
        uint256 netProfit = balanceAfter - balanceBefore;
        // Verify min profit bps
        require(netProfit >= (amount * minProfitBps) / 10000, "Arb not profitable (Below minProfitBps)");

        // 2. Profit Split
        if (netProfit > 0) {
            uint256 insuranceAmount = (netProfit * profitSplitBps) / 10000;
            uint256 treasuryAmount = netProfit - insuranceAmount;
            
            if (insuranceAmount > 0 && insuranceFund != address(0)) {
                IERC20(token).safeTransfer(insuranceFund, insuranceAmount);
            }
            if (treasuryAmount > 0 && treasury != address(0)) {
                IERC20(token).safeTransfer(treasury, treasuryAmount);
            }
            emit ProfitSplit(treasuryAmount, insuranceAmount);
        }

        // 3. Approve repayment
        IERC20(token).forceApprove(msg.sender, amountToRepay);

        emit ArbExecuted(token, amount, netProfit);
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }

    /**
     * @notice Executes a multi-step arbitrage using existing contract balance.
     * @param tokenIn The token to flash loan (e.g. WETH).
     * @param amount The amount to flash loan.
     * @param steps The swap steps to execute.
     */
    function executeArb(
        address tokenIn,
        uint256 amount,
        ArbStep[] calldata steps
    ) external onlyRole(SOLVER_ROLE) {
        _checkSolvency();
        uint256 balanceBefore = IERC20(tokenIn).balanceOf(address(this));
        
        // 1. Execute Swaps
        for (uint256 i = 0; i < steps.length; i++) {
            (bool success, ) = steps[i].target.call(steps[i].data);
            require(success, "Arb step failed");
        }

        uint256 balanceAfter = IERC20(tokenIn).balanceOf(address(this));
        require(balanceAfter > balanceBefore + amount, "Arb not profitable");

        uint256 profit = balanceAfter - balanceBefore - amount;
        
        // 2. Profit Split
        if (profit > 0) {
            uint256 insuranceAmount = (profit * profitSplitBps) / 10000;
            uint256 treasuryAmount = profit - insuranceAmount;
            
            if (insuranceAmount > 0 && insuranceFund != address(0)) {
                IERC20(tokenIn).safeTransfer(insuranceFund, insuranceAmount);
            }
            if (treasuryAmount > 0 && treasury != address(0)) {
                IERC20(tokenIn).safeTransfer(treasury, treasuryAmount);
            }
            emit ProfitSplit(treasuryAmount, insuranceAmount);
        }

        emit ArbExecuted(tokenIn, amount, profit);
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    function setInsuranceFund(address _insuranceFund) external onlyRole(DEFAULT_ADMIN_ROLE) {
        insuranceFund = _insuranceFund;
    }

    function setProfitSplit(uint256 _bps) external onlyRole(SENTINEL_ROLE) {
        require(_bps <= 10000, "Invalid BPS");
        profitSplitBps = _bps;
    }

    function toggleSentinel(bool _active) external onlyRole(SENTINEL_ROLE) {
        sentinelActive = _active;
        emit SentinelToggled(_active);
    }


    /**
     * @notice Emergency withdraw of any stuck tokens.
     */
    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        SafeERC20.safeTransfer(IERC20(token), msg.sender, balance);
    }
}
