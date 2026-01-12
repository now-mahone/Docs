// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

contract DeployOFT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        // LayerZero V2 Endpoints (Verified for Mainnet)
        address baseEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
        // address arbEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;

        // Shared decimals for cross-chain compatibility (6 for USDC-like precision)
        uint8 sharedDecimals = 6;

        // Deploy kUSD OFT on Base
        KerneOFTV2 kusdBase = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", sharedDecimals, baseEndpoint);
        console.log("kUSD OFT deployed at:", address(kusdBase));
        
        // Deploy $KERNE OFT on Base (18 decimals for governance token)
        KerneOFTV2 kerneBase = new KerneOFTV2("Kerne", "KERNE", 8, baseEndpoint);
        console.log("KERNE OFT deployed at:", address(kerneBase));

        // Deploy kUSD OFT on Arbitrum (uncomment when deploying to Arbitrum)
        // KerneOFTV2 kusdArb = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", sharedDecimals, arbEndpoint);
        
        // Deploy $KERNE OFT on Arbitrum (uncomment when deploying to Arbitrum)
        // KerneOFTV2 kerneArb = new KerneOFTV2("Kerne", "KERNE", 8, arbEndpoint);

        vm.stopBroadcast();
    }
}
