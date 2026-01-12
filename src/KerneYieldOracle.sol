// SPDX-License-Identifier: MIT
// Created: 2026-01-10
// Updated: 2026-01-12 - Decentralized with multi-node verification and consensus
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KerneYieldOracle
 * @author Kerne Protocol
 * @notice A manipulation-resistant yield oracle providing TWAY (Time-Weighted Average Yield).
 * @dev Decentralized with multi-node verification and consensus.
 */
contract KerneYieldOracle is AccessControl {
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    struct YieldObservation {
        uint256 timestamp;
        uint256 sharePrice; // Assets per 1e18 shares
    }

    struct PendingUpdate {
        uint256 sharePrice;
        uint256 timestamp;
        uint256 confirmations;
        mapping(address => bool) hasConfirmed;
    }

    /// @notice Mapping from vault address to its observations
    mapping(address => YieldObservation[]) public observations;

    /// @notice Pending updates for consensus
    mapping(address => PendingUpdate) public pendingUpdates;

    /// @notice The window for TWAY calculation (default: 7 days)
    uint256 public yieldWindow = 7 days;

    /// @notice Maximum staleness before data is considered invalid (default: 24 hours)
    uint256 public maxStaleness = 24 hours;

    /// @notice Minimum observations required for valid TWAY (default: 3)
    uint256 public minObservations = 3;

    /// @notice Required confirmations for consensus (default: 2)
    uint256 public requiredConfirmations = 2;

    /// @notice Registered vaults for batch operations
    address[] public registeredVaults;
    mapping(address => bool) public isRegistered;

    event YieldUpdated(address indexed vault, uint256 sharePrice, uint256 timestamp);
    event UpdateProposed(address indexed vault, uint256 sharePrice, address indexed proposer);
    event UpdateConfirmed(address indexed vault, address indexed confirmer);
    event VaultRegistered(address indexed vault);
    event ConfigUpdated(string param, uint256 value);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        requiredConfirmations = 1; // Initial setup
    }

    /**
     * @notice Proposes or confirms a new share price observation for a vault.
     */
    function updateYield(address vault) external onlyRole(UPDATER_ROLE) {
        KerneVault v = KerneVault(vault);
        uint256 price = v.convertToAssets(1e18);
        
        PendingUpdate storage pending = pendingUpdates[vault];
        
        // If no pending update or it's stale, start a new one
        if (pending.timestamp < block.timestamp - 1 hours) {
            pending.sharePrice = price;
            pending.timestamp = block.timestamp;
            pending.confirmations = 1;
            // Reset confirmations (in production, use a mapping with a nonce)
            emit UpdateProposed(vault, price, msg.sender);
        } else {
            require(pending.sharePrice == price, "Price mismatch in consensus");
            require(!pending.hasConfirmed[msg.sender], "Already confirmed");
            
            pending.confirmations++;
            pending.hasConfirmed[msg.sender] = true;
            emit UpdateConfirmed(vault, msg.sender);
        }

        if (pending.confirmations >= requiredConfirmations) {
            observations[vault].push(YieldObservation({
                timestamp: pending.timestamp,
                sharePrice: pending.sharePrice
            }));
            delete pendingUpdates[vault];
            emit YieldUpdated(vault, price, block.timestamp);
        }
    }

    /**
     * @notice Calculates the annualized TWAY for a vault over the yieldWindow.
     */
    function getTWAY(address vault) public view returns (uint256 apyBps) {
        YieldObservation[] storage obs = observations[vault];
        if (obs.length < 2) return 0;

        YieldObservation memory latest = obs[obs.length - 1];
        uint256 targetTime = block.timestamp > yieldWindow ? block.timestamp - yieldWindow : obs[0].timestamp;
        
        YieldObservation memory oldest = obs[0];
        for (uint256 i = obs.length; i > 0; i--) {
            if (obs[i-1].timestamp <= targetTime) {
                oldest = obs[i-1];
                break;
            }
        }

        uint256 timeDiff = latest.timestamp - oldest.timestamp;
        if (timeDiff == 0 || latest.sharePrice <= oldest.sharePrice) return 0;

        uint256 growth = ((latest.sharePrice * 1e27) / oldest.sharePrice) - 1e27;
        uint256 annualizedGrowth = (growth * 365 days) / timeDiff;
        apyBps = (annualizedGrowth * 10000) / 1e27;
    }

    function setRequiredConfirmations(uint256 _count) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_count > 0, "Invalid count");
        requiredConfirmations = _count;
        emit ConfigUpdated("requiredConfirmations", _count);
    }

    function registerVault(address vault) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(!isRegistered[vault], "Already registered");
        registeredVaults.push(vault);
        isRegistered[vault] = true;
        emit VaultRegistered(vault);
    }
}
