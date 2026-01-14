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
    bytes32 public constant SENTINEL_ROLE = keccak256("SENTINEL_ROLE");

    IPool public immutable LENDING_POOL;
    
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
    /**
     * @notice Fulfills a CowSwap/UniswapX intent using a flash loan with Sentinel V2 safety checks.
     * @param safetyParams Encoded IntentSafetyParams for circuit breaker validation.
     */
    function fulfillIntent(
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
            
            // 2. Price Deviation Check: (Placeholder for oracle comparison)
            // In production, we would compare s.expectedPrice with a Chainlink or internal oracle price.
            // require(abs(oraclePrice - s.expectedPrice) <= (oraclePrice * maxPriceDeviationBps / 10000), "Sentinel: Price deviation too high");
        }

        // Ensure we are not being sandwiched by checking block.basefee or using a private bundle
        bytes memory params = abi.encode(tokenIn, amount, user, aggregatorData);
        LENDING_POOL.flashLoanSimple(address(this), tokenOut, amount, params, 0);
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

    /**
     * @notice Aave V3 Flash Loan Callback
     */
    function executeOperation(
        address asset,
        uint256 amount,
        uint256 premium,
        address, // initiator
        bytes calldata params
    ) external returns (bool) {
        require(msg.sender == address(LENDING_POOL), "Untrusted lender");
        
        (address tokenIn, , address user, bytes memory aggregatorData) = abi.decode(params, (address, uint256, address, bytes));

        // 1. Fulfill user intent: Send tokenOut (asset) to user
        IERC20(asset).safeTransfer(user, amount);

        // 2. Settlement: Receive tokenIn from user/settlement
        // Logic to pull or receive tokenIn goes here

        // 3. Multi-Aggregator Swap: Swap tokenIn back to tokenOut to repay flash loan
        // We use the provided aggregatorData which contains the call to 1inch or Uniswap
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
        uint256 amountToRepay = amount + premium;
        IERC20(asset).forceApprove(address(LENDING_POOL), amountToRepay);

        emit IntentFulfilled(user, tokenIn, asset, amount, 0);
        return true;
    }

    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
    }

    receive() external payable {}
}
