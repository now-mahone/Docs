// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ECDSA } from "@openzeppelin/contracts/utils/cryptography/ECDSA.sol";
import { MessageHashUtils } from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";
import { OApp, Origin, MessagingFee } from "@layerzerolabs/oapp-evm/oapp/OApp.sol";

/**
 * @title KerneVerificationNode
 * @notice A cryptographically verifiable Proof of Reserve node.
 * @dev Allows authorized verifiers to submit signed CEX data attestations.
 *      Integrated with LayerZero V2 for cross-chain solvency sync.
 */
contract KerneVerificationNode is AccessControl, OApp {
    using ECDSA for bytes32;
    using MessageHashUtils for bytes32;

    bytes32 public constant VERIFIER_ROLE = keccak256("VERIFIER_ROLE");

    struct Attestation {
        uint256 offChainAssets;
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
    uint256 public authorizedSignerCount;

    event AttestationSubmitted(address indexed vault, uint256 offChainAssets, uint256 timestamp, uint256 netDelta, uint256 exchangeEquity);
    event SignerUpdated(address indexed signer, bool status);
    event ThresholdUpdated(uint256 newThreshold);
    event AttestationSynced(uint32 dstEid, address vault);

    constructor(address _endpoint, address _delegate) OApp(_endpoint, _delegate) {
        _grantRole(DEFAULT_ADMIN_ROLE, _delegate);
        _grantRole(VERIFIER_ROLE, _delegate);
    }

    /**
     * @notice Submits a new attestation with a cryptographic signature.
     * @param vault The address of the KerneVault.
     * @param offChainAssets The amount of assets held in custody off-chain.
     * @param netDelta The net delta of the hedge positions (scaled by 1e18).
     * @param exchangeEquity The total equity across CEXs.
     * @param timestamp The timestamp of the data.
     * @param signature The signature from an authorized signer.
     */
    function submitVerifiedAttestation(
        address vault,
        uint256 offChainAssets,
        uint256 netDelta,
        uint256 exchangeEquity,
        uint256 timestamp,
        bytes calldata signature
    ) external {
        require(block.timestamp - timestamp < 1 hours, "Attestation too old");
        
        bytes32 messageHash = keccak256(abi.encodePacked(
            block.chainid,
            address(this),
            vault, 
            offChainAssets, 
            netDelta, 
            exchangeEquity, 
            timestamp
        ));
        bytes32 ethSignedMessageHash = messageHash.toEthSignedMessageHash();
        
        address signer = ethSignedMessageHash.recover(signature);
        require(authorizedSigners[signer], "Invalid signer");
        require(!hasSigned[messageHash][signer], "Already signed");

        hasSigned[messageHash][signer] = true;
        uint256 count = ++signatureCounts[messageHash];

        if (count >= threshold) {
            latestAttestations[vault] = Attestation({
                offChainAssets: offChainAssets,
                netDelta: netDelta,
                exchangeEquity: exchangeEquity,
                timestamp: timestamp,
                verified: true
            });
            emit AttestationSubmitted(vault, offChainAssets, timestamp, netDelta, exchangeEquity);
        }
    }

    /**
     * @notice Synchronizes the latest verified attestation to a destination chain.
     * @param _dstEid The destination endpoint ID.
     * @param _vault The vault address to sync.
     * @param _options LayerZero execution options.
     */
    function syncAttestation(
        uint32 _dstEid,
        address _vault,
        bytes calldata _options
    ) external payable onlyRole(VERIFIER_ROLE) {
        Attestation memory a = latestAttestations[_vault];
        require(a.verified, "Attestation not verified");
        
        bytes memory payload = abi.encode(_vault, a.offChainAssets, a.netDelta, a.exchangeEquity, a.timestamp);
        
        _lzSend(
            _dstEid,
            payload,
            _options,
            MessagingFee(msg.value, 0),
            payable(msg.sender)
        );
        
        emit AttestationSynced(_dstEid, _vault);
    }

    /**
     * @notice Internal function to handle received messages from LayerZero.
     */
    function _lzReceive(
        Origin calldata /*_origin*/,
        bytes32 /*_guid*/,
        bytes calldata _message,
        address /*_executor*/,
        bytes calldata /*_extraData*/
    ) internal override {
        (address vault, uint256 offChainAssets, uint256 netDelta, uint256 exchangeEquity, uint256 timestamp) = 
            abi.decode(_message, (address, uint256, uint256, uint256, uint256));
            
        // Security Hardening: Validate timestamp freshness and ordering
        require(block.timestamp - timestamp < 2 hours, "Stale cross-chain attestation");
        
        Attestation memory existing = latestAttestations[vault];
        require(timestamp > existing.timestamp, "Attestation not newer");

        // Update with cross-chain data
        latestAttestations[vault] = Attestation({
            offChainAssets: offChainAssets,
            netDelta: netDelta,
            exchangeEquity: exchangeEquity,
            timestamp: timestamp,
            verified: true
        });
        
        emit AttestationSubmitted(vault, offChainAssets, timestamp, netDelta, exchangeEquity);
    }

    /**
     * @notice Quotes the fee for syncing an attestation.
     */
    function quote(
        uint32 _dstEid,
        address _vault,
        bytes calldata _options,
        bool _payInLzToken
    ) public view returns (MessagingFee memory fee) {
        Attestation memory a = latestAttestations[_vault];
        bytes memory payload = abi.encode(_vault, a.offChainAssets, a.netDelta, a.exchangeEquity, a.timestamp);
        fee = _quote(_dstEid, payload, _options, _payInLzToken);
    }


    /**
     * @notice Returns the verified off-chain assets for a vault.
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
        return a.verified ? a.offChainAssets : 0;
    }

    function setSigner(address signer, bool status) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (status && !authorizedSigners[signer]) authorizedSignerCount++;
        else if (!status && authorizedSigners[signer]) authorizedSignerCount--;
        authorizedSigners[signer] = status;
        emit SignerUpdated(signer, status);
    }

    function setThreshold(uint256 _threshold) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(_threshold > 0 && _threshold <= authorizedSignerCount, "Invalid threshold");
        threshold = _threshold;
        emit ThresholdUpdated(_threshold);
    }
}
