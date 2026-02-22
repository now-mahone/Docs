// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { OApp, Origin, MessagingFee, MessagingReceipt } from "@layerzerolabs/oapp-evm/oapp/OApp.sol";
import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { IMessageRelay } from "../interfaces/IMessageRelay.sol";

/**
 * @title LayerZeroRelay
 * @author Kerne Protocol
 * @notice IMessageRelay adapter backed by LayerZero V2.
 *         Only the KerneMessageRouter may call `sendMessage`.
 *         Incoming `_lzReceive` callbacks are forwarded back to the router.
 */
contract LayerZeroRelay is IMessageRelay, OApp {
    // ──────────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice The KerneMessageRouter that exclusively dispatches outgoing messages
    ///         and receives incoming ones.
    address public router;

    // ──────────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────────

    event RouterUpdated(address indexed oldRouter, address indexed newRouter);
    event MessageSentViaLZ(bytes32 indexed guid, uint32 dstEid);
    event MessageReceivedViaLZ(uint32 indexed srcEid, bytes32 sender, bytes32 indexed guid);

    // ──────────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────────

    error OnlyRouter();
    error RouterNotSet();
    error RouterCallFailed();

    // ──────────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────────

    constructor(address _endpoint, address _delegate) OApp(_endpoint, _delegate) Ownable(_delegate) {}

    // ──────────────────────────────────────────────────────────────────────────
    // Admin
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Sets the address of the KerneMessageRouter.
    function setRouter(address _router) external onlyOwner {
        emit RouterUpdated(router, _router);
        router = _router;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // IMessageRelay — send
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageRelay
    /// @dev `destinationChainId` is treated as the LayerZero endpoint ID (EID).
    ///      `extraArgs` should be a LayerZero `Options` bytes blob (e.g. from
    ///      `OptionsBuilder.newOptions().addExecutorLzReceiveOption(...)`).
    ///      Any surplus ETH beyond the quoted fee is refunded to the caller.
    function sendMessage(
        uint32 destinationChainId,
        address, /* target — encoded inside payload by the router */
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable override returns (bytes32 messageId) {
        if (msg.sender != router) revert OnlyRouter();

        MessagingReceipt memory receipt = _lzSend(
            destinationChainId,
            payload,
            extraArgs,
            MessagingFee({ nativeFee: msg.value, lzTokenFee: 0 }),
            payable(tx.origin) // surplus-gas refund goes back to the EOA
        );

        emit MessageSentViaLZ(receipt.guid, destinationChainId);
        return receipt.guid;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // IMessageRelay — fee quotation
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageRelay
    function estimateFee(
        uint32 destinationChainId,
        address, /* target */
        bytes calldata payload,
        bytes calldata extraArgs
    ) external view override returns (uint256 fee) {
        MessagingFee memory lzFee = _quote(destinationChainId, payload, extraArgs, false);
        return lzFee.nativeFee;
    }

    // ──────────────────────────────────────────────────────────────────────────
    // OApp — incoming message callback
    // ──────────────────────────────────────────────────────────────────────────

    /// @dev Called by the LayerZero endpoint when a message arrives from a remote chain.
    ///      Forwards the payload and source metadata to the KerneMessageRouter.
    function _lzReceive(
        Origin calldata _origin,
        bytes32 _guid,
        bytes calldata _message,
        address, /* _executor */
        bytes calldata /* _extraData */
    ) internal override {
        if (router == address(0)) revert RouterNotSet();

        emit MessageReceivedViaLZ(_origin.srcEid, _origin.sender, _guid);

        // Derive sender address from bytes32 (LayerZero stores it right-padded)
        address senderAddr = address(uint160(uint256(_origin.sender)));

        (bool success,) = router.call(
            abi.encodeWithSignature(
                "receiveMessage(uint32,address,bytes)", _origin.srcEid, senderAddr, _message
            )
        );
        if (!success) revert RouterCallFailed();
    }
}