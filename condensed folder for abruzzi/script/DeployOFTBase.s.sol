// Created: 2026-01-20
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

/**
 * @title DeployOFTBase  
 * @author Kerne Protocol
 * @notice Deploys KerneOFTV2 (kUSD and KERNE) to Base Mainnet.
 *         This replaces the V1 OFTs with V2 for omnichain compatibility.
 * 
 * DEPLOYMENT COMMAND:
 * forge script script/DeployOFTBase.s.sol:DeployOFTBase \
 *   --rpc-url https://mainnet.base.org \
 *   --broadcast \
 *   --verify \
 *   -vvvv
 * 
 * REQUIRED ENV VARS:
 * - PRIVATE_KEY: Deployer private key
 */
contract DeployOFTBase is Script {
    // LayerZero V2 Endpoint (same address on all supported chains)
    address constant LZ_ENDPOINT_V2 = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Chain IDs
    uint256 constant BASE_CHAIN_ID = 8453;

    function run() external {
        require(block.chainid == BASE_CHAIN_ID, "Must run on Base (chainId 8453)");
        
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        console.log("============================================================");
        console.log("Kerne OFT V2 Deployment - Base Mainnet");
        console.log("============================================================");
        console.log("Deployer:", admin);
        console.log("LayerZero Endpoint:", LZ_ENDPOINT_V2);
        console.log("");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy kUSD OFT V2
        KerneOFTV2 kusd = new KerneOFTV2(
            "Kerne Synthetic Dollar",
            "kUSD",
            LZ_ENDPOINT_V2,
            admin
        );
        console.log("kUSD OFT V2 deployed at:", address(kusd));

        // Deploy KERNE OFT V2
        KerneOFTV2 kerne = new KerneOFTV2(
            "Kerne",
            "KERNE",
            LZ_ENDPOINT_V2,
            admin
        );
        console.log("KERNE OFT V2 deployed at:", address(kerne));

        vm.stopBroadcast();

        console.log("");
        console.log("============================================================");
        console.log("DEPLOYMENT COMPLETE");
        console.log("============================================================");
        console.log("");
        console.log("NOTE: These are NEW V2 OFTs replacing the V1 contracts:");
        console.log("OLD V1 kUSD:  0xb50bFec5FF426744b9d195a8C262da376637Cb6A");
        console.log("OLD V1 KERNE: 0xE828810B6B60A3DE21AB9d0BDba962bF9FbDc255");
        console.log("");
        console.log("NEXT STEPS:");
        console.log("1. Update bot/.env with NEW Base OFT V2 addresses");
        console.log("2. Run peer wiring with Arbitrum OFT V2s:");
        console.log("   Arbitrum kUSD:  0xc1CF31008eF7C5aC0ebFF9712E96a39F299e8222");
        console.log("   Arbitrum KERNE: 0x087365f83caF2E2504c399330F5D15f62Ae7dAC3");
    }
}
