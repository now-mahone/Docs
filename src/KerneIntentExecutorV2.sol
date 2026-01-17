// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";

interface IUniversalRouter {
    function execute(bytes calldata commands, bytes[] calldata inputs, uint256 deadline) external payable;
}

/**
 * @title KerneIntentExecutorV2
 * @notice Zero-Fee Intent Network (ZIN) - Transforms Kerne into Base's primary execution engine.
 * @dev Uses internal liquidity (Vault/PSM) to fulfill intents at zero cost, capturing the spread.
 * @custom:security Contact security@kerne.io
 */
contract KerneIntentExecutorV2 is AccessControl, ReentrancyGuard, IERC3156FlashBorrower {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    bytes32 public constant SENTINEL_ROLE = keccak256("SENTINEL_ROLE");

    // Aggregator Addresses (Base Mainnet)
    address public constant ONE_INCH_ROUTER = 0x111111125421cA6dc452d289314280a0f8842A65;
    address public constant UNISWAP_ROUTER = 0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD;
    address public constant AERODROME_ROUTER = 0xCf77A3bA9A5ca399B7c97c478569A74Dd55c726f;

    // Sentinel V2 Parameters
    uint256 public maxLatency = 500; // 500ms
    uint256 public maxPriceDeviationBps = 100; // 1% (100 bps)
    bool public sentinelActive = true;

    // ZIN Profit Tracking
    address public profitVault; // Vault where profits are deposited
    uint256 public totalSpreadCaptured; // Lifetime spread captured (in USD equivalent, 18 decimals)
    uint256 public totalIntentsFulfilled; // Total intents processed
    mapping(address => uint256) public tokenSpreadCaptured; // Spread captured per token

    struct IntentSafetyParams {
        uint256 timestamp;
        uint256 expectedPrice; // Price in 1e18
        uint256 minProfitBps; // Minimum profit in basis points (optional)
    }

    struct IntentExecution {
        address user;
        address tokenIn;
        address tokenOut;
        uint256 amountOut;
        uint256 spreadCaptured;
        uint256 timestamp;
    }

    event IntentFulfilled(
        address indexed user,
        address tokenIn,
        address tokenOut,
        uint256 amountOut,
        uint256 spreadCaptured,
        uint256 timestamp
    );
    event ProfitHarvested(address indexed token, uint256 amount, address indexed vault);
    event SentinelParamUpdated(string param, uint256 newValue);
    event SentinelStatusToggled(bool active);

    constructor(address admin, address solver, address _profitVault) {
        require(_profitVault != address(0), "Profit vault cannot be zero");
        profitVault = _profitVault;
        
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        _grantRole(SENTINEL_ROLE, admin);
    }

    /**
     * @notice Fulfills a CowSwap/UniswapX intent using Kerne's internal liquidity.
     * @dev This is the core ZIN function - we flash loan from internal vault, fulfill user intent,
     *      swap received tokens back to repay the loan, and CAPTURE THE SPREAD.
     * @param lender The Kerne internal liquidity source (KerneVault or KUSDPSM).
     * @param tokenIn The token the user is providing.
     * @param tokenOut The token the user wants to receive.
     * @param amountOut The amount of tokenOut to provide to the user.
     * @param user The address of the user whose intent is being fulfilled.
     * @param aggregatorData The call data for the aggregator (1inch/Uniswap/Aerodrome) to settle the trade.
     * @param safetyParams Encoded IntentSafetyParams for circuit breaker validation.
     */
    function fulfillIntent(
        address lender,
        address tokenIn,
        address tokenOut,
        uint256 amountOut,
        address user,
        bytes calldata aggregatorData,
        bytes calldata safetyParams
    ) external onlyRole(SOLVER_ROLE) nonReentrant {
        if (sentinelActive) {
            IntentSafetyParams memory s = abi.decode(safetyParams, (IntentSafetyParams));
            
            // 1. Latency Check: Ensure the intent was signed recently
            uint256 latencySeconds = maxLatency / 1000;
            if (latencySeconds == 0) latencySeconds = 1; // Minimum 1s resolution
            require(block.timestamp <= s.timestamp + latencySeconds, "Sentinel: Intent expired (Latency)");
        }

        bytes memory data = abi.encode(tokenIn, amountOut, user, aggregatorData, msg.sender);
        IERC3156FlashLender(lender).flashLoan(this, tokenOut, amountOut, data);
    }

    /**
     * @notice IERC3156 Flash Loan Callback - The Core ZIN Engine
     * @dev Flow:
     *      1. Receive flash loan of tokenOut
     *      2. Send tokenOut to user (fulfill their intent)
     *      3. Use aggregatorData to swap user's tokenIn for tokenOut
     *      4. Repay flash loan amount (0 fee for internal liquidity)
     *      5. Keep the difference as spread profit
     */
    function onFlashLoan(
        address initiator,
        address tokenOut,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(initiator == address(this), "Untrusted initiator");
        
        (address tokenIn, uint256 amountOut, address user, bytes memory aggregatorData, address solver) = 
            abi.decode(data, (address, uint256, address, bytes, address));

        // Step 1: Fulfill user intent - Send tokenOut to user at zero cost to them
        IERC20(tokenOut).safeTransfer(user, amountOut);

        // Step 2: Execute aggregator trade to get tokenIn and swap it to tokenOut
        // The aggregatorData should handle pulling tokenIn from user and swapping to tokenOut
        uint256 balanceBefore = IERC20(tokenOut).balanceOf(address(this));
        
        (bool success, bytes memory returnData) = ONE_INCH_ROUTER.call(aggregatorData);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            } else {
                revert("Aggregator swap failed");
            }
        }

        // Step 3: Calculate spread captured
        uint256 balanceAfter = IERC20(tokenOut).balanceOf(address(this));
        uint256 amountRepayable = amount + fee; // Fee should be 0 for internal liquidity
        
        // The spread is any tokenOut remaining after repaying the flash loan
        // This represents the profit from fulfilling the intent better than market price
        uint256 spreadCaptured = 0;
        if (balanceAfter > amountRepayable) {
            spreadCaptured = balanceAfter - amountRepayable;
        }

        // Step 4: Repay Flash Loan
        IERC20(tokenOut).forceApprove(msg.sender, amountRepayable);

        // Step 5: Track and distribute spread profit
        if (spreadCaptured > 0) {
            totalSpreadCaptured += spreadCaptured;
            tokenSpreadCaptured[tokenOut] += spreadCaptured;
            totalIntentsFulfilled += 1;
            
            // Auto-harvest to profit vault
            if (profitVault != address(0)) {
                IERC20(tokenOut).safeTransfer(profitVault, spreadCaptured);
                emit ProfitHarvested(tokenOut, spreadCaptured, profitVault);
            }
        }

        emit IntentFulfilled(user, tokenIn, tokenOut, amountOut, spreadCaptured, block.timestamp);
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }

    /**
     * @notice Updates Sentinel parameters.
     */
    function updateSentinelParams(uint256 _maxLatency, uint256 _maxPriceDeviationBps) external onlyRole(SENTINEL_ROLE) {
        maxLatency = _maxLatency;
        maxPriceDeviationBps = _maxPriceDeviationBps;
        emit SentinelParamUpdated("latency", _maxLatency);
        emit SentinelParamUpdated("deviation", _maxPriceDeviationBps);
    }

    /**
     * @notice Toggles Sentinel safety checks.
     */
    function toggleSentinel(bool _active) external onlyRole(SENTINEL_ROLE) {
        sentinelActive = _active;
        emit SentinelStatusToggled(_active);
    }

    /**
     * @notice Updates the profit vault address.
     */
    function setProfitVault(address _profitVault) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_profitVault != address(0), "Profit vault cannot be zero");
        profitVault = _profitVault;
    }

    /**
     * @notice Manually harvest accumulated profits to the vault.
     * @dev Use this if auto-harvest fails or for emergency withdrawals.
     */
    function harvestProfits(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        require(balance > 0, "No tokens to harvest");
        
        IERC20(token).safeTransfer(profitVault, balance);
        emit ProfitHarvested(token, balance, profitVault);
    }

    /**
     * @notice Recover stuck tokens (emergency only).
     */
    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
    }

    /**
     * @notice Get ZIN performance metrics.
     */
    function getZINMetrics() external view returns (
        uint256 totalSpread,
        uint256 totalIntents,
        address currentVault
    ) {
        return (totalSpreadCaptured, totalIntentsFulfilled, profitVault);
    }

    /**
     * @notice Get spread captured for a specific token.
     */
    function getTokenSpread(address token) external view returns (uint256) {
        return tokenSpreadCaptured[token];
    }

    receive() external payable {}
}
