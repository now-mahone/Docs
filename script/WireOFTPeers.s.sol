// Created: 2026-01-20
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";

/**
 * @title WireOFTPeers
 * @author Kerne Protocol
 * @notice Wires OFT peers bidirectionally between Base and Arbitrum.
 * 
 * This script must be run TWICE - once on each chain:
 * 
 * STEP 1 - Run on Base (set Arbitrum as peer):
 * forge script script/WireOFTPeers.s.sol:WireOFTPeers \
 *   --rpc-url base \
 *   --broadcast \
 *   -vvvv
 * 
 * STEP 2 - Run on Arbitrum (set Base as peer):
 * forge script script/WireOFTPeers.s.sol:WireOFTPeers \
 *   --rpc-url arbitrum \
 *   --broadcast \
 *   -vvvv
 * 
 * REQUIRED ENV VARS:
 * - PRIVATE_KEY: Owner private key
 * - BASE_KUSD_OFT_ADDRESS: kUSD OFT on Base
 * - BASE_KERNE_OFT_ADDRESS: KERNE OFT on Base
 * - ARBITRUM_KUSD_OFT_ADDRESS: kUSD OFT on Arbitrum
 * - ARBITRUM_KERNE_OFT_ADDRESS: KERNE OFT on Arbitrum
 */
contract WireOFTPeers is Script {
    // LayerZero V2 Endpoint IDs
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;
    
    // Chain IDs
    uint256 constant BASE_CHAIN_ID = 8453;
    uint256 constant ARBITRUM_CHAIN_ID = 42161;

    // Known Base Mainnet OFT addresses (from TREASURY_LEDGER.md)
    address constant BASE_KUSD_OFT_DEFAULT = 0xb50bFec5FF426744b9d195a8C262da376637Cb6A;
    address constant BASE_KERNE_OFT_DEFAULT = 0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get OFT addresses from env or use defaults
        address baseKusd = _getEnvAddressOr("BASE_KUSD_OFT_ADDRESS", BASE_KUSD_OFT_DEFAULT);
        address baseKerne = _getEnvAddressOr("BASE_KERNE_OFT_ADDRESS", BASE_KERNE_OFT_DEFAULT);
        address arbKusd = vm.envAddress("ARBITRUM_KUSD_OFT_ADDRESS");
        address arbKerne = vm.envAddress("ARBITRUM_KERNE_OFT_ADDRESS");

        console.log("============================================================");
        console.log("Kerne OFT Peer Wiring");
        console.log("============================================================");
        console.log("Current Chain ID:", block.chainid);
        console.log("");
        console.log("Base OFTs:");
        console.log("  kUSD:", baseKusd);
        console.log("  KERNE:", baseKerne);
        console.log("");
        console.log("Arbitrum OFTs:");
        console.log("  kUSD:", arbKusd);
        console.log("  KERNE:", arbKerne);
        console.log("");

        vm.startBroadcast(deployerPrivateKey);

        if (block.chainid == BASE_CHAIN_ID) {
            _wireOnBase(baseKusd, baseKerne, arbKusd, arbKerne);
        } else if (block.chainid == ARBITRUM_CHAIN_ID) {
            _wireOnArbitrum(baseKusd, baseKerne, arbKusd, arbKerne);
        } else {
            revert("Unsupported chain. Must run on Base (8453) or Arbitrum (42161)");
        }

        vm.stopBroadcast();

        console.log("");
        console.log("============================================================");
        console.log("PEER WIRING COMPLETE");
        console.log("============================================================");
    }

    function _wireOnBase(
        address baseKusd,
        address baseKerne,
        address arbKusd,
        address arbKerne
    ) internal {
        console.log("Wiring Base OFTs -> Arbitrum peers...");
        console.log("");

        // Wire kUSD: Base -> Arbitrum
        bytes32 arbKusdPeer = bytes32(uint256(uint160(arbKusd)));
        (bool success1, ) = baseKusd.call(
            abi.encodeWithSignature("setPeer(uint32,bytes32)", ARBITRUM_EID, arbKusdPeer)
        );
        require(success1, "Failed to set kUSD peer on Base");
        console.log("kUSD peer set: Base -> Arbitrum (EID:", ARBITRUM_EID, ")");

        // Wire KERNE: Base -> Arbitrum
        bytes32 arbKernePeer = bytes32(uint256(uint160(arbKerne)));
        (bool success2, ) = baseKerne.call(
            abi.encodeWithSignature("setPeer(uint32,bytes32)", ARBITRUM_EID, arbKernePeer)
        );
        require(success2, "Failed to set KERNE peer on Base");
        console.log("KERNE peer set: Base -> Arbitrum (EID:", ARBITRUM_EID, ")");
    }

    function _wireOnArbitrum(
        address baseKusd,
        address baseKerne,
        address arbKusd,
        address arbKerne
    ) internal {
        console.log("Wiring Arbitrum OFTs -> Base peers...");
        console.log("");

        // Wire kUSD: Arbitrum -> Base
        bytes32 baseKusdPeer = bytes32(uint256(uint160(baseKusd)));
        (bool success1, ) = arbKusd.call(
            abi.encodeWithSignature("setPeer(uint32,bytes32)", BASE_EID, baseKusdPeer)
        );
        require(success1, "Failed to set kUSD peer on Arbitrum");
        console.log("kUSD peer set: Arbitrum -> Base (EID:", BASE_EID, ")");

        // Wire KERNE: Arbitrum -> Base
        bytes32 baseKernePeer = bytes32(uint256(uint160(baseKerne)));
        (bool success2, ) = arbKerne.call(
            abi.encodeWithSignature("setPeer(uint32,bytes32)", BASE_EID, baseKernePeer)
        );
        require(success2, "Failed to set KERNE peer on Arbitrum");
        console.log("KERNE peer set: Arbitrum -> Base (EID:", BASE_EID, ")");
    }

    function _getEnvAddressOr(string memory key, address defaultValue) internal view returns (address) {
        try vm.envAddress(key) returns (address value) {
            return value;
        } catch {
            return defaultValue;
        }
    }
}

/**
 * @title VerifyOFTPeers
 * @notice Verifies that OFT peers are correctly wired.
 * 
 * USAGE:
 * forge script script/WireOFTPeers.s.sol:VerifyOFTPeers \
 *   --rpc-url base \
 *   -vvvv
 */
contract VerifyOFTPeers is Script {
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;

    function run() external view {
        address kusdOft = vm.envAddress("OFT_ADDRESS");
        uint32 peerEid = block.chainid == 8453 ? ARBITRUM_EID : BASE_EID;

        console.log("Verifying OFT peer configuration...");
        console.log("OFT Address:", kusdOft);
        console.log("Checking peer for EID:", peerEid);

        // Call peers(eid) to get the peer address
        (bool success, bytes memory data) = kusdOft.staticcall(
            abi.encodeWithSignature("peers(uint32)", peerEid)
        );

        if (success && data.length >= 32) {
            bytes32 peer = abi.decode(data, (bytes32));
            address peerAddress = address(uint160(uint256(peer)));
            console.log("Peer Address:", peerAddress);
            
            if (peerAddress == address(0)) {
                console.log("WARNING: Peer not set!");
            } else {
                console.log("SUCCESS: Peer is configured");
            }
        } else {
            console.log("ERROR: Failed to read peer");
        }
    }
}
