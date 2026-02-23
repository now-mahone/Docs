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
    uint256 public constant MAX_ARB_STEPS = 10;

    /// @notice Whitelist of allowed target addresses for arb steps (DEX routers only)
    mapping(address => bool) public allowedTargets;

    /// @notice SECURITY: Approved flash loan lenders (only trusted internal contracts)
    mapping(address => bool) public approvedLenders;

    /// @notice SECURITY: Whitelist of allowed function selectors per target
    mapping(address => mapping(bytes4 => bool)) public allowedSelectors;

    struct ArbStep {
        address target;
        bytes data;
    }

    error TargetNotWhitelisted(address target);
    error SelectorNotWhitelisted(address target, bytes4 selector);
    error TooManySteps(uint256 count);

    event ArbExecuted(address indexed tokenIn, uint256 amountIn, uint256 profit);
    event ProfitSplit(uint256 treasuryAmount, uint256 insuranceAmount);
    event SentinelToggled(bool active);
    event TargetWhitelistUpdated(address indexed target, bool allowed);
    event ApprovedLenderUpdated(address indexed lender, bool approved);
    event AllowedSelectorUpdated(address indexed target, bytes4 indexed selector, bool allowed);

    constructor(address admin, address solver, address _treasury, address _insuranceFund, address _vault) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        _grantRole(SENTINEL_ROLE, admin);
        treasury = _treasury;
        insuranceFund = _insuranceFund;
        vault = _vault;
    }

    /**
     * @notice Sets an address as an approved flash loan lender.
     * @dev SECURITY FIX: Only trusted internal contracts (KerneVault, KUSDPSM) should be approved.
     */
    function setApprovedLender(address lender, bool approved) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(lender != address(0), "Invalid lender");
        approvedLenders[lender] = approved;
        emit ApprovedLenderUpdated(lender, approved);
    }

    /**
     * @notice Add or remove a target address from the whitelist.
     * @dev Only DEX routers should be whitelisted (e.g., Aerodrome, Uniswap V3).
     *      SECURITY FIX: Prevents arbitrary call injection via ArbStep targets.
     */
    function setAllowedTarget(address target, bool allowed) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(target != address(0), "Invalid target");
        // Prevent whitelisting protocol contracts to avoid self-drain
        require(target != address(this), "Cannot whitelist self");
        require(target != treasury, "Cannot whitelist treasury");
        require(target != insuranceFund, "Cannot whitelist insurance");
        require(target != vault, "Cannot whitelist vault");
        allowedTargets[target] = allowed;
        emit TargetWhitelistUpdated(target, allowed);
    }

    /**
     * @notice Set allowed function selectors for a specific target.
     * @dev SECURITY: Only whitelisted selectors can be called on whitelisted targets.
     *      This prevents calling dangerous functions (transferOwnership, approve, etc.) on DEX routers.
     */
    function setAllowedSelector(address target, bytes4 selector, bool allowed) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(target != address(0), "Invalid target");
        allowedSelectors[target][selector] = allowed;
        emit AllowedSelectorUpdated(target, selector, allowed);
    }

    /**
     * @notice Batch set allowed selectors for a target.
     */
    function batchSetAllowedSelectors(
        address target,
        bytes4[] calldata selectors,
        bool allowed
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(target != address(0), "Invalid target");
        require(selectors.length <= 50, "Too many selectors");
        for (uint256 i = 0; i < selectors.length; i++) {
            allowedSelectors[target][selectors[i]] = allowed;
            emit AllowedSelectorUpdated(target, selectors[i], allowed);
        }
    }

    /**
     * @notice Validates that all arb step targets and selectors are whitelisted.
     * @dev SECURITY: Enforces both target whitelist AND function selector whitelist.
     *      Also enforces max steps to prevent gas griefing.
     */
    function _validateSteps(ArbStep[] memory steps) internal view {
        if (steps.length > MAX_ARB_STEPS) {
            revert TooManySteps(steps.length);
        }
        require(steps.length > 0, "No steps provided");
        for (uint256 i = 0; i < steps.length; i++) {
            if (!allowedTargets[steps[i].target]) {
                revert TargetNotWhitelisted(steps[i].target);
            }
            // Extract function selector (first 4 bytes of calldata)
            require(steps[i].data.length >= 4, "Invalid calldata");
            bytes4 selector = bytes4(steps[i].data[0]) | (bytes4(steps[i].data[1]) >> 8) | (bytes4(steps[i].data[2]) >> 16) | (bytes4(steps[i].data[3]) >> 24);
            if (!allowedSelectors[steps[i].target][selector]) {
                revert SelectorNotWhitelisted(steps[i].target, selector);
            }
        }
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
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(initiator == address(this), "Unauthorized initiator");
        // SECURITY FIX: Authenticate the lender (msg.sender) as an approved source
        require(approvedLenders[msg.sender], "Unapproved lender");
        
        uint256 balanceBefore = IERC20(token).balanceOf(address(this));
        
        ArbStep[] memory steps = abi.decode(data, (ArbStep[]));
        
        // SECURITY: Validate all targets are whitelisted DEX routers
        _validateSteps(steps);
        
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
        
        // SECURITY: Validate all targets are whitelisted DEX routers
        _validateSteps(steps);
        
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
        require(_treasury != address(0), "Invalid treasury");
        treasury = _treasury;
    }

    function setInsuranceFund(address _insuranceFund) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_insuranceFund != address(0), "Invalid insurance fund");
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
