// Created: 2026-01-06
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneOFT.sol";

contract DeployOFT is Script {
    function run() external {
        uint256 deployerPrivateKey;
        try vm.envUint("PRIVATE_KEY") returns (uint256 pk) {
            deployerPrivateKey = pk;
        } catch {
            deployerPrivateKey = 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80;
        }
        address lzEndpoint;

        // LayerZero V2 Endpoints
        // Base: 0x1a44076050125825900e736c501f859c50fE728c
        // Arbitrum: 0x1a44076050125825900e736c501f859c50fE728c
        // (Note: LZ V2 often uses the same address across many chains)

        if (block.chainid == 8453) {
            lzEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
        } else if (block.chainid == 42161) {
            lzEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
        } else {
            lzEndpoint = vm.envAddress("LZ_ENDPOINT");
        }

        vm.startBroadcast(deployerPrivateKey);

        address delegate = vm.addr(deployerPrivateKey);

        // Deploy kUSD OFT
        KerneOFT kusdOFT = new KerneOFT(
            "Kerne Synthetic Dollar",
            "kUSD",
            lzEndpoint
        );

        // Deploy KERNE OFT
        KerneOFT kerneOFT = new KerneOFT(
            "Kerne Governance Token",
            "KERNE",
            lzEndpoint
        );

        console.log("Chain ID:", block.chainid);
        console.log("kUSD OFT deployed at:", address(kusdOFT));
        console.log("KERNE OFT deployed at:", address(kerneOFT));

        vm.stopBroadcast();
    }
}
