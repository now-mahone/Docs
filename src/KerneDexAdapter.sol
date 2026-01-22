// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import "./interfaces/IAerodromeRouter.sol";

/**
 * @title KerneDexAdapter
 * @author Kerne Protocol
 * @notice Adapts Aerodrome Router to the simple swap interface expected by kUSDMinter
 * @dev The kUSDMinter expects: swap(address from, address to, uint256 amount, uint256 minOut)
 *      Aerodrome uses route-based swaps, so this adapter translates the interface.
 */
contract KerneDexAdapter is Ownable {
    using SafeERC20 for IERC20;

    // ═══════════════════════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════════════════════

    /// @notice Aerodrome Router V2 on Base
    IAerodromeRouter public immutable router;
    
    /// @notice Factory for pool lookups
    address public immutable factory;
    
    /// @notice WETH address for hop routing
    address public constant WETH = 0x4200000000000000000000000000000000000006;
    
    /// @notice Mapping of token pairs that should route through WETH
    /// @dev key = keccak256(tokenA, tokenB), value = true if needs hop
    mapping(bytes32 => bool) public needsHop;
    
    /// @notice Mapping of stable pool pairs
    mapping(bytes32 => bool) public isStablePair;

    // ═══════════════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════════════

    event Swapped(address indexed fromAsset, address indexed toAsset, uint256 amountIn, uint256 amountOut);
    event HopConfigured(address indexed tokenA, address indexed tokenB, bool needsHop);
    event StablePairConfigured(address indexed tokenA, address indexed tokenB, bool isStable);

    // ═══════════════════════════════════════════════════════════════════════════════
    // ERRORS
    // ═══════════════════════════════════════════════════════════════════════════════

    error SwapFailed();
    error ZeroAddress();
    error InsufficientOutput();

    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Initialize the adapter with Aerodrome router
     * @param _router Aerodrome Router V2 address
     */
    constructor(address _router) Ownable(msg.sender) {
        if (_router == address(0)) revert ZeroAddress();
        router = IAerodromeRouter(_router);
        factory = router.defaultFactory();
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // CORE SWAP FUNCTION
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Execute a swap from one token to another
     * @param fromAsset The token to swap from
     * @param toAsset The token to swap to
     * @param amount The amount of fromAsset to swap
     * @param minAmountOut Minimum amount of toAsset to receive (slippage protection)
     * @return receivedAmount The amount of toAsset received
     * @dev This is the interface expected by kUSDMinter
     */
    function swap(
        address fromAsset,
        address toAsset,
        uint256 amount,
        uint256 minAmountOut
    ) external returns (uint256 receivedAmount) {
        if (fromAsset == address(0) || toAsset == address(0)) revert ZeroAddress();
        
        // Transfer tokens from caller
        IERC20(fromAsset).safeTransferFrom(msg.sender, address(this), amount);
        
        // Approve router
        IERC20(fromAsset).safeIncreaseAllowance(address(router), amount);
        
        // Build route
        IAerodromeRouter.Route[] memory routes = _buildRoute(fromAsset, toAsset);
        
        // Get expected output for price check
        uint256[] memory expectedAmounts = router.getAmountsOut(amount, routes);
        uint256 expectedOut = expectedAmounts[expectedAmounts.length - 1];
        
        // Apply minAmountOut if not specified (use 99% of expected)
        if (minAmountOut == 0) {
            minAmountOut = (expectedOut * 99) / 100;
        }
        
        // Track balance before
        uint256 balanceBefore = IERC20(toAsset).balanceOf(address(this));
        
        // Execute swap
        router.swapExactTokensForTokens(
            amount,
            minAmountOut,
            routes,
            address(this),
            block.timestamp + 300
        );
        
        // Calculate received amount
        receivedAmount = IERC20(toAsset).balanceOf(address(this)) - balanceBefore;
        
        if (receivedAmount < minAmountOut) revert InsufficientOutput();
        
        // Transfer output to caller
        IERC20(toAsset).safeTransfer(msg.sender, receivedAmount);
        
        emit Swapped(fromAsset, toAsset, amount, receivedAmount);
    }

    /**
     * @notice Get expected output for a swap
     * @param fromAsset The token to swap from
     * @param toAsset The token to swap to
     * @param amount The amount of fromAsset to swap
     * @return expectedOut Expected amount of toAsset
     */
    function getAmountOut(
        address fromAsset,
        address toAsset,
        uint256 amount
    ) external view returns (uint256 expectedOut) {
        IAerodromeRouter.Route[] memory routes = _buildRoute(fromAsset, toAsset);
        uint256[] memory amounts = router.getAmountsOut(amount, routes);
        expectedOut = amounts[amounts.length - 1];
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // INTERNAL FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Build the optimal route for a swap
     * @param fromAsset Source token
     * @param toAsset Destination token
     * @return routes Array of Route structs for Aerodrome
     */
    function _buildRoute(
        address fromAsset,
        address toAsset
    ) internal view returns (IAerodromeRouter.Route[] memory routes) {
        bytes32 pairKey = _getPairKey(fromAsset, toAsset);
        
        // Check if we need to route through WETH
        if (needsHop[pairKey] && fromAsset != WETH && toAsset != WETH) {
            // Two-hop route: fromAsset → WETH → toAsset
            routes = new IAerodromeRouter.Route[](2);
            
            bytes32 firstHopKey = _getPairKey(fromAsset, WETH);
            bytes32 secondHopKey = _getPairKey(WETH, toAsset);
            
            routes[0] = IAerodromeRouter.Route({
                from: fromAsset,
                to: WETH,
                stable: isStablePair[firstHopKey],
                factory: factory
            });
            routes[1] = IAerodromeRouter.Route({
                from: WETH,
                to: toAsset,
                stable: isStablePair[secondHopKey],
                factory: factory
            });
        } else {
            // Direct route: fromAsset → toAsset
            routes = new IAerodromeRouter.Route[](1);
            routes[0] = IAerodromeRouter.Route({
                from: fromAsset,
                to: toAsset,
                stable: isStablePair[pairKey],
                factory: factory
            });
        }
    }

    /**
     * @notice Generate a unique key for a token pair (order-independent)
     * @param tokenA First token
     * @param tokenB Second token
     * @return key The keccak256 hash of the ordered pair
     */
    function _getPairKey(address tokenA, address tokenB) internal pure returns (bytes32) {
        (address token0, address token1) = tokenA < tokenB 
            ? (tokenA, tokenB) 
            : (tokenB, tokenA);
        return keccak256(abi.encodePacked(token0, token1));
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Configure whether a pair needs WETH hop routing
     * @param tokenA First token
     * @param tokenB Second token
     * @param _needsHop Whether to route through WETH
     */
    function setNeedsHop(address tokenA, address tokenB, bool _needsHop) external onlyOwner {
        bytes32 pairKey = _getPairKey(tokenA, tokenB);
        needsHop[pairKey] = _needsHop;
        emit HopConfigured(tokenA, tokenB, _needsHop);
    }

    /**
     * @notice Configure whether a pair should use stable pool
     * @param tokenA First token
     * @param tokenB Second token
     * @param _isStable Whether to use stable pool
     */
    function setStablePair(address tokenA, address tokenB, bool _isStable) external onlyOwner {
        bytes32 pairKey = _getPairKey(tokenA, tokenB);
        isStablePair[pairKey] = _isStable;
        emit StablePairConfigured(tokenA, tokenB, _isStable);
    }

    /**
     * @notice Batch configure hop routing for multiple pairs
     * @param tokens Array of token pairs [tokenA1, tokenB1, tokenA2, tokenB2, ...]
     * @param hops Array of hop settings corresponding to pairs
     */
    function batchSetHops(address[] calldata tokens, bool[] calldata hops) external onlyOwner {
        require(tokens.length == hops.length * 2, "Invalid array lengths");
        for (uint256 i = 0; i < hops.length; i++) {
            bytes32 pairKey = _getPairKey(tokens[i * 2], tokens[i * 2 + 1]);
            needsHop[pairKey] = hops[i];
        }
    }

    /**
     * @notice Recover any stuck tokens
     * @param token Token to recover
     * @param to Recipient address
     */
    function rescueTokens(address token, address to) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(to, balance);
    }
}
