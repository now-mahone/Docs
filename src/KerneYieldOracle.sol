// SPDX-License-Identifier: MIT
// Created: 2026-01-10
// Updated: 2026-01-12 - Hardened for aggregator integration
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KerneYieldOracle
 * @author Kerne Protocol
 * @notice A manipulation-resistant yield oracle providing TWAY (Time-Weighted Average Yield).
 * @dev Designed for integration with yield aggregators (Yearn, Beefy, DefiLlama).
 *      Features: staleness checks, min observation requirements, batch updates.
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

    /// @notice Maximum staleness before data is considered invalid (default: 24 hours)
    uint256 public maxStaleness = 24 hours;

    /// @notice Minimum observations required for valid TWAY (default: 3)
    uint256 public minObservations = 3;

    /// @notice Registered vaults for batch operations
    address[] public registeredVaults;
    mapping(address => bool) public isRegistered;

    event YieldUpdated(address indexed vault, uint256 sharePrice, uint256 timestamp);
    event VaultRegistered(address indexed vault);
    event VaultUnregistered(address indexed vault);
    event ConfigUpdated(string param, uint256 value);

    error StaleData(address vault, uint256 lastUpdate, uint256 staleness);
    error InsufficientObservations(address vault, uint256 count, uint256 required);
    error VaultNotRegistered(address vault);

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
        emit ConfigUpdated("yieldWindow", _window);
    }

    // ============ AGGREGATOR INTEGRATION FUNCTIONS ============

    /**
     * @notice Register a vault for batch operations and tracking.
     * @param vault The vault address to register
     */
    function registerVault(address vault) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(!isRegistered[vault], "Already registered");
        registeredVaults.push(vault);
        isRegistered[vault] = true;
        emit VaultRegistered(vault);
    }

    /**
     * @notice Unregister a vault from batch operations.
     * @param vault The vault address to unregister
     */
    function unregisterVault(address vault) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(isRegistered[vault], "Not registered");
        isRegistered[vault] = false;
        // Remove from array (swap and pop)
        for (uint256 i = 0; i < registeredVaults.length; i++) {
            if (registeredVaults[i] == vault) {
                registeredVaults[i] = registeredVaults[registeredVaults.length - 1];
                registeredVaults.pop();
                break;
            }
        }
        emit VaultUnregistered(vault);
    }

    /**
     * @notice Batch update yields for all registered vaults.
     * @dev Gas-efficient for keeper bots updating multiple vaults.
     */
    function batchUpdateYields() external onlyRole(UPDATER_ROLE) {
        for (uint256 i = 0; i < registeredVaults.length; i++) {
            address vault = registeredVaults[i];
            KerneVault v = KerneVault(vault);
            uint256 price = v.convertToAssets(1e18);
            
            observations[vault].push(YieldObservation({
                timestamp: block.timestamp,
                sharePrice: price
            }));

            emit YieldUpdated(vault, price, block.timestamp);
        }
    }

    /**
     * @notice Get TWAY with staleness validation for aggregators.
     * @param vault The vault address
     * @return apyBps The annualized yield in basis points
     * @return isStale Whether the data exceeds maxStaleness
     * @return lastUpdate Timestamp of last observation
     */
    function getTWAYWithMeta(address vault) external view returns (
        uint256 apyBps,
        bool isStale,
        uint256 lastUpdate
    ) {
        YieldObservation[] storage obs = observations[vault];
        
        if (obs.length == 0) {
            return (0, true, 0);
        }
        
        lastUpdate = obs[obs.length - 1].timestamp;
        isStale = (block.timestamp - lastUpdate) > maxStaleness;
        apyBps = getTWAY(vault);
    }

    /**
     * @notice Strict TWAY getter that reverts on stale or insufficient data.
     * @dev Use this for on-chain integrations that require fresh data.
     * @param vault The vault address
     * @return apyBps The annualized yield in basis points
     */
    function getTWAYStrict(address vault) external view returns (uint256 apyBps) {
        YieldObservation[] storage obs = observations[vault];
        
        if (obs.length < minObservations) {
            revert InsufficientObservations(vault, obs.length, minObservations);
        }
        
        uint256 lastUpdate = obs[obs.length - 1].timestamp;
        uint256 staleness = block.timestamp - lastUpdate;
        
        if (staleness > maxStaleness) {
            revert StaleData(vault, lastUpdate, staleness);
        }
        
        apyBps = getTWAY(vault);
    }

    /**
     * @notice Get historical APY at a specific point in time.
     * @dev Useful for charting and analytics dashboards.
     * @param vault The vault address
     * @param targetTimestamp The timestamp to query
     * @return apyBps The APY at that time (0 if insufficient data)
     */
    function getHistoricalAPY(address vault, uint256 targetTimestamp) external view returns (uint256 apyBps) {
        YieldObservation[] storage obs = observations[vault];
        if (obs.length < 2) return 0;

        // Find observations around targetTimestamp
        YieldObservation memory targetObs;
        YieldObservation memory priorObs;
        bool foundTarget = false;
        bool foundPrior = false;

        for (uint256 i = obs.length; i > 0; i--) {
            if (!foundTarget && obs[i-1].timestamp <= targetTimestamp) {
                targetObs = obs[i-1];
                foundTarget = true;
            }
            if (foundTarget && obs[i-1].timestamp <= targetTimestamp - yieldWindow) {
                priorObs = obs[i-1];
                foundPrior = true;
                break;
            }
        }

        if (!foundTarget || !foundPrior) return 0;

        uint256 timeDiff = targetObs.timestamp - priorObs.timestamp;
        if (timeDiff == 0 || targetObs.sharePrice <= priorObs.sharePrice) return 0;

        uint256 growth = ((targetObs.sharePrice * 1e18) / priorObs.sharePrice) - 1e18;
        uint256 annualizedGrowth = (growth * 365 days) / timeDiff;
        apyBps = (annualizedGrowth * 10000) / 1e18;
    }

    /**
     * @notice Get all registered vaults and their current APYs.
     * @dev Designed for aggregator dashboards to fetch all data in one call.
     * @return vaults Array of vault addresses
     * @return apys Array of APYs in basis points
     * @return timestamps Array of last update timestamps
     */
    function getAllVaultAPYs() external view returns (
        address[] memory vaults,
        uint256[] memory apys,
        uint256[] memory timestamps
    ) {
        uint256 len = registeredVaults.length;
        vaults = new address[](len);
        apys = new uint256[](len);
        timestamps = new uint256[](len);

        for (uint256 i = 0; i < len; i++) {
            address vault = registeredVaults[i];
            vaults[i] = vault;
            apys[i] = getTWAY(vault);
            
            YieldObservation[] storage obs = observations[vault];
            timestamps[i] = obs.length > 0 ? obs[obs.length - 1].timestamp : 0;
        }
    }

    /**
     * @notice Get observation count for a vault.
     * @param vault The vault address
     * @return count Number of observations recorded
     */
    function getObservationCount(address vault) external view returns (uint256 count) {
        return observations[vault].length;
    }

    /**
     * @notice Set maximum staleness threshold.
     * @param _maxStaleness New staleness threshold in seconds
     */
    function setMaxStaleness(uint256 _maxStaleness) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_maxStaleness >= 1 hours, "Staleness too short");
        maxStaleness = _maxStaleness;
        emit ConfigUpdated("maxStaleness", _maxStaleness);
    }

    /**
     * @notice Set minimum observations required for valid TWAY.
     * @param _minObservations New minimum count
     */
    function setMinObservations(uint256 _minObservations) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_minObservations >= 2, "Min too low");
        minObservations = _minObservations;
        emit ConfigUpdated("minObservations", _minObservations);
    }

    /**
     * @notice Get count of registered vaults.
     * @return count Number of registered vaults
     */
    function getRegisteredVaultCount() external view returns (uint256 count) {
        return registeredVaults.length;
    }
}
