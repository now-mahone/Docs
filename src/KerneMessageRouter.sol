// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";
import { IMessageRelay, IMessageReceiver } from "./interfaces/IMessageRelay.sol";

/**
 * @title KerneMessageRouter
 * @author Kerne Protocol
 * @notice Central hub for all Kerne cross-chain messaging.
 *
 *  Architecture
 *  ┌─────────────┐    sendMessage()    ┌────────────────────┐    protocol call   ┌─────────────────┐
 *  │  Authorized │ ──────────────────► │ KerneMessageRouter │ ─────────────────► │  IMessageRelay  │
 *  │  Sender     │                     │   (this contract)  │                    │  (LZ/WH/CCIP)   │
 *  └─────────────┘                     └────────────────────┘                    └─────────────────┘
 *                                              ▲
 *                                  receiveMessage() from relay adapter
 *                                              │
 *                                    forwards to Authorized Receiver
 *
 *  Key properties
 *  • Multiple relay adapters registered under protocol IDs (1=LZ, 2=WH, 3=CCIP).
 *  • A `defaultProtocolId` is used for vanilla `sendMessage` calls.
 *  • `sendMessageWithProtocol` allows explicit adapter selection.
 *  • `sendMessageMulti` broadcasts to N adapters simultaneously for maximum
 *    resilience: the first successful delivery wins on the destination chain.
 *  • Access control prevents arbitrary contracts from dispatching or receiving.
 *  • Emergency pause via `PAUSER_ROLE`.
 */
