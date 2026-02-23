// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { IMessageRelay } from "../interfaces/IMessageRelay.sol";

// ─────────────────────────────────────────────────────────────────────────────
// Minimal Wormhole Automatic Relayer interface
// Full spec: https://docs.wormhole.com/wormhole/quick-start/tutorials/relayers
// ─────────────────────────────────────────────────────────────────────────────

/// @dev Standard Wormhole IWormholeRelayer interface for automatic EVM relaying.
interface IWormholeRelayer {
    /// @notice Send a payload to an EVM contract on another chain.
    function sendPayloadToEvm(
        uint16 targetChain,
        address targetAddress,
        bytes memory payload,
        uint256 receiverValue,
        uint256 gasLimit,
        uint16 refundChain,
        address refundAddress
    ) external payable returns (uint64 sequence);

    /// @notice Quote the fee for a cross-chain delivery.
    function quoteEVMDeliveryPrice(
        uint16 targetChain,
        uint256 receiverValue,
        uint256 gasLimit
    ) external view returns (uint256 nativePriceQuote, uint256 targetChainRefundPerGasUnused);
}

/**
 * @title WormholeRelay
 * @author Kerne Protocol
 * @notice IMessageRelay adapter backed by the Wormhole Automatic Relayer.
 *         Only the KerneMessageRouter may call `sendMessage`.
 *         The Wormhole relayer calls `receiveWormholeMessages` on delivery.
 *
 * @dev Chain ID mapping:  Wormhole uses its own 16-bit chain IDs; the router
 *      passes the canonical Wormhole chain ID as `destinationChainId` (cast to uint16).
 *      `extraArgs` is ABI-encoded as a single `uint256 gasLimit` value.
 *      Default gas limit falls back to 200 000 when `extraArgs` is empty.
 */
contract WormholeRelay is IMessageRelay, Ownable {
    // ──────────────────────────────────────────────────────────────────────────
    // Constants
    // ──────────────────────────────────────────────────────────────────────────

    uint256 public constant DEFAULT_GAS_LIMIT = 200_000;

    // ──────────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────────

    address public router;
    IWormholeRelayer public immutable wormholeRelayer;

    // ──────────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────────

    event RouterUpdated(address indexed oldRouter, address indexed newRouter);
    event MessageSentViaWormhole(uint64 indexed sequence, uint16 targetChain);
    event MessageReceivedViaWormhole(uint16 indexed sourceChain, bytes32 sourceAddress);

    // ──────────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────────

    error OnlyRouter();
    error OnlyWormholeRelayer();
    error RouterNotSet();
    error RouterCallFailed();

    // ──────────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────────

    constructor(address _wormholeRelayer, address _delegate) Ownable(_delegate) {
        wormholeRelayer = IWormholeRelayer(_wormholeRelayer);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Admin
    // ──────────────────────────────────────────────────────────────────────────

    function setRouter(address _router) external onlyOwner {
        emit RouterUpdated(router, _router);
        router = _router;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // IMessageRelay — send
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageRelay
    /// @dev `destinationChainId` must be the Wormhole chain ID (uint16 range).
    ///      `extraArgs` is ABI-encoded `uint256 gasLimit`; empty → 200 000.
    function sendMessage(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable override returns (bytes32 messageId) {
        if (msg.sender != router) revert OnlyRouter();

        uint256 gasLimit = extraArgs.length > 0 ? abi.decode(extraArgs, (uint256)) : DEFAULT_GAS_LIMIT;
        uint16 targetChain = uint16(destinationChainId);

        uint64 sequence = wormholeRelayer.sendPayloadToEvm{ value: msg.value }(
            targetChain,
            target,
            payload,
            0, // receiverValue (no native gas forwarded to target)
            gasLimit,
            targetChain, // refundChain = destination chain
            msg.sender // refundAddress
        );

        emit MessageSentViaWormhole(sequence, targetChain);
        return bytes32(uint256(sequence));
    }

    // ──────────────────────────────────────────────────────────────────────────
    // IMessageRelay — fee quotation
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageRelay
    function estimateFee(
        uint32 destinationChainId,
        address, /* target */
        bytes calldata, /* payload */
        bytes calldata extraArgs
    ) external view override returns (uint256 fee) {
        uint256 gasLimit = extraArgs.length > 0 ? abi.decode(extraArgs, (uint256)) : DEFAULT_GAS_LIMIT;
        (uint256 nativePriceQuote,) =
            wormholeRelayer.quoteEVMDeliveryPrice(uint16(destinationChainId), 0, gasLimit);
        return nativePriceQuote;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Wormhole Automatic Relayer — incoming delivery callback
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Called by the Wormhole Automatic Relayer on the destination chain.
    /// @param payload        The original payload sent by the source contract.
    /// @param sourceAddress  bytes32-encoded address of the source contract.
    /// @param sourceChain    Wormhole chain ID of the source chain.
    function receiveWormholeMessages(
        bytes memory payload,
        bytes[] memory, /* additionalVaas — not used */
        bytes32 sourceAddress,
        uint16 sourceChain,
        bytes32 /* deliveryHash */
    ) external payable {
        if (msg.sender != address(wormholeRelayer)) revert OnlyWormholeRelayer();
        if (router == address(0)) revert RouterNotSet();

        address senderAddr = address(uint160(uint256(sourceAddress)));
        emit MessageReceivedViaWormhole(sourceChain, sourceAddress);

        (bool success,) = router.call(
            abi.encodeWithSignature(
                "receiveMessage(uint32,address,bytes)", uint32(sourceChain), senderAddr, payload
            )
        );
        if (!success) revert RouterCallFailed();
    }
}