// Created: 2026-01-06
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneOFT.sol";

contract DeployOFT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address lzEndpoint = vm.envAddress("LZ_ENDPOINT"); // Arbitrum LZ Endpoint

        vm.startBroadcast(deployerPrivateKey);

        // Deploy kUSD OFT
        KerneOFT kusdOFT = new KerneOFT(
            "Kerne Synthetic Dollar",
            "kUSD",
            6, // Shared decimals
            lzEndpoint
        );

        // Deploy KERNE OFT
        KerneOFT kerneOFT = new KerneOFT(
            "Kerne Governance Token",
            "KERNE",
            6, // Shared decimals
            lzEndpoint
        );

        console.log("kUSD OFT deployed at:", address(kusdOFT));
        console.log("KERNE OFT deployed at:", address(kerneOFT));

        vm.stopBroadcast();
    }
}
