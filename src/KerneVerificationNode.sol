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
        uint256 timestamp;
        bool verified;
    }

    mapping(address => Attestation) public latestAttestations;
    mapping(address => bool) public authorizedSigners;

    event AttestationSubmitted(address indexed vault, uint256 amount, uint256 timestamp);
    event SignerUpdated(address indexed signer, bool status);

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(VERIFIER_ROLE, admin);
    }

    /**
     * @notice Submits a new attestation with a cryptographic signature.
     * @param vault The address of the KerneVault.
     * @param amount The amount of assets held in custody.
     * @param timestamp The timestamp of the data.
     * @param signature The signature from an authorized signer.
     */
    function submitVerifiedAttestation(
        address vault,
        uint256 amount,
        uint256 timestamp,
        bytes calldata signature
    ) external {
        require(block.timestamp - timestamp < 1 hours, "Attestation too old");
        
        bytes32 messageHash = keccak256(abi.encodePacked(vault, amount, timestamp));
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        address signer = ethSignedMessageHash.recover(signature);
        require(authorizedSigners[signer], "Invalid signer");

        latestAttestations[vault] = Attestation({
            totalAssets: amount,
            timestamp: timestamp,
            verified: true
        });

        emit AttestationSubmitted(vault, amount, timestamp);
    }

    /**
     * @notice Returns the verified assets for a vault.
     */
    function getVerifiedAssets(address vault) external view returns (uint256) {
        Attestation memory a = latestAttestations[vault];
        if (block.timestamp - a.timestamp > 24 hours) {
            return 0;
        }
        return a.verified ? a.totalAssets : 0;
    }

    function setSigner(address signer, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        authorizedSigners[signer] = status;
        emit SignerUpdated(signer, status);
    }
}
