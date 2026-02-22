// Created: 2026-02-22
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test } from "forge-std/Test.sol";
import { KerneMessageRouter } from "src/KerneMessageRouter.sol";
import { IMessageRelay, IMessageReceiver } from "src/interfaces/IMessageRelay.sol";

// ─────────────────────────────────────────────────────────────────────────────
// Helpers
// ─────────────────────────────────────────────────────────────────────────────

/// @dev A trivial relay mock that records calls and returns a fixed messageId.
contract MockRelay is IMessageRelay {
    bytes32 public constant FIXED_MESSAGE_ID = keccak256("mock");
    uint256 public constant FIXED_FEE = 0.01 ether;

    struct SentMessage {
        uint32 destinationChainId;
        address target;
        bytes payload;
        bytes extraArgs;
        uint256 value;
    }

    SentMessage[] public sentMessages;

    function sendMessage(
        uint32 destinationChainId,
        address target,
        bytes calldata payload,
        bytes calldata extraArgs
    ) external payable override returns (bytes32) {
        sentMessages.push(
            SentMessage({
                destinationChainId: destinationChainId,
                target: target,
                payload: payload,
                extraArgs: extraArgs,
                value: msg.value
            })
        );
        return FIXED_MESSAGE_ID;
    }

    function estimateFee(uint32, address, bytes calldata, bytes calldata)
        external
        pure
        override
        returns (uint256)
    {
        return FIXED_FEE;
    }

    function sentCount() external view returns (uint256) {
        return sentMessages.length;
    }
}

/// @dev A relay that always reverts (used to test fallback behaviour).
contract RevertingRelay is IMessageRelay {
    function sendMessage(uint32, address, bytes calldata, bytes calldata)
        external
        payable
        override
        returns (bytes32)
    {
        revert("relay failure");
    }

    function estimateFee(uint32, address, bytes calldata, bytes calldata) external pure override returns (uint256) {
        return 0;
    }
}

