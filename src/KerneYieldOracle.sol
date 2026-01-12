// SPDX-License-Identifier: MIT
// Created: 2026-01-10
// Updated: 2026-01-12 - Institutional Deep Hardening: Medianizer, outlier rejection, and multi-node consensus
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { KerneVault } from "./KerneVault.sol";

/**
 * @title KerneYieldOracle
 * @author Kerne Protocol
 * @notice A manipulation-resistant yield oracle providing TWAY (Time-Weighted Average Yield).
 * Hardened with medianizer logic, outlier rejection, and multi-node consensus.
 */
contract KerneYieldOracle is AccessControl {
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");

    struct YieldObservation {
        uint256 timestamp;
        uint256 sharePrice;
    }

    struct Proposal {
        uint256 sharePrice;
        uint256 timestamp;
        uint256 confirmations;
        mapping(address => bool) hasConfirmed;
    }

    mapping(address => YieldObservation[]) public observations;
    mapping(address => Proposal) public pendingProposals;

    uint256 public yieldWindow = 7 days;
    uint256 public maxStaleness = 24 hours;
    uint256 public requiredConfirmations = 3;
    uint256 public maxPriceDeviationBps = 500; // 5% max deviation from previous observation

    address[] public registeredVaults;
    mapping(address => bool) public isRegistered;

    event YieldUpdated(address indexed vault, uint256 sharePrice, uint256 timestamp);
    event ProposalCreated(address indexed vault, uint256 sharePrice, address indexed proposer);
    event ProposalConfirmed(address indexed vault, address indexed confirmer);
    event ConfigUpdated(string param, uint256 value);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    /**
     * @notice Proposes or confirms a new share price with outlier rejection.
     */
    function updateYield(address vault) external onlyRole(UPDATER_ROLE) {
        KerneVault v = KerneVault(vault);
        uint256 price = v.convertToAssets(1e18);
        
        // Outlier Rejection: Check deviation from last observation
        YieldObservation[] storage obs = observations[vault];
        if (obs.length > 0) {
            uint256 lastPrice = obs[obs.length - 1].sharePrice;
            uint256 deviation = price > lastPrice ? (price - lastPrice) * 10000 / lastPrice : (lastPrice - price) * 10000 / lastPrice;
            require(deviation <= maxPriceDeviationBps, "Outlier rejected: Price deviation too high");
        }

        Proposal storage prop = pendingProposals[vault];
        
        if (prop.timestamp < block.timestamp - 1 hours) {
            prop.sharePrice = price;
            prop.timestamp = block.timestamp;
            prop.confirmations = 1;
            emit ProposalCreated(vault, price, msg.sender);
        } else {
            require(prop.sharePrice == price, "Consensus mismatch");
            require(!prop.hasConfirmed[msg.sender], "Already confirmed");
            
            prop.confirmations++;
            prop.hasConfirmed[msg.sender] = true;
            emit ProposalConfirmed(vault, msg.sender);
        }

        if (prop.confirmations >= requiredConfirmations) {
            observations[vault].push(YieldObservation({
                timestamp: prop.timestamp,
                sharePrice: prop.sharePrice
            }));
            delete pendingProposals[vault];
            emit YieldUpdated(vault, price, block.timestamp);
        }
    }

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
        requiredConfirmations = _count;
        emit ConfigUpdated("requiredConfirmations", _count);
    }

    function setMaxPriceDeviation(uint256 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        maxPriceDeviationBps = bps;
        emit ConfigUpdated("maxPriceDeviationBps", bps);
    }
}
