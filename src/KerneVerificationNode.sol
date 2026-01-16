// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ECDSA } from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import { MessageHashUtils } from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

/**
 * @title KerneVerificationNode
 * @notice A cryptographically verifiable Proof of Reserve node.
 * @dev Allows authorized verifiers to submit signed CEX data attestations.
 */
contract KerneVerificationNode is AccessControl {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");

    struct Attestation {
        uint256 totalAssets;
        uint256 netDelta;
        uint256 exchangeEquity;
        uint256 timestamp;
        bool verified;
    }

    mapping(address => Attestation) public latestAttestations;
    mapping(address => bool) public authorizedSigners;
    mapping(bytes32 => uint256) public signatureCounts;
    mapping(bytes32 => mapping(address => bool)) public hasSigned;
    uint256 public threshold = 1;

    event AttestationSubmitted(address indexed vault, uint256 amount, uint256 timestamp, uint256 netDelta, uint256 exchangeEquity);
    event SignerUpdated(address indexed signer, bool status);
    event ThresholdUpdated(uint256 newThreshold);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(VERIFIER_ROLE, admin);
    }

    /**
     * @notice Submits a new attestation with a cryptographic signature.
     * @param vault The address of the KerneVault.
     * @param amount The amount of assets held in custody.
     * @param netDelta The net delta of the hedge positions (scaled by 1e18).
     * @param exchangeEquity The total equity across CEXs.
     * @param timestamp The timestamp of the data.
     * @param signature The signature from an authorized signer.
     */
    function submitVerifiedAttestation(
        address vault,
        uint256 amount,
        uint256 netDelta,
        uint256 exchangeEquity,
        uint256 timestamp,
        bytes calldata signature
    ) external {
        require(block.timestamp - timestamp < 1 hours, "Attestation too old");
        
        bytes32 messageHash = keccak256(abi.encodePacked(vault, amount, netDelta, exchangeEquity, timestamp));
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        address signer = ethSignedMessageHash.recover(signature);
        require(authorizedSigners[signer], "Invalid signer");
        require(!hasSigned[messageHash][signer], "Already signed");

        hasSigned[messageHash][signer] = true;
        uint256 count = ++signatureCounts[messageHash];

        if (count >= threshold) {
            latestAttestations[vault] = Attestation({
                totalAssets: amount,
                netDelta: netDelta,
                exchangeEquity: exchangeEquity,
                timestamp: timestamp,
                verified: true
            });
            emit AttestationSubmitted(vault, amount, timestamp, netDelta, exchangeEquity);
        }
    }

    /**
     * @notice Returns the verified assets for a vault.
     */
    function getVerifiedAssets(address vault) external view returns (uint256) {
        Attestation memory a = latestAttestations[vault];
        if (block.timestamp - a.timestamp > 24 hours) {
            return 0;
        }
        // Solvency hardening: Ensure delta is within acceptable bounds (e.g., < 5%)
        // If delta is too high, we return 0 to trigger circuit breaker in vault
        if (a.netDelta > 5e16) { // 0.05 * 1e18
            return 0;
        }
        return a.verified ? a.totalAssets : 0;
    }

    function setSigner(address signer, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        authorizedSigners[signer] = status;
        emit SignerUpdated(signer, status);
    }

    function setThreshold(uint256 _threshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_threshold > 0, "Threshold must be > 0");
        threshold = _threshold;
        emit ThresholdUpdated(_threshold);
    }
}
