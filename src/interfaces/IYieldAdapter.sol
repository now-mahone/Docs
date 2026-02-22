// SPDX-License-Identifier: MIT
// Created: 2026-02-22
pragma solidity 0.8.24;

/**
 * @title IYieldAdapter
 * @author Kerne Protocol
 * @notice Universal interface for yield adapters to allow rapid addition of new yield sources.
 *         Uses flexible data payloads to accommodate complex integration requirements.
 */
interface IYieldAdapter {
    /**
     * @notice Harvests yield from the underlying protocol.
     * @param data Flexible data payload for complex harvesting logic (e.g., swap routes, min amounts).
     * @return harvestedAmount The amount of yield harvested (in terms of the base asset or reward token).
     */
    function harvest(bytes calldata data) external returns (uint256 harvestedAmount);

    /**
     * @notice Returns the total assets managed by the adapter.
     */
    function totalAssets() external view returns (uint256);
}