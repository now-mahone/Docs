// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KerneYieldOracle
 * @author Kerne Protocol
 * @notice A manipulation-resistant yield oracle providing TWAY (Time-Weighted Average Yield).
 */
contract KerneYieldOracle is AccessControl {
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    struct YieldObservation {
        uint256 timestamp;
        uint256 sharePrice; // Assets per 1e18 shares
    }

    /// @notice Mapping from vault address to its observations
    mapping(address => YieldObservation[]) public observations;

    /// @notice The window for TWAY calculation (default: 7 days)
    uint256 public yieldWindow = 7 days;

    event YieldUpdated(address indexed vault, uint256 sharePrice, uint256 timestamp);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    /**
     * @notice Records a new share price observation for a vault.
     * @dev Requires that the vault's solvency has been recently verified by the VerificationNode.
     * @param vault The address of the KerneVault
     */
    function updateYield(address vault) external onlyRole(UPDATER_ROLE) {
        KerneVault v = KerneVault(vault);
        
        // Verify that the vault's assets are backed by a recent attestation
        address verificationNode = v.verificationNode();
        if (verificationNode != address(0)) {
            (bool success, bytes memory data) = verificationNode.staticcall(
                abi.encodeWithSignature("latestAttestations(address)", vault)
            );
            if (success && data.length >= 64) {
                (, uint256 timestamp, bool verified) = abi.decode(data, (uint256, uint256, bool));
                require(verified && (block.timestamp - timestamp < 24 hours), "Yield update requires recent attestation");
            }
        }

        uint256 price = v.convertToAssets(1e18);
        
        observations[vault].push(YieldObservation({
            timestamp: block.timestamp,
            sharePrice: price
        }));

        emit YieldUpdated(vault, price, block.timestamp);
    }

    /**
     * @notice Calculates the annualized TWAY for a vault over the yieldWindow.
     * @param vault The address of the KerneVault
     * @return apyBps The annualized yield in basis points (e.g., 1500 = 15%)
     */
    function getTWAY(address vault) public view returns (uint256 apyBps) {
        YieldObservation[] storage obs = observations[vault];
        if (obs.length < 2) return 0;

        YieldObservation memory latest = obs[obs.length - 1];
        
        // Find the observation closest to (now - yieldWindow)
        uint256 targetTime = block.timestamp > yieldWindow ? block.timestamp - yieldWindow : obs[0].timestamp;
        
        YieldObservation memory oldest = obs[0];
        for (uint256 i = obs.length; i > 0; i--) {
            if (obs[i-1].timestamp <= targetTime) {
                oldest = obs[i-1];
                break;
            }
        }

        uint256 timeDiff = latest.timestamp - oldest.timestamp;
        if (timeDiff == 0) return 0;

        // Calculate growth: (latestPrice / oldestPrice) - 1
        // Annualize: growth * (365 days / timeDiff)
        
        if (latest.sharePrice <= oldest.sharePrice) return 0;

        uint256 growth = ((latest.sharePrice * 1e18) / oldest.sharePrice) - 1e18;
        uint256 annualizedGrowth = (growth * 365 days) / timeDiff;
        
        // Convert to basis points (1e18 = 10000 bps)
        apyBps = (annualizedGrowth * 10000) / 1e18;
    }

    /**
     * @notice Sets the yield window for TWAY calculation.
     */
    function setYieldWindow(uint256 _window) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_window >= 1 days, "Window too short");
        yieldWindow = _window;
    }
}