contract KerneMessageRouter is AccessControl, Pausable, IMessageReceiver {
    // ──────────────────────────────────────────────────────────────────────────
    // Roles
    // ──────────────────────────────────────────────────────────────────────────

    bytes32 public constant ROUTER_ADMIN_ROLE = keccak256("ROUTER_ADMIN_ROLE");
    bytes32 public constant PAUSER_ROLE = keccak256("PAUSER_ROLE");

    // ──────────────────────────────────────────────────────────────────────────
    // Protocol IDs (canonical constants — adapters registered under these keys)
    // ──────────────────────────────────────────────────────────────────────────

    uint8 public constant PROTOCOL_LAYERZERO = 1;
    uint8 public constant PROTOCOL_WORMHOLE = 2;
    uint8 public constant PROTOCOL_CCIP = 3;

    // ──────────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice protocolId → IMessageRelay adapter address.
    mapping(uint8 => IMessageRelay) public relays;

    /// @notice Set of all registered relay adapter addresses for O(1) auth check.
    mapping(address => bool) public authorizedRelays;

    /// @notice Default protocol used when caller does not specify one.
    uint8 public defaultProtocolId;

    /// @notice destinationChainId → target KerneMessageRouter address on that chain.
    mapping(uint32 => address) public targetRouters;

    /// @notice Contracts on *this* chain allowed to dispatch outgoing messages.
    mapping(address => bool) public authorizedSenders;

    /// @notice Contracts on *this* chain allowed to receive incoming messages.
    mapping(address => bool) public authorizedReceivers;

    // ──────────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────────

    event RelayRegistered(uint8 indexed protocolId, address relay);
    event RelayRemoved(uint8 indexed protocolId);
    event DefaultProtocolUpdated(uint8 protocolId);
    event TargetRouterUpdated(uint32 indexed chainId, address targetRouter);
    event SenderAuthorized(address indexed sender, bool authorized);
    event ReceiverAuthorized(address indexed receiver, bool authorized);
    event MessageDispatched(
        bytes32 indexed messageId,
        uint8 indexed protocolId,
        uint32 destinationChainId,
        address target,
        bytes payload
    );
    event MessageDelivered(uint32 indexed sourceChainId, address sender, address target, bytes payload);
    event MultiSendAttempt(uint8 protocolId, bool success);

    // ──────────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────────

    error UnauthorizedSender(address caller);
    error UnauthorizedReceiver(address target);
    error UnauthorizedRelay(address caller);
    error UnauthorizedSourceRouter(uint32 chainId, address sender);
    error RelayNotConfigured(uint8 protocolId);
    error TargetRouterNotConfigured(uint32 chainId);
    error DefaultProtocolNotSet();
    error NoRelaySucceeded();

    // ──────────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────────

    constructor(address admin) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(ROUTER_ADMIN_ROLE, admin);
        _grantRole(PAUSER_ROLE, admin);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Admin — relay management
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Register or replace a relay adapter.
    /// @param protocolId  One of PROTOCOL_LAYERZERO / PROTOCOL_WORMHOLE / PROTOCOL_CCIP
    ///                    or a future value.
    /// @param relay       Address of the IMessageRelay implementation.
    function setRelay(uint8 protocolId, address relay) external onlyRole(ROUTER_ADMIN_ROLE) {
        // Deregister old adapter if present
        address oldRelay = address(relays[protocolId]);
        if (oldRelay != address(0)) {
            authorizedRelays[oldRelay] = false;
        }

        relays[protocolId] = IMessageRelay(relay);
        authorizedRelays[relay] = true;
        emit RelayRegistered(protocolId, relay);
    }

    /// @notice Remove a relay adapter (e.g. after a bridge hack).
    function removeRelay(uint8 protocolId) external onlyRole(ROUTER_ADMIN_ROLE) {
        address relay = address(relays[protocolId]);
        if (relay != address(0)) {
            authorizedRelays[relay] = false;
            delete relays[protocolId];
        }
        // If we just removed the default, callers must switch protocols explicitly
        emit RelayRemoved(protocolId);
    }

    /// @notice Set the protocol used for plain `sendMessage` calls.
    function setDefaultProtocol(uint8 protocolId) external onlyRole(ROUTER_ADMIN_ROLE) {
        if (address(relays[protocolId]) == address(0)) revert RelayNotConfigured(protocolId);
        defaultProtocolId = protocolId;
        emit DefaultProtocolUpdated(protocolId);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Admin — routing table
    // ──────────────────────────────────────────────────────────────────────────

    function setTargetRouter(uint32 chainId, address targetRouter) external onlyRole(ROUTER_ADMIN_ROLE) {
        targetRouters[chainId] = targetRouter;
        emit TargetRouterUpdated(chainId, targetRouter);
    }

    function setAuthorizedSender(address sender, bool authorized) external onlyRole(ROUTER_ADMIN_ROLE) {
        authorizedSenders[sender] = authorized;
        emit SenderAuthorized(sender, authorized);
    }

    function setAuthorizedReceiver(address receiver, bool authorized) external onlyRole(ROUTER_ADMIN_ROLE) {
        authorizedReceivers[receiver] = authorized;
        emit ReceiverAuthorized(receiver, authorized);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Admin — circuit breaker
    // ──────────────────────────────────────────────────────────────────────────

    function pause() external onlyRole(PAUSER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Outbound — send via default protocol
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Send a message using the configured default protocol.
    /// @dev Caller must be in `authorizedSenders`.  ETH attached covers relay fee.
    function sendMessage(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable whenNotPaused returns (bytes32 messageId) {
        if (!authorizedSenders[msg.sender]) revert UnauthorizedSender(msg.sender);
        if (defaultProtocolId == 0) revert DefaultProtocolNotSet();
        return _dispatch(defaultProtocolId, destinationChainId, target, payload, extraArgs);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Outbound — send via explicit protocol
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Send a message explicitly through a specific protocol adapter.
    function sendMessageWithProtocol(
        uint8 protocolId,
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable whenNotPaused returns (bytes32 messageId) {
        if (!authorizedSenders[msg.sender]) revert UnauthorizedSender(msg.sender);
        return _dispatch(protocolId, destinationChainId, target, payload, extraArgs);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Outbound — multi-protocol broadcast
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Broadcast a message across multiple protocols simultaneously.
    ///         Maximises delivery probability at the cost of higher fees.
    ///         The entire `msg.value` is split equally among adapters; any
    ///         excess per-adapter fee is refunded by the underlying protocol.
    /// @param protocolIds  Array of protocol IDs to broadcast through.
    /// @return messageIds  Per-protocol message IDs (zero bytes32 where call reverted).
    function sendMessageMulti(
        uint8[] calldata protocolIds,
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable whenNotPaused returns (bytes32[] memory messageIds) {
        if (!authorizedSenders[msg.sender]) revert UnauthorizedSender(msg.sender);

        uint256 n = protocolIds.length;
        messageIds = new bytes32[](n);
        uint256 feePerAdapter = msg.value / n;
        bool anySucceeded;

        for (uint256 i = 0; i < n; i++) {
            uint8 pid = protocolIds[i];
            IMessageRelay relay = relays[pid];
            if (address(relay) == address(0)) {
                emit MultiSendAttempt(pid, false);
                continue;
            }
            address targetRouter = targetRouters[destinationChainId];
            if (targetRouter == address(0)) {
                emit MultiSendAttempt(pid, false);
                continue;
            }

            bytes memory routedPayload = abi.encode(target, payload);

            try relay.sendMessage{ value: feePerAdapter }(
                destinationChainId, targetRouter, routedPayload, extraArgs
            ) returns (bytes32 mid) {
                messageIds[i] = mid;
                anySucceeded = true;
                emit MultiSendAttempt(pid, true);
                emit MessageDispatched(mid, pid, destinationChainId, target, payload);
            } catch {
                emit MultiSendAttempt(pid, false);
            }
        }

        if (!anySucceeded) revert NoRelaySucceeded();
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Inbound — called by relay adapters
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageReceiver
    /// @dev Called by a relay adapter (LayerZeroRelay, WormholeRelay, CCIPRelay).
    ///      The adapter must be registered in `authorizedRelays`.
    ///      The source address must match the registered target router for that chain.
    function receiveMessage(uint32 sourceChainId, address sender, bytes calldata payload)
        external
        override
        whenNotPaused
    {
        // 1. Authenticate the calling relay adapter
        if (!authorizedRelays[msg.sender]) revert UnauthorizedRelay(msg.sender);

        // 2. Authenticate the *source* router address
        address expectedRouter = targetRouters[sourceChainId];
        if (expectedRouter == address(0) || sender != expectedRouter) {
            revert UnauthorizedSourceRouter(sourceChainId, sender);
        }

        // 3. Decode the routing envelope the source router wrapped the payload in
        (address finalTarget, bytes memory actualPayload) = abi.decode(payload, (address, bytes));

        // 4. Authenticate the final target
        if (!authorizedReceivers[finalTarget]) revert UnauthorizedReceiver(finalTarget);

        emit MessageDelivered(sourceChainId, sender, finalTarget, actualPayload);

        // 5. Forward to the target contract
        IMessageReceiver(finalTarget).receiveMessage(sourceChainId, sender, actualPayload);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Fee estimation
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Get the relay fee for a specific protocol.
    function estimateFee(
        uint8 protocolId,
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external view returns (uint256 fee) {
        IMessageRelay relay = relays[protocolId];
        if (address(relay) == address(0)) revert RelayNotConfigured(protocolId);
        address targetRouter = targetRouters[destinationChainId];
        if (targetRouter == address(0)) revert TargetRouterNotConfigured(destinationChainId);

        bytes memory routedPayload = abi.encode(target, payload);
        return relay.estimateFee(destinationChainId, targetRouter, routedPayload, extraArgs);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Internal
    // ──────────────────────────────────────────────────────────────────────────

    function _dispatch(
        uint8 protocolId,
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) internal returns (bytes32 messageId) {
        IMessageRelay relay = relays[protocolId];
        if (address(relay) == address(0)) revert RelayNotConfigured(protocolId);

        address targetRouter = targetRouters[destinationChainId];
        if (targetRouter == address(0)) revert TargetRouterNotConfigured(destinationChainId);

        // Wrap: the destination router needs to know which local contract to forward to
        bytes memory routedPayload = abi.encode(target, payload);

        messageId = relay.sendMessage{ value: msg.value }(
            destinationChainId, targetRouter, routedPayload, extraArgs
        );

        emit MessageDispatched(messageId, protocolId, destinationChainId, target, payload);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // Fallback — accept ETH for fee forwarding
    // ──────────────────────────────────────────────────────────────────────────

    receive() external payable {}
}