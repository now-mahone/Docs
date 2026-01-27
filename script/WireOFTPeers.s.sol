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
    uint32 constant OPTIMISM_EID = 30111;
    
    // Chain IDs
    uint256 constant BASE_CHAIN_ID = 8453;
    uint256 constant ARBITRUM_CHAIN_ID = 42161;
    uint256 constant OPTIMISM_CHAIN_ID = 10;

    // Known Base Mainnet OFT addresses (from project_state.md)
    address constant BASE_KUSD_OFT_DEFAULT = 0x257579db2702BAeeBFAC5c19d354f2FF39831299;
    address constant BASE_KERNE_OFT_DEFAULT = 0x4E1ce62F571893eCfD7062937781A766ff64F14e;

    // Known Arbitrum Mainnet OFT addresses
    address constant ARBITRUM_KUSD_OFT_DEFAULT = 0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222;
    address constant ARBITRUM_KERNE_OFT_DEFAULT = 0x087365f83caF2E2504c399330F5D15f62Ae7dAC3;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        // Get OFT addresses from env or use defaults
        address baseKusd = _getEnvAddressOr("BASE_KUSD_OFT_ADDRESS", BASE_KUSD_OFT_DEFAULT);
        address baseKerne = _getEnvAddressOr("BASE_KERNE_OFT_ADDRESS", BASE_KERNE_OFT_DEFAULT);
        address arbKusd = _getEnvAddressOr("ARBITRUM_KUSD_OFT_ADDRESS", ARBITRUM_KUSD_OFT_DEFAULT);
        address arbKerne = _getEnvAddressOr("ARBITRUM_KERNE_OFT_ADDRESS", ARBITRUM_KERNE_OFT_DEFAULT);
        address optKusd = vm.envAddress("OPTIMISM_KUSD_OFT_ADDRESS");
        address optKerne = vm.envAddress("OPTIMISM_KERNE_OFT_ADDRESS");

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
        console.log("Optimism OFTs:");
        console.log("  kUSD:", optKusd);
        console.log("  KERNE:", optKerne);
        console.log("");

        vm.startBroadcast(deployerPrivateKey);

        if (block.chainid == BASE_CHAIN_ID) {
            _wireOnBase(baseKusd, baseKerne, arbKusd, arbKerne, optKusd, optKerne);
        } else if (block.chainid == ARBITRUM_CHAIN_ID) {
            _wireOnArbitrum(baseKusd, baseKerne, arbKusd, arbKerne, optKusd, optKerne);
        } else if (block.chainid == OPTIMISM_CHAIN_ID) {
            _wireOnOptimism(baseKusd, baseKerne, arbKusd, arbKerne, optKusd, optKerne);
        } else {
            revert("Unsupported chain. Must run on Base, Arbitrum, or Optimism");
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
        address arbKerne,
        address optKusd,
        address optKerne
    ) internal {
        console.log("Wiring Base OFTs -> peers...");

        // Wire to Arbitrum
        _setPeer(baseKusd, ARBITRUM_EID, arbKusd);
        _setPeer(baseKerne, ARBITRUM_EID, arbKerne);

        // Wire to Optimism
        if (optKusd != address(0)) _setPeer(baseKusd, OPTIMISM_EID, optKusd);
        if (optKerne != address(0)) _setPeer(baseKerne, OPTIMISM_EID, optKerne);
    }

    function _wireOnArbitrum(
        address baseKusd,
        address baseKerne,
        address arbKusd,
        address arbKerne,
        address optKusd,
        address optKerne
    ) internal {
        console.log("Wiring Arbitrum OFTs -> peers...");

        // Wire to Base
        _setPeer(arbKusd, BASE_EID, baseKusd);
        _setPeer(arbKerne, BASE_EID, baseKerne);

        // Wire to Optimism
        if (optKusd != address(0)) _setPeer(arbKusd, OPTIMISM_EID, optKusd);
        if (optKerne != address(0)) _setPeer(arbKerne, OPTIMISM_EID, optKerne);
    }

    function _wireOnOptimism(
        address baseKusd,
        address baseKerne,
        address arbKusd,
        address arbKerne,
        address optKusd,
        address optKerne
    ) internal {
        console.log("Wiring Optimism OFTs -> peers...");

        // Wire to Base
        _setPeer(optKusd, BASE_EID, baseKusd);
        _setPeer(optKerne, BASE_EID, baseKerne);

        // Wire to Arbitrum
        _setPeer(optKusd, ARBITRUM_EID, arbKusd);
        _setPeer(optKerne, ARBITRUM_EID, arbKerne);
    }

    function _setPeer(address oft, uint32 remoteEid, address peer) internal {
        if (peer == address(0)) return;
        bytes32 peerBytes32 = bytes32(uint256(uint160(peer)));
        (bool success, ) = oft.call(
            abi.encodeWithSignature("setPeer(uint32,bytes32)", remoteEid, peerBytes32)
        );
        require(success, string(abi.encodePacked("Failed to set peer for EID ", _uintToString(remoteEid))));
        console.log("Peer set for EID:", remoteEid, "->", peer);
    }

    function _uintToString(uint32 value) internal pure returns (string memory) {
        if (value == 0) return "0";
        uint32 temp = value;
        uint32 digits;
        while (temp != 0) {
            digits++;
            temp /= 10;
        }
        bytes memory buffer = new bytes(digits);
        while (value != 0) {
            digits -= 1;
            buffer[digits] = bytes1(uint8(48 + uint32(value % 10)));
            value /= 10;
        }
        return string(buffer);
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
