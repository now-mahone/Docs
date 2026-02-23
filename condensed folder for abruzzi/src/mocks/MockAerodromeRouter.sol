// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "../interfaces/IAerodromeRouter.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title MockAerodromeRouter
 * @notice Mock implementation of Aerodrome Router for testing
 * @dev Simulates swap behavior with configurable exchange rates
 */
contract MockAerodromeRouter is IAerodromeRouter {
    address public override weth;
    address public override defaultFactory;
    
    // Exchange rate: how much output per input (in basis points, 10000 = 1:1)
    uint256 public exchangeRateBps = 10000;
    
    // Per-pair exchange rates (in 1e18 precision for flexibility)
    mapping(address => mapping(address => uint256)) public mockRates;
    
    // Track swap calls for assertions
    uint256 public swapCallCount;
    address public lastSwapToken;
    uint256 public lastSwapAmount;
    
    // Configurable failure
    bool public shouldFail;
    
    constructor() {
        defaultFactory = address(this); // Self as factory for simplicity
    }
    
    function setWeth(address _weth) external {
        weth = _weth;
    }
    
    function setExchangeRate(uint256 _rateBps) external {
        exchangeRateBps = _rateBps;
    }
    
    /// @notice Set mock exchange rate between tokens (1e18 = 1:1)
    function setMockRate(address tokenIn, address tokenOut, uint256 rate) external {
        mockRates[tokenIn][tokenOut] = rate;
    }
    
    function setShouldFail(bool _fail) external {
        shouldFail = _fail;
    }
    
    function sortTokens(address tokenA, address tokenB) 
        external 
        pure 
        override 
        returns (address token0, address token1) 
    {
        return tokenA < tokenB ? (tokenA, tokenB) : (tokenB, tokenA);
    }
    
    function poolFor(
        address,
        address,
        bool,
        address
    ) external view override returns (address pool) {
        return address(this);
    }
    
    function getReserves(
        address,
        address,
        bool,
        address
    ) external pure override returns (uint256 reserveA, uint256 reserveB) {
        return (1000000e18, 1000000e18);
    }
    
    function getAmountOut(
        uint256 amountIn,
        address,
        address
    ) external view override returns (uint256 amount, bool stable) {
        amount = (amountIn * exchangeRateBps) / 10000;
        stable = false;
    }
    
    function getAmountsOut(
        uint256 amountIn,
        Route[] calldata routes
    ) external view override returns (uint256[] memory amounts) {
        amounts = new uint256[](routes.length + 1);
        amounts[0] = amountIn;
        
        uint256 currentAmount = amountIn;
        for (uint256 i = 0; i < routes.length; i++) {
            uint256 rate = mockRates[routes[i].from][routes[i].to];
            if (rate > 0) {
                currentAmount = (currentAmount * rate) / 1e18;
            } else {
                currentAmount = (currentAmount * exchangeRateBps) / 10000;
            }
            amounts[i + 1] = currentAmount;
        }
    }
    
    function swapExactTokensForTokens(
        uint256 amountIn,
        uint256 amountOutMin,
        Route[] calldata routes,
        address to,
        uint256
    ) external override returns (uint256[] memory amounts) {
        require(!shouldFail, "MockRouter: swap failed");
        
        swapCallCount++;
        lastSwapToken = routes[0].from;
        lastSwapAmount = amountIn;
        
        amounts = new uint256[](routes.length + 1);
        amounts[0] = amountIn;
        
        // Transfer input token from sender
        IERC20(routes[0].from).transferFrom(msg.sender, address(this), amountIn);
        
        // Calculate output
        uint256 currentAmount = amountIn;
        for (uint256 i = 0; i < routes.length; i++) {
            uint256 rate = mockRates[routes[i].from][routes[i].to];
            if (rate > 0) {
                currentAmount = (currentAmount * rate) / 1e18;
            } else {
                currentAmount = (currentAmount * exchangeRateBps) / 10000;
            }
            amounts[i + 1] = currentAmount;
        }
        
        uint256 amountOut = amounts[routes.length];
        require(amountOut >= amountOutMin, "MockRouter: insufficient output");
        
        // Mint output tokens to recipient (assuming we have them or can mint)
        address outputToken = routes[routes.length - 1].to;
        IERC20(outputToken).transfer(to, amountOut);
        
        return amounts;
    }
    
    function swapExactETHForTokens(
        uint256,
        Route[] calldata,
        address,
        uint256
    ) external payable override returns (uint256[] memory) {
        revert("Not implemented");
    }
    
    function swapExactTokensForETH(
        uint256,
        uint256,
        Route[] calldata,
        address,
        uint256
    ) external pure override returns (uint256[] memory) {
        revert("Not implemented");
    }
    
    function addLiquidity(
        address,
        address,
        bool,
        uint256,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256, uint256, uint256) {
        revert("Not implemented");
    }
    
    function removeLiquidity(
        address,
        address,
        bool,
        uint256,
        uint256,
        uint256,
        address,
        uint256
    ) external pure override returns (uint256, uint256) {
        revert("Not implemented");
    }
    
    function quoteAddLiquidity(
        address,
        address,
        bool,
        address,
        uint256,
        uint256
    ) external pure override returns (uint256, uint256, uint256) {
        revert("Not implemented");
    }
    
    function quoteRemoveLiquidity(
        address,
        address,
        bool,
        address,
        uint256
    ) external pure override returns (uint256, uint256) {
        revert("Not implemented");
    }
}
