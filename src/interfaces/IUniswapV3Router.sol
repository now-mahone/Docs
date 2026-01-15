// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title IUniswapV3Router
 * @notice Interface for Uniswap V3 SwapRouter on Base
 * @dev Used for executing single-hop and multi-hop swaps via Uniswap V3
 *      Base Mainnet: 0x2626664c2603336E57B271c5C0b26F421741e481
 */
interface IUniswapV3Router {
    /// @notice Parameters for exactInputSingle
    struct ExactInputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
        uint160 sqrtPriceLimitX96;
    }

    /// @notice Parameters for exactOutputSingle
    struct ExactOutputSingleParams {
        address tokenIn;
        address tokenOut;
        uint24 fee;
        address recipient;
        uint256 amountOut;
        uint256 amountInMaximum;
        uint160 sqrtPriceLimitX96;
    }

    /// @notice Parameters for exactInput (multi-hop)
    struct ExactInputParams {
        bytes path;
        address recipient;
        uint256 amountIn;
        uint256 amountOutMinimum;
    }

    /// @notice Parameters for exactOutput (multi-hop)
    struct ExactOutputParams {
        bytes path;
        address recipient;
        uint256 amountOut;
        uint256 amountInMaximum;
    }

    /// @notice Swaps `amountIn` of one token for as much as possible of another token
    /// @param params The parameters necessary for the swap
    /// @return amountOut The amount of the received token
    function exactInputSingle(
        ExactInputSingleParams calldata params
    ) external payable returns (uint256 amountOut);

    /// @notice Swaps `amountIn` of one token for as much as possible of another along the specified path
    /// @param params The parameters necessary for the multi-hop swap
    /// @return amountOut The amount of the received token
    function exactInput(
        ExactInputParams calldata params
    ) external payable returns (uint256 amountOut);

    /// @notice Swaps as little as possible of one token for an exact amount of another token
    /// @param params The parameters necessary for the swap
    /// @return amountIn The amount of the input token
    function exactOutputSingle(
        ExactOutputSingleParams calldata params
    ) external payable returns (uint256 amountIn);

    /// @notice Swaps as little as possible along the specified path to receive an exact amount
    /// @param params The parameters necessary for the multi-hop swap
    /// @return amountIn The amount of the input token
    function exactOutput(
        ExactOutputParams calldata params
    ) external payable returns (uint256 amountIn);

    /// @notice Returns the amount out received for a given exact input swap without executing the swap
    /// @param path The path of the swap
    /// @param amountIn The amount of input tokens to swap
    /// @return amountOut The amount of output tokens
    function quoteExactInput(
        bytes memory path,
        uint256 amountIn
    ) external returns (uint256 amountOut);

    /// @notice Returns the amount out received for a given exact input but for a single pool swap
    /// @param tokenIn Token being swapped in
    /// @param tokenOut Token being swapped out
    /// @param fee Pool fee tier
    /// @param amountIn Amount being swapped
    /// @param sqrtPriceLimitX96 Price limit
    /// @return amountOut The amount of output tokens
    function quoteExactInputSingle(
        address tokenIn,
        address tokenOut,
        uint24 fee,
        uint256 amountIn,
        uint160 sqrtPriceLimitX96
    ) external returns (uint256 amountOut);

    /// @notice Unwraps the contract's WETH9 balance and sends it to recipient as ETH
    /// @param amountMinimum The minimum amount of WETH9
    /// @param recipient The address to receive ETH
    function unwrapWETH9(uint256 amountMinimum, address recipient) external payable;

    /// @notice Refunds any ETH balance held by this contract to the caller
    function refundETH() external payable;

    /// @notice Transfers token balance held by this contract to recipient
    /// @param token Token to sweep
    /// @param amountMinimum Minimum to sweep
    /// @param recipient The address to receive tokens
    function sweepToken(
        address token,
        uint256 amountMinimum,
        address recipient
    ) external payable;
}
