// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { IKerneVault } from "./interfaces/IKerneVault.sol";

interface IKerneVerificationNode {
    struct Attestation {
        uint256 totalAssets;
        uint256 netDelta;
        uint256 exchangeEquity;
        uint256 timestamp;
        bool verified;
    }
    function latestAttestations(address vault) external view returns (uint256, uint256, uint256, uint256, bool);
    function getVerifiedAssets(address vault) external view returns (uint256);
}

/**
 * @title KerneTrustAnchor
 * @author Kerne Protocol
 * @notice Centralized source of truth for institutional solvency verification.
 */
contract KerneTrustAnchor is AccessControl {
    bytes32 public constant AUDITOR_ROLE = keccak256("AUDITOR_ROLE");

    struct SolvencyReport {
        uint256 onChainCollateral;
        uint256 verifiedOffChainEquity;
        uint256 totalLiabilities;
        uint256 solvencyRatio;
        uint256 netDelta;
        uint256 lastAttestationTimestamp;
        bool isSolvent;
    }

    uint256 public constant RATIO_PRECISION = 10000;
    uint256 public minSolvencyThreshold = 10050; // 100.5%

    mapping(address => address) public verificationNodes;

    event SolvencyThresholdUpdated(uint256 newThreshold);
    event VerificationNodeUpdated(address indexed vault, address indexed node);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
    }

    function setVerificationNode(address vault, address node) external onlyRole(DEFAULT_ADMIN_ROLE) {
        verificationNodes[vault] = node;
        emit VerificationNodeUpdated(vault, node);
    }

    function setMinSolvencyThreshold(uint256 threshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(threshold >= 10000, "Threshold below 100%");
        minSolvencyThreshold = threshold;
        emit SolvencyThresholdUpdated(threshold);
    }

    /**
     * @notice Returns a detailed solvency report for a vault.
     */
    function getSolvencyReport(address vault) public view returns (SolvencyReport memory report) {
        IKerneVault v = IKerneVault(vault);
        address nodeAddr = verificationNodes[vault];
        
        report.totalLiabilities = v.totalSupply();
        report.onChainCollateral = v.totalAssets() - v.offChainAssets() - v.hedgingReserve();
        
        if (nodeAddr != address(0)) {
            IKerneVerificationNode node = IKerneVerificationNode(nodeAddr);
            (, uint256 delta, uint256 equity, uint256 ts, bool verified) = node.latestAttestations(vault);
            
            if (verified && block.timestamp - ts <= 24 hours) {
                report.verifiedOffChainEquity = equity;
                report.netDelta = delta;
                report.lastAttestationTimestamp = ts;
            }
        }

        uint256 totalAssets = report.onChainCollateral + report.verifiedOffChainEquity;
        if (report.totalLiabilities > 0) {
            report.solvencyRatio = (totalAssets * RATIO_PRECISION) / report.totalLiabilities;
        } else {
            report.solvencyRatio = 20000; // Solvent if no liabilities
        }

        // Institutional Hardening: Solvent only if ratio >= threshold AND delta is tight
        report.isSolvent = (report.solvencyRatio >= minSolvencyThreshold) && (report.netDelta <= 5e16);
    }

    /**
     * @notice Simple binary solvency check for vault circuit breakers.
     */
    function isSolvent(address vault) external view returns (bool) {
        SolvencyReport memory report = getSolvencyReport(vault);
        return report.isSolvent;
    }
}
