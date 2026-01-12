// Created: 2026-01-12
// Updated: 2026-01-12 - Strengthened with LayerZero V2 OApp patterns
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { MerkleProof } from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import { OApp, Origin, MessagingFee } from "@layerzerolabs/oapp-evm/contracts/oapp/OApp.sol";
import { OptionsBuilder } from "@layerzerolabs/oapp-evm/contracts/oapp/libs/OptionsBuilder.sol";

/**
 * @title KerneYieldAttestation
 * @notice Cryptographic proof of yield engine for institutional auditing.
 * @dev Integrated with LayerZero V2 for cross-chain yield verification.
 */
contract KerneYieldAttestation is OApp {
    using OptionsBuilder for bytes;

    struct Attestation {
        bytes32 merkleRoot;
        uint256 timestamp;
        uint256 totalYieldGenerated;
        string ipfsHash; // Detailed breakdown of funding cycles
    }

    mapping(address => Attestation[]) public vaultAttestations;

    event AttestationPublished(address indexed vault, bytes32 merkleRoot, uint256 totalYield);
    event AttestationSynced(uint32 dstEid, bytes32 merkleRoot);

    constructor(address _endpoint, address _owner) OApp(_endpoint, _owner) {}

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
     * @notice Syncs an attestation to another chain via LayerZero V2.
     */
    function syncAttestation(
        uint32 _dstEid,
        address _vault,
        uint256 _index,
        bytes calldata _options
    ) external payable onlyOwner {
        Attestation memory att = vaultAttestations[_vault][_index];
        bytes memory payload = abi.encode(_vault, att.merkleRoot, att.totalYieldGenerated, att.timestamp);
        
        _lzSend(
            _dstEid,
            payload,
            _options,
            MessagingFee(msg.value, 0),
            payable(msg.sender)
        );

        emit AttestationSynced(_dstEid, att.merkleRoot);
    }

    /**
     * @dev Internal LayerZero receiver logic.
     */
    function _lzReceive(
        Origin calldata /*_origin*/,
        bytes32 /*_guid*/,
        bytes calldata _message,
        address /*_executor*/,
        bytes calldata /*_extraData*/
    ) internal override {
        (address vault, bytes32 merkleRoot, uint256 totalYield, uint256 timestamp) = abi.decode(
            _message,
            (address, bytes32, uint256, uint256)
        );

        vaultAttestations[vault].push(Attestation({
            merkleRoot: merkleRoot,
            timestamp: timestamp,
            totalYieldGenerated: totalYield,
            ipfsHash: "SYNCED_VIA_LZ"
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
