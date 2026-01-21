// Created: 2026-01-20
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

/**
 * @title DeployOFTArbitrum
 * @author Kerne Protocol
 * @notice Deploys KerneOFTV2 (kUSD and KERNE) to Arbitrum One.
 * 
 * DEPLOYMENT COMMAND:
 * forge script script/DeployOFTArbitrum.s.sol:DeployOFTArbitrum \
 *   --rpc-url arbitrum \
 *   --broadcast \
 *   --verify \
 *   -vvvv
 * 
 * REQUIRED ENV VARS:
 * - PRIVATE_KEY: Deployer private key
 * - ARBITRUM_RPC_URL: Arbitrum RPC endpoint
 * - ARBISCAN_API_KEY: For contract verification
 */
contract DeployOFTArbitrum is Script {
    // LayerZero V2 Endpoint (same address on all supported chains)
    address constant LZ_ENDPOINT_V2 = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Chain IDs
    uint256 constant ARBITRUM_CHAIN_ID = 42161;

    function run() external {
        require(block.chainid == ARBITRUM_CHAIN_ID, "Must run on Arbitrum (chainId 42161)");
        
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        console.log("============================================================");
        console.log("Kerne OFT V2 Deployment - Arbitrum One");
        console.log("============================================================");
        console.log("Deployer:", admin);
        console.log("LayerZero Endpoint:", LZ_ENDPOINT_V2);
        console.log("");

        vm.startBroadcast(deployerPrivateKey);

        // Deploy kUSD OFT
        KerneOFTV2 kusd = new KerneOFTV2(
            "Kerne Synthetic Dollar",
            "kUSD",
            LZ_ENDPOINT_V2,
            admin
        );
        console.log("kUSD OFT deployed at:", address(kusd));

        // Deploy KERNE OFT
        KerneOFTV2 kerne = new KerneOFTV2(
            "Kerne",
            "KERNE",
            LZ_ENDPOINT_V2,
            admin
        );
        console.log("KERNE OFT deployed at:", address(kerne));

        vm.stopBroadcast();

        console.log("");
        console.log("============================================================");
        console.log("DEPLOYMENT COMPLETE");
        console.log("============================================================");
        console.log("");
        console.log("NEXT STEPS:");
        console.log("1. Update bot/.env with Arbitrum OFT addresses:");
        console.log("   ARBITRUM_KUSD_OFT_ADDRESS=", address(kusd));
        console.log("   ARBITRUM_KERNE_OFT_ADDRESS=", address(kerne));
        console.log("");
        console.log("2. Run peer wiring on BOTH chains:");
        console.log("   - On Base: Set Arbitrum as peer");
        console.log("   - On Arbitrum: Set Base as peer");
        console.log("");
        console.log("3. Use WireOFTPeers.s.sol for bidirectional wiring");
    }
}
