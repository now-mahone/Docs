// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";

/**
 * @title KerneZINRouter
 * @notice Intelligent order router for the Zero-Fee Intent Network. Routes orders across
 *         Kerne's internal liquidity (Vault, PSM, ZINPool) before falling back to external DEXs.
 * @dev This is the "brain" of ZIN - it determines the optimal route for each intent.
 */
contract KerneZINRouter is AccessControl, ReentrancyGuard, IERC3156FlashBorrower {
    using SafeERC20 for IERC20;

    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");
    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    // === Liquidity Sources ===
    address public kerneVault;      // Primary internal liquidity (highest priority)
    address public kusdPSM;         // Stablecoin PSM (for stable pairs)
    address public zinPool;         // Aggregated ZIN liquidity pool

    // === External DEX Routers (Base Mainnet) ===
    address public constant ONE_INCH_ROUTER = 0x111111125421cA6dc452d289314280a0f8842A65;
    address public constant UNISWAP_ROUTER = 0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD;
    address public constant AERODROME_ROUTER = 0xCf77A3bA9A5ca399B7c97c478569A74Dd55c726f;
    address public constant BALANCER_VAULT = 0xBA12222222228d8Ba445958a75a0704d566BF2C8;

    // === Route Configuration ===
    uint256 public internalLiquidityThreshold = 80; // Use internal if >80% of amount available
    uint256 public minProfitBps = 5; // Minimum 0.05% profit required to execute
    uint256 public maxSlippageBps = 100; // Max 1% slippage allowed

    // === Profit Tracking ===
    address public treasury;
    uint256 public totalVolume;
    uint256 public totalProfit;
    uint256 public totalOrdersFilled;
    mapping(address => uint256) public tokenVolume;
    mapping(address => uint256) public tokenProfit;

    // === Order Types ===
    enum RouteType { INTERNAL_VAULT, INTERNAL_PSM, INTERNAL_POOL, EXTERNAL_1INCH, EXTERNAL_UNISWAP, EXTERNAL_AERODROME, SPLIT }
    
    struct Route {
        RouteType routeType;
        address source;
        uint256 percentage; // For split routes, percentage from this source (in bps, 10000 = 100%)
        bytes callData;
    }

    struct Intent {
        address user;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 minAmountOut;
        uint256 deadline;
        bytes32 intentHash;
    }

    struct ExecutionResult {
        uint256 amountOut;
        uint256 profit;
        RouteType primaryRoute;
        bool success;
    }

    // === Events ===
    event IntentRouted(bytes32 indexed intentHash, address indexed user, RouteType routeType, uint256 amountIn, uint256 amountOut, uint256 profit);
    event RouteAnalyzed(bytes32 indexed intentHash, RouteType recommended, uint256 estimatedOutput, uint256 estimatedProfit);
    event LiquiditySourceUpdated(string sourceName, address newAddress);
    event ConfigUpdated(string param, uint256 value);

    constructor(
        address admin,
        address _kerneVault,
        address _kusdPSM,
        address _treasury
    ) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MANAGER_ROLE, admin);
        _grantRole(SOLVER_ROLE, admin);
        
        kerneVault = _kerneVault;
        kusdPSM = _kusdPSM;
        treasury = _treasury;
    }

    // === Core Routing Logic ===

    /**
     * @notice Analyzes the best route for an intent without executing.
     * @param tokenIn Input token
     * @param tokenOut Output token
     * @param amountIn Amount of input token
     * @return bestRoute The recommended route type
     * @return estimatedOut Estimated output amount
     * @return internalLiquidity Available internal liquidity
     */
    function analyzeRoute(
        address tokenIn,
        address tokenOut,
        uint256 amountIn
    ) public view returns (
        RouteType bestRoute,
        uint256 estimatedOut,
        uint256 internalLiquidity
    ) {
        // Check internal vault liquidity first
        if (kerneVault != address(0)) {
            uint256 vaultBalance = IERC20(tokenOut).balanceOf(kerneVault);
            if (vaultBalance >= amountIn) {
                return (RouteType.INTERNAL_VAULT, amountIn, vaultBalance);
            }
            internalLiquidity += vaultBalance;
        }

        // Check PSM for stablecoin pairs
        if (kusdPSM != address(0)) {
            uint256 psmBalance = IERC20(tokenOut).balanceOf(kusdPSM);
            if (psmBalance >= amountIn) {
                return (RouteType.INTERNAL_PSM, amountIn, psmBalance);
            }
            internalLiquidity += psmBalance;
        }

        // Check ZIN Pool
        if (zinPool != address(0)) {
            uint256 poolBalance = IERC20(tokenOut).balanceOf(zinPool);
            if (poolBalance >= amountIn) {
                return (RouteType.INTERNAL_POOL, amountIn, poolBalance);
            }
            internalLiquidity += poolBalance;
        }

        // Check if we can do a split route
        if (internalLiquidity >= (amountIn * internalLiquidityThreshold) / 100) {
            return (RouteType.SPLIT, amountIn, internalLiquidity);
        }

        // Fall back to external DEXs
        return (RouteType.EXTERNAL_1INCH, amountIn, 0);
    }

    /**
     * @notice Executes an intent using the optimal route.
     * @param intent The intent to execute
     * @param routes Precomputed routes (from off-chain solver)
     * @param aggregatorCallData Call data for external DEX (if needed)
     */
    function executeIntent(
        Intent calldata intent,
        Route[] calldata routes,
        bytes calldata aggregatorCallData
    ) external onlyRole(SOLVER_ROLE) nonReentrant returns (ExecutionResult memory) {
        require(block.timestamp <= intent.deadline, "Intent expired");
        
        // Track starting balances
        uint256 tokenOutBefore = IERC20(intent.tokenOut).balanceOf(address(this));
        // uint256 tokenInBefore = IERC20(intent.tokenIn).balanceOf(address(this));

        // Execute primary route
        Route memory primaryRoute = routes[0];
        
        if (primaryRoute.routeType == RouteType.INTERNAL_VAULT) {
            _executeInternalVaultRoute(intent, primaryRoute);
        } else if (primaryRoute.routeType == RouteType.INTERNAL_PSM) {
            _executeInternalPSMRoute(intent, primaryRoute);
        } else if (primaryRoute.routeType == RouteType.INTERNAL_POOL) {
            _executeInternalPoolRoute(intent, primaryRoute);
        } else if (primaryRoute.routeType == RouteType.SPLIT) {
            _executeSplitRoute(intent, routes, aggregatorCallData);
        } else {
            _executeExternalRoute(intent, primaryRoute, aggregatorCallData);
        }

        // Calculate results
        uint256 tokenOutAfter = IERC20(intent.tokenOut).balanceOf(address(this));
        uint256 amountReceived = tokenOutAfter > tokenOutBefore ? tokenOutAfter - tokenOutBefore : 0;
        
        require(amountReceived >= intent.minAmountOut, "Slippage exceeded");

        // Send tokens to user
        IERC20(intent.tokenOut).safeTransfer(intent.user, intent.minAmountOut);

        // Calculate and capture profit
        uint256 profit = 0;
        if (amountReceived > intent.minAmountOut) {
            profit = amountReceived - intent.minAmountOut;
            if (profit > 0 && treasury != address(0)) {
                IERC20(intent.tokenOut).safeTransfer(treasury, profit);
            }
        }

        // Update statistics
        totalVolume += intent.amountIn;
        totalProfit += profit;
        totalOrdersFilled++;
        tokenVolume[intent.tokenIn] += intent.amountIn;
        tokenProfit[intent.tokenOut] += profit;

        emit IntentRouted(
            intent.intentHash,
            intent.user,
            primaryRoute.routeType,
            intent.amountIn,
            amountReceived,
            profit
        );

        return ExecutionResult({
            amountOut: amountReceived,
            profit: profit,
            primaryRoute: primaryRoute.routeType,
            success: true
        });
    }

    /**
     * @notice Flash loan callback for internal liquidity sourcing.
     */
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        require(initiator == address(this), "Untrusted initiator");
        
        (address user, uint256 minAmountOut, bytes memory swapData) = abi.decode(data, (address, uint256, bytes));

        // Execute the swap using provided calldata
        if (swapData.length > 0) {
            (bool success,) = ONE_INCH_ROUTER.call(swapData);
            require(success, "Swap failed");
        }

        // Send minimum to user
        IERC20(token).safeTransfer(user, minAmountOut);

        // Repay flash loan
        uint256 repayAmount = amount + fee;
        IERC20(token).forceApprove(msg.sender, repayAmount);

        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }

    // === Internal Route Executors ===

    function _executeInternalVaultRoute(Intent calldata intent, Route memory route) internal {
        // Flash loan from vault, fulfill user, repay with swapped tokens
        bytes memory data = abi.encode(intent.user, intent.minAmountOut, route.callData);
        IERC3156FlashLender(kerneVault).flashLoan(this, intent.tokenOut, intent.minAmountOut, data);
    }

    function _executeInternalPSMRoute(Intent calldata intent, Route memory route) internal {
        // PSM swap for stablecoin pairs
        bytes memory data = abi.encode(intent.user, intent.minAmountOut, route.callData);
        IERC3156FlashLender(kusdPSM).flashLoan(this, intent.tokenOut, intent.minAmountOut, data);
    }

    function _executeInternalPoolRoute(Intent calldata intent, Route memory route) internal {
        bytes memory data = abi.encode(intent.user, intent.minAmountOut, route.callData);
        IERC3156FlashLender(zinPool).flashLoan(this, intent.tokenOut, intent.minAmountOut, data);
    }

    function _executeSplitRoute(
        Intent calldata intent,
        Route[] calldata routes,
        bytes calldata aggregatorCallData
    ) internal {
        // Split across multiple sources for large orders
        for (uint256 i = 0; i < routes.length; i++) {
            Route memory route = routes[i];
            uint256 splitAmount = (intent.minAmountOut * route.percentage) / 10000;
            
            if (route.routeType == RouteType.INTERNAL_VAULT && kerneVault != address(0)) {
                bytes memory data = abi.encode(intent.user, splitAmount, route.callData);
                IERC3156FlashLender(kerneVault).flashLoan(this, intent.tokenOut, splitAmount, data);
            } else if (route.routeType == RouteType.EXTERNAL_1INCH) {
                (bool success,) = ONE_INCH_ROUTER.call(aggregatorCallData);
                require(success, "External swap failed");
            }
        }
    }

    function _executeExternalRoute(
        Intent calldata intent,
        Route memory route,
        bytes calldata aggregatorCallData
    ) internal {
        // Pure external execution through aggregator
        address router;
        if (route.routeType == RouteType.EXTERNAL_1INCH) {
            router = ONE_INCH_ROUTER;
        } else if (route.routeType == RouteType.EXTERNAL_UNISWAP) {
            router = UNISWAP_ROUTER;
        } else if (route.routeType == RouteType.EXTERNAL_AERODROME) {
            router = AERODROME_ROUTER;
        } else {
            revert("Invalid route type");
        }

        (bool success, bytes memory returnData) = router.call(aggregatorCallData);
        if (!success) {
            if (returnData.length > 0) {
                assembly {
                    let returndata_size := mload(returnData)
                    revert(add(32, returnData), returndata_size)
                }
            }
            revert("External route failed");
        }
    }

    // === Configuration ===

    function setLiquiditySources(
        address _kerneVault,
        address _kusdPSM,
        address _zinPool
    ) external onlyRole(MANAGER_ROLE) {
        if (_kerneVault != address(0)) {
            kerneVault = _kerneVault;
            emit LiquiditySourceUpdated("kerneVault", _kerneVault);
        }
        if (_kusdPSM != address(0)) {
            kusdPSM = _kusdPSM;
            emit LiquiditySourceUpdated("kusdPSM", _kusdPSM);
        }
        if (_zinPool != address(0)) {
            zinPool = _zinPool;
            emit LiquiditySourceUpdated("zinPool", _zinPool);
        }
    }

    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        treasury = _treasury;
    }

    function setRoutingConfig(
        uint256 _internalLiquidityThreshold,
        uint256 _minProfitBps,
        uint256 _maxSlippageBps
    ) external onlyRole(MANAGER_ROLE) {
        require(_internalLiquidityThreshold <= 100, "Invalid threshold");
        require(_maxSlippageBps <= 500, "Slippage too high");
        
        internalLiquidityThreshold = _internalLiquidityThreshold;
        minProfitBps = _minProfitBps;
        maxSlippageBps = _maxSlippageBps;
        
        emit ConfigUpdated("internalLiquidityThreshold", _internalLiquidityThreshold);
        emit ConfigUpdated("minProfitBps", _minProfitBps);
        emit ConfigUpdated("maxSlippageBps", _maxSlippageBps);
    }

    // === View Functions ===

    function getMetrics() external view returns (
        uint256 volume,
        uint256 profit,
        uint256 orders,
        address currentTreasury
    ) {
        return (totalVolume, totalProfit, totalOrdersFilled, treasury);
    }

    function getTokenMetrics(address token) external view returns (
        uint256 volume,
        uint256 profit
    ) {
        return (tokenVolume[token], tokenProfit[token]);
    }

    function getInternalLiquidity(address token) external view returns (uint256) {
        uint256 total = 0;
        if (kerneVault != address(0)) total += IERC20(token).balanceOf(kerneVault);
        if (kusdPSM != address(0)) total += IERC20(token).balanceOf(kusdPSM);
        if (zinPool != address(0)) total += IERC20(token).balanceOf(zinPool);
        return total;
    }

    // === Emergency ===

    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(treasury, balance);
    }

    receive() external payable {}
}
