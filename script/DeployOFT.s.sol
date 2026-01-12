// Created: 2026-01-06
// Updated: 2026-01-12 - Fixed LayerZero V1 endpoint addresses
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

        // LayerZero V1 Endpoints (using V1 for compatibility)
        // Base: 0xb6319cC6c8c27A8F5dAF0dD3DF91EA35C4720dd7
        // Arbitrum: 0x3c2269811836af69497E5F486A85D7316753cf62

        if (block.chainid == 8453) {
            // Base Mainnet - LayerZero V1 Endpoint
            lzEndpoint = 0xb6319cC6c8c27A8F5dAF0dD3DF91EA35C4720dd7;
        } else if (block.chainid == 42161) {
            // Arbitrum One - LayerZero V1 Endpoint
            lzEndpoint = 0x3c2269811836af69497E5F486A85D7316753cf62;
        } else {
            lzEndpoint = vm.envAddress("LZ_ENDPOINT");
        }

        vm.startBroadcast(deployerPrivateKey);

        address deployer = vm.addr(deployerPrivateKey);

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
        console.log("Deployer:", deployer);
        console.log("LayerZero Endpoint:", lzEndpoint);
        console.log("kUSD OFT deployed at:", address(kusdOFT));
        console.log("KERNE OFT deployed at:", address(kerneOFT));

        vm.stopBroadcast();
    }
}
