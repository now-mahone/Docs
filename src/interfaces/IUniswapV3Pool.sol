// Created: 2026-02-19
// Kerne Protocol - Uniswap V3 Pool Interface for TWAP
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IUniswapV3Pool
/// @notice Minimal interface for Uniswap V3 pool TWAP observations
/// @dev Only includes functions needed for price oracle
interface IUniswapV3Pool {
    /// @notice The first token of the pool
    function token0() external view returns (address);

    /// @notice The second token of the pool
    function token1() external view returns (address);

    /// @notice The pool's fee in hundredths of a bip
    function fee() external view returns (uint24);

    /// @notice The 0th storage slot in the pool stores many values
    /// @return sqrtPriceX96 The current price of the pool as a sqrt(token1/token0) Q64.96 value
    /// @return tick The current tick of the pool
    /// @return observationIndex The index of the last oracle observation
    /// @return observationCardinality The current maximum number of observations
    /// @return observationCardinalityNext The next maximum number of observations
    /// @return feeProtocol The protocol fee for both tokens
    /// @return unlocked Whether the pool is currently locked to reentrancy
    function slot0() external view returns (
        uint160 sqrtPriceX96,
        int24 tick,
        uint16 observationIndex,
        uint16 observationCardinality,
        uint16 observationCardinalityNext,
        uint8 feeProtocol,
        bool unlocked
    );

    /// @notice Returns data about a specific observation index
    /// @param index The element of the observations array to fetch
    /// @return blockTimestamp The timestamp of the observation
    /// @return tickCumulative The tick multiplied by seconds elapsed for the life of the pool as of the observation timestamp
    /// @return secondsPerLiquidityCumulativeX128 The seconds per in range liquidity for the life of the pool as of the observation timestamp
    /// @return initialized Whether the observation has been initialized and the values are safe to use
    function observations(uint256 index) external view returns (
        uint32 blockTimestamp,
        int56 tickCumulative,
        uint160 secondsPerLiquidityCumulativeX128,
        bool initialized
    );

    /// @notice Returns the cumulative tick and liquidity as of each timestamp secondsAgo from the current block timestamp
    /// @param secondsAgos Each amount of time to look back, in seconds, at which point to return an observation
    /// @return tickCumulatives The tick * time elapsed since the pool was first initialized
    /// @return secondsPerLiquidityCumulativeX128s The seconds per / in range liquidity since the pool was first initialized
    function observe(uint32[] calldata secondsAgos) external view returns (
        int56[] memory tickCumulatives,
        uint160[] memory secondsPerLiquidityCumulativeX128s
    );
}