/// @dev A contract that implements IMessageReceiver and records calls.
contract MockReceiver is IMessageReceiver {
    struct ReceivedMessage {
        uint32 sourceChainId;
        address sender;
        bytes payload;
    }

    ReceivedMessage[] public receivedMessages;

    function receiveMessage(uint32 sourceChainId, address sender, bytes calldata payload) external override {
        receivedMessages.push(ReceivedMessage({ sourceChainId: sourceChainId, sender: sender, payload: payload }));
    }

    function receivedCount() external view returns (uint256) {
        return receivedMessages.length;
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// Test contract
// ─────────────────────────────────────────────────────────────────────────────

contract KerneMessageRouterTest is Test {
    // ── Actors ────────────────────────────────────────────────────────────────
    address admin = makeAddr("admin");
    address alice = makeAddr("alice"); // authorized sender
    address bob = makeAddr("bob"); // unauthorized sender

    // ── Protocol IDs ──────────────────────────────────────────────────────────
    uint8 constant LZ_ID = 1;
    uint8 constant WH_ID = 2;
    uint8 constant CCIP_ID = 3;

    // ── Fixture ───────────────────────────────────────────────────────────────
    KerneMessageRouter router;
    MockRelay lzRelay;
    MockRelay whRelay;
    MockRelay ccipRelay;
    RevertingRelay badRelay;
    MockReceiver receiver;

    // ── Constants ─────────────────────────────────────────────────────────────
    uint32 constant DEST_CHAIN_ID = 42;
    address constant TARGET_ROUTER_ON_DEST = address(0xDEAD);
    bytes constant PAYLOAD = abi.encode("kerne_cross_chain_payload");
    bytes constant EXTRA_ARGS = "";

    function setUp() public {
        vm.startPrank(admin);

        router = new KerneMessageRouter(admin);
        lzRelay = new MockRelay();
        whRelay = new MockRelay();
        ccipRelay = new MockRelay();
        badRelay = new RevertingRelay();
        receiver = new MockReceiver();

        // Register adapters
        router.setRelay(LZ_ID, address(lzRelay));
        router.setRelay(WH_ID, address(whRelay));
        router.setRelay(CCIP_ID, address(ccipRelay));

        // Set default to LayerZero
        router.setDefaultProtocol(LZ_ID);

        // Register routing table
        router.setTargetRouter(DEST_CHAIN_ID, TARGET_ROUTER_ON_DEST);

        // Authorise alice as sender and receiver contract as receiver
        router.setAuthorizedSender(alice, true);
        router.setAuthorizedReceiver(address(receiver), true);

        vm.stopPrank();

        vm.deal(alice, 10 ether);
        vm.deal(address(router), 0); // start clean
    }

    // ─────────────────────────────────────────────────────────────────────────
    // sendMessage — default protocol (LayerZero)
    // ─────────────────────────────────────────────────────────────────────────

    function test_sendMessage_defaultProtocol() public {
        vm.prank(alice);
        bytes32 mid =
            router.sendMessage{ value: 0.01 ether }(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);

        assertEq(mid, MockRelay(address(lzRelay)).FIXED_MESSAGE_ID());
        assertEq(lzRelay.sentCount(), 1);

        // Verify wrapped payload structure (Solidity public-array getter returns tuple)
        (uint32 sentDst, address sentTarget, bytes memory sentPayload,,) = lzRelay.sentMessages(0);
        assertEq(sentDst, DEST_CHAIN_ID);
        assertEq(sentTarget, TARGET_ROUTER_ON_DEST);

        (address finalTarget, bytes memory innerPayload) = abi.decode(sentPayload, (address, bytes));
        assertEq(finalTarget, address(receiver));
        assertEq(innerPayload, PAYLOAD);
    }

    function test_sendMessage_unauthorizedSender_reverts() public {
        // No ETH needed — the authorisation check fires before any fee logic
        vm.prank(bob);
        vm.expectRevert(abi.encodeWithSelector(KerneMessageRouter.UnauthorizedSender.selector, bob));
        router.sendMessage(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    function test_sendMessage_defaultProtocolNotSet_reverts() public {
        // Deploy a fresh router without a default protocol
        KerneMessageRouter freshRouter = new KerneMessageRouter(admin);
        vm.startPrank(admin);
        freshRouter.setRelay(LZ_ID, address(lzRelay));
        freshRouter.setTargetRouter(DEST_CHAIN_ID, TARGET_ROUTER_ON_DEST);
        freshRouter.setAuthorizedSender(alice, true);
        vm.stopPrank();

        vm.deal(alice, 1 ether);
        vm.prank(alice);
        vm.expectRevert(KerneMessageRouter.DefaultProtocolNotSet.selector);
        freshRouter.sendMessage{ value: 0.01 ether }(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    function test_sendMessage_relayNotConfigured_reverts() public {
        vm.startPrank(admin);
        router.removeRelay(LZ_ID);
        vm.stopPrank();

        vm.prank(alice);
        vm.expectRevert(abi.encodeWithSelector(KerneMessageRouter.RelayNotConfigured.selector, LZ_ID));
        router.sendMessage{ value: 0.01 ether }(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    function test_sendMessage_targetRouterNotConfigured_reverts() public {
        vm.prank(alice);
        vm.expectRevert(
            abi.encodeWithSelector(KerneMessageRouter.TargetRouterNotConfigured.selector, uint32(999))
        );
        router.sendMessage{ value: 0.01 ether }(999, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // sendMessageWithProtocol — explicit adapter selection
    // ─────────────────────────────────────────────────────────────────────────

    function test_sendMessageWithProtocol_wormhole() public {
        vm.prank(alice);
        bytes32 mid = router.sendMessageWithProtocol{ value: 0.01 ether }(
            WH_ID, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS
        );

        assertEq(mid, MockRelay(address(whRelay)).FIXED_MESSAGE_ID());
        assertEq(whRelay.sentCount(), 1);
        assertEq(lzRelay.sentCount(), 0); // LZ was NOT used
    }

    function test_sendMessageWithProtocol_ccip() public {
        vm.prank(alice);
        router.sendMessageWithProtocol{ value: 0.01 ether }(
            CCIP_ID, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS
        );

        assertEq(ccipRelay.sentCount(), 1);
        assertEq(lzRelay.sentCount(), 0);
        assertEq(whRelay.sentCount(), 0);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // sendMessageMulti — broadcast
    // ─────────────────────────────────────────────────────────────────────────

    function test_sendMessageMulti_allProtocols() public {
        uint8[] memory ids = new uint8[](3);
        ids[0] = LZ_ID;
        ids[1] = WH_ID;
        ids[2] = CCIP_ID;

        vm.prank(alice);
        bytes32[] memory mids = router.sendMessageMulti{ value: 0.03 ether }(
            ids, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS
        );

        assertEq(mids.length, 3);
        assertEq(lzRelay.sentCount(), 1);
        assertEq(whRelay.sentCount(), 1);
        assertEq(ccipRelay.sentCount(), 1);
    }

    function test_sendMessageMulti_oneRevertOneSuccess() public {
        // Replace LZ with a reverting relay
        vm.prank(admin);
        router.setRelay(LZ_ID, address(badRelay));

        uint8[] memory ids = new uint8[](2);
        ids[0] = LZ_ID; // will fail
        ids[1] = WH_ID; // will succeed

        vm.prank(alice);
        bytes32[] memory mids = router.sendMessageMulti{ value: 0.02 ether }(
            ids, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS
        );

        assertEq(mids[0], bytes32(0)); // failed
        assertEq(mids[1], MockRelay(address(whRelay)).FIXED_MESSAGE_ID()); // succeeded
        assertEq(whRelay.sentCount(), 1);
    }

    function test_sendMessageMulti_allRevert_reverts() public {
        vm.startPrank(admin);
        router.setRelay(LZ_ID, address(badRelay));
        router.setRelay(WH_ID, address(badRelay));
        vm.stopPrank();

        uint8[] memory ids = new uint8[](2);
        ids[0] = LZ_ID;
        ids[1] = WH_ID;

        vm.prank(alice);
        vm.expectRevert(KerneMessageRouter.NoRelaySucceeded.selector);
        router.sendMessageMulti{ value: 0.02 ether }(ids, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // receiveMessage — inbound
    // ─────────────────────────────────────────────────────────────────────────

    function _buildInboundPayload(address target, bytes memory innerPayload)
        internal
        pure
        returns (bytes memory)
    {
        return abi.encode(target, innerPayload);
    }

    function test_receiveMessage_success() public {
        bytes memory routedPayload = _buildInboundPayload(address(receiver), PAYLOAD);

        // Simulate the LZ relay calling the router with the source router address
        vm.prank(address(lzRelay));
        router.receiveMessage(DEST_CHAIN_ID, TARGET_ROUTER_ON_DEST, routedPayload);

        assertEq(receiver.receivedCount(), 1);
        (uint32 recvChainId, address recvSender, bytes memory recvPayload) = receiver.receivedMessages(0);
        assertEq(recvChainId, DEST_CHAIN_ID);
        assertEq(recvSender, TARGET_ROUTER_ON_DEST);
        assertEq(recvPayload, PAYLOAD);
    }

    function test_receiveMessage_unauthorizedRelay_reverts() public {
        bytes memory routedPayload = _buildInboundPayload(address(receiver), PAYLOAD);

        vm.prank(address(0xBAD));
        vm.expectRevert(
            abi.encodeWithSelector(KerneMessageRouter.UnauthorizedRelay.selector, address(0xBAD))
        );
        router.receiveMessage(DEST_CHAIN_ID, TARGET_ROUTER_ON_DEST, routedPayload);
    }

    function test_receiveMessage_wrongSourceRouter_reverts() public {
        bytes memory routedPayload = _buildInboundPayload(address(receiver), PAYLOAD);

        vm.prank(address(lzRelay));
        vm.expectRevert(
            abi.encodeWithSelector(
                KerneMessageRouter.UnauthorizedSourceRouter.selector,
                DEST_CHAIN_ID,
                address(0xEEEE)
            )
        );
        router.receiveMessage(DEST_CHAIN_ID, address(0xEEEE), routedPayload);
    }

    function test_receiveMessage_unauthorizedReceiver_reverts() public {
        address unauthorizedTarget = address(0xBEEF);
        bytes memory routedPayload = _buildInboundPayload(unauthorizedTarget, PAYLOAD);

        vm.prank(address(lzRelay));
        vm.expectRevert(
            abi.encodeWithSelector(KerneMessageRouter.UnauthorizedReceiver.selector, unauthorizedTarget)
        );
        router.receiveMessage(DEST_CHAIN_ID, TARGET_ROUTER_ON_DEST, routedPayload);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Fee estimation
    // ─────────────────────────────────────────────────────────────────────────

    function test_estimateFee_returnsRelayFee() public view {
        uint256 fee =
            router.estimateFee(LZ_ID, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
        assertEq(fee, MockRelay(address(lzRelay)).FIXED_FEE());
    }

    function test_estimateFee_relayNotConfigured_reverts() public {
        vm.expectRevert(abi.encodeWithSelector(KerneMessageRouter.RelayNotConfigured.selector, uint8(99)));
        router.estimateFee(99, DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Admin — relay registration / removal
    // ─────────────────────────────────────────────────────────────────────────

    function test_setRelay_updatesAuthMapping() public {
        address newRelay = address(new MockRelay());

        vm.prank(admin);
        router.setRelay(LZ_ID, newRelay);

        assertTrue(router.authorizedRelays(newRelay));
        assertFalse(router.authorizedRelays(address(lzRelay))); // old one deauthorized
    }

    function test_removeRelay_deauthorizes() public {
        vm.prank(admin);
        router.removeRelay(LZ_ID);

        assertFalse(router.authorizedRelays(address(lzRelay)));
        assertEq(address(router.relays(LZ_ID)), address(0));
    }

    function test_setDefaultProtocol_invalidId_reverts() public {
        vm.prank(admin);
        vm.expectRevert(abi.encodeWithSelector(KerneMessageRouter.RelayNotConfigured.selector, uint8(99)));
        router.setDefaultProtocol(99);
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Pause
    // ─────────────────────────────────────────────────────────────────────────

    function test_pause_blocksAllSends() public {
        vm.prank(admin);
        router.pause();

        vm.prank(alice);
        vm.expectRevert(); // EnforcedPause
        router.sendMessage{ value: 0.01 ether }(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
    }

    function test_unpause_restoresSends() public {
        vm.startPrank(admin);
        router.pause();
        router.unpause();
        vm.stopPrank();

        vm.prank(alice);
        bytes32 mid =
            router.sendMessage{ value: 0.01 ether }(DEST_CHAIN_ID, address(receiver), PAYLOAD, EXTRA_ARGS);
        assertEq(mid, MockRelay(address(lzRelay)).FIXED_MESSAGE_ID());
    }

    // ─────────────────────────────────────────────────────────────────────────
    // Access control guards
    // ─────────────────────────────────────────────────────────────────────────

    function test_setRelay_nonAdmin_reverts() public {
        // Deploy the contract BEFORE setting the prank so the constructor call
        // does not consume the vm.prank before setRelay() is reached.
        address newRelayAddr = address(new MockRelay());
        vm.prank(bob);
        vm.expectRevert();
        router.setRelay(LZ_ID, newRelayAddr);
    }

    function test_setTargetRouter_nonAdmin_reverts() public {
        vm.prank(bob);
        vm.expectRevert();
        router.setTargetRouter(DEST_CHAIN_ID, address(0x1));
    }
}