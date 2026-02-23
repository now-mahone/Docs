// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

/**
 * @title IMessageRelay
 * @author Kerne Protocol
 * @notice Standard interface for all cross-chain messaging protocol adapters.
 *         Abstracts away LayerZero, Wormhole, CCIP, and future protocols behind
 *         a single API so the router can switch or multi-route without code changes.
 */
interface IMessageRelay {
    /// @notice Sends a cross-chain message to `target` on `destinationChainId`.
    /// @param destinationChainId  Protocol-agnostic chain identifier (protocol adapters
    ///                            map this to their own chain ID / EID internally).
    /// @param target              Address of the recipient contract on the destination chain.
    /// @param payload             ABI-encoded message payload.
    /// @param extraArgs           Protocol-specific encoding (e.g. gas limit options).
    /// @return messageId          Unique identifier for the sent message.
    function sendMessage(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable returns (bytes32 messageId);

    /// @notice Quotes the native-gas fee required to send a message.
    /// @param destinationChainId  Protocol-agnostic chain identifier.
    /// @param target              Address of the recipient contract on the destination chain.
    /// @param payload             ABI-encoded message payload.
    /// @param extraArgs           Protocol-specific encoding.
    /// @return fee                Estimated fee in native gas tokens.
    function estimateFee(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external view returns (uint256 fee);
}

/**
 * @title IMessageReceiver
 * @notice Interface that any contract wishing to receive abstracted cross-chain
 *         messages must implement.
 */
interface IMessageReceiver {
    /// @notice Handles an incoming cross-chain message forwarded by the router.
    /// @param sourceChainId  Protocol-agnostic identifier of the source chain.
    /// @param sender         Address of the sender contract on the source chain.
    /// @param payload        ABI-encoded message payload.
    function receiveMessage(uint32 sourceChainId, address sender, bytes calldata payload) external;
}