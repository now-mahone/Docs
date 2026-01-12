// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";

/**
 * @title KerneYieldAttestation
 * @notice Cryptographic proof of yield engine for institutional auditing.
 */
contract KerneYieldAttestation is Ownable {
    struct Attestation {
        bytes32 merkleRoot;
        uint256 timestamp;
        uint256 totalYieldGenerated;
        string ipfsHash; // Detailed breakdown of funding cycles
    }

    mapping(address => Attestation[]) public vaultAttestations;

    event AttestationPublished(address indexed vault, bytes32 merkleRoot, uint256 totalYield);

    constructor() Ownable(msg.sender) {}

    /**
     * @notice Publishes a new yield attestation for a vault.
     */
    function publishAttestation(
        address vault,
        bytes32 merkleRoot,
        uint256 totalYield,
        string calldata ipfsHash
    ) external onlyOwner {
        vaultAttestations[vault].push(Attestation({
            merkleRoot: merkleRoot,
            timestamp: block.timestamp,
            totalYieldGenerated: totalYield,
            ipfsHash: ipfsHash
        }));

        emit AttestationPublished(vault, merkleRoot, totalYield);
    }

    /**
     * @notice Verifies a specific yield event against an attestation.
     */
    function verifyYieldEvent(
        address vault,
        uint256 index,
        bytes32 leaf,
        bytes32[] calldata proof
    ) external view returns (bool) {
        require(index < vaultAttestations[vault].length, "Invalid index");
        bytes32 root = vaultAttestations[vault][index].merkleRoot;
        return MerkleProof.verify(proof, root, leaf);
    }

    function getAttestationCount(address vault) external view returns (uint256) {
        return vaultAttestations[vault].length;
    }
}
