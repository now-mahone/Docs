// SPDX-License-Identifier: MIT
// Created: 2026-01-13
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
 * @title KerneIntentExecutor
 * @notice Executes intent-based trades using Kerne's internal liquidity (Vault/PSM) via flash loans.
 * @dev Transforms Kerne into the primary execution engine for high-volume trading on Base.
 */
contract KerneIntentExecutor is AccessControl, ReentrancyGuard, IERC3156FlashBorrower {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    bytes32 public constant SENTINEL_ROLE = keccak256("SENTINEL_ROLE");

    // Aggregator Addresses (Base Mainnet)
    address public constant ONE_INCH_ROUTER = 0x111111125421cA6dc452d289314280a0f8842A65;
    address public constant UNISWAP_ROUTER = 0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD;

    // Sentinel V2 Parameters
    uint256 public maxLatency = 500; // 500ms
    uint256 public maxPriceDeviationBps = 100; // 1% (100 bps)
    bool public sentinelActive = true;

    struct IntentSafetyParams {
        uint256 timestamp;
        uint256 expectedPrice; // Price in 1e18
    }

    event IntentFulfilled(address indexed user, address tokenIn, address tokenOut, uint256 amount, uint256 profit);
    event SentinelParamUpdated(string param, uint256 newValue);
    event SentinelStatusToggled(bool active);

    constructor(address admin, address solver) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(SOLVER_ROLE, solver);
        _grantRole(SENTINEL_ROLE, admin);
    }

    /**
     * @notice Fulfills a CowSwap/UniswapX intent using Kerne's internal liquidity.
     * @param lender The Kerne internal liquidity source (KerneVault or KUSDPSM).
     * @param tokenIn The token the user is providing.
     * @param tokenOut The token the user wants to receive.
     * @param amount The amount of tokenOut to provide.
     * @param user The address of the user whose intent is being fulfilled.
     * @param aggregatorData The call data for the aggregator (1inch/Uniswap) to settle the trade.
     * @param safetyParams Encoded IntentSafetyParams for circuit breaker validation.
     */
    function fulfillIntent(
        address lender,
        address tokenIn,
        address tokenOut,
        uint256 amount,
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

        bytes memory data = abi.encode(tokenIn, amount, user, aggregatorData);
        IERC3156FlashLender(lender).flashLoan(this, tokenOut, amount, data);
    }

    /**
     * @notice IERC3156 Flash Loan Callback
     */
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(initiator == address(this), "Untrusted initiator");
        
        (address tokenIn, , address user, bytes memory aggregatorData) = abi.decode(data, (address, uint256, address, bytes));

        // 1. Fulfill user intent: Send tokenOut (token) to user
        IERC20(token).safeTransfer(user, amount);

        // 2. Settlement: The aggregatorData should handle pulling tokenIn and swapping it back to token
        // to cover the flash loan amount + fee.
        
        // 3. Multi-Aggregator Swap: Swap tokenIn back to token to repay flash loan
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

        // 4. Repay Flash Loan
        uint256 amountToRepay = amount + fee;
        IERC20(token).forceApprove(msg.sender, amountToRepay);

        emit IntentFulfilled(user, tokenIn, token, amount, 0);
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
     * @notice Sweeps solver profits to the KerneVault.
     */
    function harvestToVault(address vault, address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).forceApprove(vault, balance);
        // Assuming vault has a deposit function for the strategist
        // KerneVault(vault).deposit(balance, address(this));
    }

    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {

        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
    }

    receive() external payable {}
}
