// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { IUniswapV3Router } from "../interfaces/IUniswapV3Router.sol";

/**
 * @title MockUniswapV3Router
 * @notice Mock Uniswap V3 Router for testing arbitrage functionality
 */
contract MockUniswapV3Router is IUniswapV3Router {
    
    /// @notice Exchange rate: how many tokenOut per tokenIn (in 1e18 precision)
    mapping(address => mapping(address => uint256)) public mockRates;
    
    /// @notice Fee tier rates (simulates different pool depths)
    mapping(uint24 => uint256) public feeTierSlippage;
    
    constructor() {
        // Default fee tier slippage (in basis points of price impact)
        feeTierSlippage[100] = 1;    // 0.01% fee, minimal slippage
        feeTierSlippage[500] = 5;    // 0.05% fee, minimal slippage
        feeTierSlippage[3000] = 30;  // 0.3% fee, some slippage
        feeTierSlippage[10000] = 100; // 1% fee, more slippage
    }
    
    /// @notice Set mock exchange rate between tokens
    function setMockRate(address tokenIn, address tokenOut, uint256 rate) external {
        mockRates[tokenIn][tokenOut] = rate;
    }
    
    /// @notice Batch set rates for easier testing
    function setMockRates(
        address[] calldata tokensIn,
        address[] calldata tokensOut,
        uint256[] calldata rates
    ) external {
        require(tokensIn.length == tokensOut.length && tokensOut.length == rates.length, "Length mismatch");
        for (uint256 i = 0; i < tokensIn.length; i++) {
            mockRates[tokensIn[i]][tokensOut[i]] = rates[i];
        }
    }
    
    function exactInputSingle(
        ExactInputSingleParams calldata params
    ) external payable override returns (uint256 amountOut) {
        // Transfer input tokens from sender
        IERC20(params.tokenIn).transferFrom(msg.sender, address(this), params.amountIn);
        
        // Calculate output based on mock rate
        uint256 rate = mockRates[params.tokenIn][params.tokenOut];
        if (rate == 0) {
            rate = 1e18; // 1:1 default
        }
        
        amountOut = (params.amountIn * rate) / 1e18;
        
        // Apply fee tier slippage
        uint256 slippage = feeTierSlippage[params.fee];
        if (slippage > 0) {
            amountOut = amountOut * (10000 - slippage) / 10000;
        }
        
        require(amountOut >= params.amountOutMinimum, "Too little received");
        
        // Transfer output tokens to recipient
        IERC20(params.tokenOut).transfer(params.recipient, amountOut);
        
        return amountOut;
    }
    
    function exactInput(
        ExactInputParams calldata params
    ) external payable override returns (uint256 amountOut) {
        // Simplified: extract first and last token from path (20 bytes each, with 3 byte fees between)
        require(params.path.length >= 43, "Invalid path");
        
        address tokenIn = _extractAddress(params.path, 0);
        address tokenOut = _extractAddress(params.path, params.path.length - 20);
        
        IERC20(tokenIn).transferFrom(msg.sender, address(this), params.amountIn);
        
        uint256 rate = mockRates[tokenIn][tokenOut];
        if (rate == 0) rate = 1e18;
        
        amountOut = (params.amountIn * rate) / 1e18;
        require(amountOut >= params.amountOutMinimum, "Too little received");
        
        IERC20(tokenOut).transfer(params.recipient, amountOut);
        
        return amountOut;
    }
    
    function exactOutputSingle(
        ExactOutputSingleParams calldata params
    ) external payable override returns (uint256 amountIn) {
        uint256 rate = mockRates[params.tokenIn][params.tokenOut];
        if (rate == 0) rate = 1e18;
        
        // Calculate required input
        amountIn = (params.amountOut * 1e18) / rate;
        
        // Add fee slippage
        uint256 slippage = feeTierSlippage[params.fee];
        if (slippage > 0) {
            amountIn = amountIn * (10000 + slippage) / 10000;
        }
        
        require(amountIn <= params.amountInMaximum, "Too much requested");
        
        IERC20(params.tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(params.tokenOut).transfer(params.recipient, params.amountOut);
        
        return amountIn;
    }
    
    function exactOutput(
        ExactOutputParams calldata params
    ) external payable override returns (uint256 amountIn) {
        require(params.path.length >= 43, "Invalid path");
        
        // For exactOutput, path is reversed: tokenOut -> ... -> tokenIn
        address tokenOut = _extractAddress(params.path, 0);
        address tokenIn = _extractAddress(params.path, params.path.length - 20);
        
        uint256 rate = mockRates[tokenIn][tokenOut];
        if (rate == 0) rate = 1e18;
        
        amountIn = (params.amountOut * 1e18) / rate;
        require(amountIn <= params.amountInMaximum, "Too much requested");
        
        IERC20(tokenIn).transferFrom(msg.sender, address(this), amountIn);
        IERC20(tokenOut).transfer(params.recipient, params.amountOut);
        
        return amountIn;
    }
    
    function quoteExactInput(
        bytes memory path,
        uint256 amountIn
    ) external view override returns (uint256 amountOut) {
        require(path.length >= 43, "Invalid path");
        
        address tokenIn = _extractAddressFromMemory(path, 0);
        address tokenOut = _extractAddressFromMemory(path, path.length - 20);
        
        uint256 rate = mockRates[tokenIn][tokenOut];
        if (rate == 0) rate = 1e18;
        
        amountOut = (amountIn * rate) / 1e18;
    }
    
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 /* sqrtPriceLimitX96 */
    ) external view override returns (uint256 amountOut) {
        uint256 rate = mockRates[tokenIn][tokenOut];
        if (rate == 0) rate = 1e18;
        
        amountOut = (amountIn * rate) / 1e18;
        
        // Apply fee tier slippage
        uint256 slippage = feeTierSlippage[fee];
        if (slippage > 0) {
            amountOut = amountOut * (10000 - slippage) / 10000;
        }
    }
    
    /// @dev Extract address from calldata bytes at offset
    function _extractAddress(bytes calldata data, uint256 offset) internal pure returns (address) {
        bytes20 addrBytes;
        for (uint256 i = 0; i < 20; i++) {
            addrBytes |= bytes20(data[offset + i]) >> (i * 8);
        }
        return address(addrBytes);
    }
    
    /// @dev Extract address from memory bytes at offset
    function _extractAddressFromMemory(bytes memory data, uint256 offset) internal pure returns (address addr) {
        assembly {
            addr := mload(add(add(data, 20), offset))
        }
    }
    
    function unwrapWETH9(uint256, address) external payable override {}
    function refundETH() external payable override {}
    function sweepToken(address, uint256, address) external payable override {}
    
    receive() external payable {}
}
