// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Ownable } from "@openzeppelin/contracts/access/Ownable.sol";
import { IMessageRelay } from "../interfaces/IMessageRelay.sol";

// ─────────────────────────────────────────────────────────────────────────────
// Minimal Chainlink CCIP interfaces
// Full spec: https://docs.chain.link/ccip/api-reference/i-router-client
// ─────────────────────────────────────────────────────────────────────────────

interface ICCIPRouterClient {
    struct EVMTokenAmount {
        address token;
        uint256 amount;
    }

    struct EVM2AnyMessage {
        bytes receiver; // abi.encode(address)
        bytes data;
        EVMTokenAmount[] tokenAmounts;
        address feeToken; // address(0) = pay in native gas
        bytes extraArgs; // Client.argsToBytes(EVMExtraArgsV1)
    }

    /// @notice Send a message to another chain.
    function ccipSend(uint64 destinationChainSelector, EVM2AnyMessage calldata message)
        external
        payable
        returns (bytes32 messageId);

    /// @notice Get the fee for a message.
    function getFee(uint64 destinationChainSelector, EVM2AnyMessage calldata message)
        external
        view
        returns (uint256 fee);
}

interface ICCIPReceiver {
    struct Any2EVMMessage {
        bytes32 messageId;
        uint64 sourceChainSelector;
        bytes sender; // abi.encode(address)
        bytes data;
        ICCIPRouterClient.EVMTokenAmount[] destTokenAmounts;
    }

    function ccipReceive(Any2EVMMessage calldata message) external;
}

/**
 * @title CCIPRelay
 * @author Kerne Protocol
 * @notice IMessageRelay adapter backed by Chainlink CCIP.
 *         Only the KerneMessageRouter may call `sendMessage`.
 *         The CCIP Router calls `ccipReceive` on the destination chain.
 *
 * @dev `destinationChainId` maps to the CCIP chain selector (uint64).
 *      `extraArgs` is forwarded verbatim as the CCIP `extraArgs` field;
 *      pass `Client.argsToBytes(Client.EVMExtraArgsV1({gasLimit: N}))` off-chain.
 *      All fees must be paid in native gas (feeToken = address(0)).
 */
contract CCIPRelay is IMessageRelay, ICCIPReceiver, Ownable {
    // ──────────────────────────────────────────────────────────────────────────
    // Storage
    // ──────────────────────────────────────────────────────────────────────────

    address public router;
    ICCIPRouterClient public immutable ccipRouter;

    // ──────────────────────────────────────────────────────────────────────────
    // Events
    // ──────────────────────────────────────────────────────────────────────────

    event RouterUpdated(address indexed oldRouter, address indexed newRouter);
    event MessageSentViaCCIP(bytes32 indexed messageId, uint64 destinationChainSelector);
    event MessageReceivedViaCCIP(bytes32 indexed messageId, uint64 sourceChainSelector);

    // ──────────────────────────────────────────────────────────────────────────
    // Errors
    // ──────────────────────────────────────────────────────────────────────────

    error OnlyRouter();
    error OnlyCCIPRouter();
    error RouterNotSet();
    error RouterCallFailed();

    // ──────────────────────────────────────────────────────────────────────────
    // Constructor
    // ──────────────────────────────────────────────────────────────────────────

    constructor(address _ccipRouter, address _delegate) Ownable(_delegate) {
        ccipRouter = ICCIPRouterClient(_ccipRouter);
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
    /// @dev `destinationChainId` is the CCIP chain selector (cast to uint64).
    ///      `extraArgs` is forwarded verbatim to CCIP `EVM2AnyMessage.extraArgs`
    ///      (encode via `Client.argsToBytes(Client.EVMExtraArgsV1({gasLimit: N}))`).
    function sendMessage(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable override returns (bytes32 messageId) {
        if (msg.sender != router) revert OnlyRouter();

        ICCIPRouterClient.EVM2AnyMessage memory message = ICCIPRouterClient.EVM2AnyMessage({
            receiver: abi.encode(target),
            data: payload,
            tokenAmounts: new ICCIPRouterClient.EVMTokenAmount[](0),
            feeToken: address(0), // native gas
            extraArgs: extraArgs
        });

        messageId = ccipRouter.ccipSend{ value: msg.value }(uint64(destinationChainId), message);

        emit MessageSentViaCCIP(messageId, uint64(destinationChainId));
    }

    // ──────────────────────────────────────────────────────────────────────────
    // IMessageRelay — fee quotation
    // ──────────────────────────────────────────────────────────────────────────

    /// @inheritdoc IMessageRelay
    function estimateFee(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external view override returns (uint256 fee) {
        ICCIPRouterClient.EVM2AnyMessage memory message = ICCIPRouterClient.EVM2AnyMessage({
            receiver: abi.encode(target),
            data: payload,
            tokenAmounts: new ICCIPRouterClient.EVMTokenAmount[](0),
            feeToken: address(0),
            extraArgs: extraArgs
        });
        return ccipRouter.getFee(uint64(destinationChainId), message);
    }

    // ──────────────────────────────────────────────────────────────────────────
    // ICCIPReceiver — incoming message callback
    // ──────────────────────────────────────────────────────────────────────────

    /// @notice Called by the Chainlink CCIP Router when a message arrives.
    function ccipReceive(Any2EVMMessage calldata message) external override {
        if (msg.sender != address(ccipRouter)) revert OnlyCCIPRouter();
        if (router == address(0)) revert RouterNotSet();

        address senderAddr = abi.decode(message.sender, (address));
        emit MessageReceivedViaCCIP(message.messageId, message.sourceChainSelector);

        (bool success,) = router.call(
            abi.encodeWithSignature(
                "receiveMessage(uint32,address,bytes)",
                uint32(message.sourceChainSelector),
                senderAddr,
                message.data
            )
        );
        if (!success) revert RouterCallFailed();
    }
}