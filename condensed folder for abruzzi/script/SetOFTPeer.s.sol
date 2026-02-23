// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

contract SetOFTPeer is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address oftAddress = vm.envAddress("OFT_ADDRESS");
        uint32 peerEid = uint32(vm.envUint("PEER_EID"));
        address peerAddress = vm.envAddress("PEER_ADDRESS");

        vm.startBroadcast(deployerPrivateKey);

        KerneOFTV2 oft = KerneOFTV2(oftAddress);
        bytes32 peer = bytes32(uint256(uint160(peerAddress)));
        oft.setPeer(peerEid, peer);

        console.log("Set peer for OFT:", oftAddress);
        console.log("Peer EID:", peerEid);
        console.log("Peer Address:", peerAddress);

        vm.stopBroadcast();
    }
}
