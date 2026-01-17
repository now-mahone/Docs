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
        uint256 lastAuditorPulse;
        bool isSolvent;
    }

    uint256 public constant RATIO_PRECISION = 10000;
    uint256 public minSolvencyThreshold = 10050; // 100.5%
    uint256 public constant AUDITOR_PULSE_WINDOW = 48 hours;

    mapping(address => address) public verificationNodes;
    mapping(address => uint256) public lastAuditorPulses;
    mapping(address => bool) public auditorEmergencyFlag;

    event SolvencyThresholdUpdated(uint256 newThreshold);
    event VerificationNodeUpdated(address indexed vault, address indexed node);
    event AuditorPulseSubmitted(address indexed vault, address indexed auditor, uint256 timestamp);
    event EmergencyFlagRaised(address indexed vault, address indexed auditor);

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
     * @notice Allows an auditor to submit a solvency pulse, confirming off-chain reserves.
     */
    function submitAuditorPulse(address vault) external onlyRole(AUDITOR_ROLE) {
        lastAuditorPulses[vault] = block.timestamp;
        auditorEmergencyFlag[vault] = false;
        emit AuditorPulseSubmitted(vault, msg.sender, block.timestamp);
    }

    /**
     * @notice Allows an auditor to raise an emergency flag, triggering a vault pause.
     */
    function raiseEmergencyFlag(address vault) external onlyRole(AUDITOR_ROLE) {
        auditorEmergencyFlag[vault] = true;
        emit EmergencyFlagRaised(vault, msg.sender);
        
        // Trigger pause on vault if possible
        IKerneVault v = IKerneVault(vault);
        try v.pause() {} catch {}
    }

    /**
     * @notice Returns a detailed solvency report for a vault.
     */
    function getSolvencyReport(address vault) public view returns (SolvencyReport memory report) {
        IKerneVault v = IKerneVault(vault);
        address nodeAddr = verificationNodes[vault];
        
        report.totalLiabilities = v.totalSupply();
        
        uint256 total = v.totalAssets();
        uint256 offChain = v.offChainAssets();
        uint256 reserve = v.hedgingReserve();
        
        if (total >= offChain + reserve) {
            report.onChainCollateral = total - offChain - reserve;
        } else {
            report.onChainCollateral = 0;
        }

        report.lastAuditorPulse = lastAuditorPulses[vault];
        
        if (nodeAddr != address(0)) {
            IKerneVerificationNode node = IKerneVerificationNode(nodeAddr);
            (uint256 offChainAttested, uint256 delta, , uint256 ts, bool verified) = node.latestAttestations(vault);
            
            if (verified && block.timestamp - ts <= 24 hours) {
                report.verifiedOffChainEquity = offChainAttested;
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

        // Institutional Hardening: Solvent only if:
        // 1. Ratio >= threshold
        // 2. Delta is tight (<= 5%)
        // 3. No auditor emergency flag is raised
        // 4. Auditor pulse is fresh (Institutional Hardening)
        bool auditFresh = (block.timestamp - report.lastAuditorPulse <= AUDITOR_PULSE_WINDOW);
        bool basicSolvency = (report.solvencyRatio >= minSolvencyThreshold) && (report.netDelta <= 5e16);
        report.isSolvent = basicSolvency && !auditorEmergencyFlag[vault] && auditFresh;
    }

    /**
     * @notice Simple binary solvency check for vault circuit breakers.
     */
    function isSolvent(address vault) external view returns (bool) {
        SolvencyReport memory report = getSolvencyReport(vault);
        return report.isSolvent;
    }
}
