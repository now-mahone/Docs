// Created: 2026-02-19
// Kerne Protocol - Price Oracle Interface
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

/// @title IKernePriceOracle
/// @notice Interface for multi-source price oracle with TWAP support
/// @dev Used to validate prices from multiple sources and detect manipulation
interface IKernePriceOracle {
    /// @notice Returns current median price from all sources
    /// @return price The current price in 18 decimal precision
    function getPrice() external view returns (uint256 price);

    /// @notice Returns TWAP price from Uniswap V3
    /// @return price The TWAP price in 18 decimal precision
    function getTwapPrice() external view returns (uint256 price);

    /// @notice Returns true if all price sources are within tolerance
    /// @return valid Whether the price sources agree within acceptable bounds
    function isPriceValid() external view returns (bool valid);

    /// @notice Returns individual source prices for transparency
    /// @return chainlinkPrice The price from Chainlink feed
    /// @return uniswapTwapPrice The TWAP price from Uniswap V3
    /// @return timestamp The timestamp of the last observation
    function getPriceSources() external view returns (
        uint256 chainlinkPrice,
        uint256 uniswapTwapPrice,
        uint256 timestamp
    );

    /// @notice Updates TWAP observation (called by bot)
    /// @dev Only callable by UPDATER_ROLE
    function updateObservation() external;

    /// @notice Emitted when a new observation is recorded
    event ObservationRecorded(
        uint256 indexed timestamp,
        uint256 price0Cumulative,
        uint256 price1Cumulative
    );

    /// @notice Emitted when price deviation exceeds threshold
    event PriceDeviationWarning(
        uint256 chainlinkPrice,
        uint256 twapPrice,
        uint256 deviationBps
    );

    /// @notice Emitted when circuit breaker is triggered
    event CircuitBreakerTriggered(uint256 recordedPrice, uint256 attemptedPrice);
}