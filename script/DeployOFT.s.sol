// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

contract DeployOFT is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address delegate = vm.addr(deployerPrivateKey);
        vm.startBroadcast(deployerPrivateKey);

        // LayerZero V2 Endpoints (Verified for Mainnet)
        address baseEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
        address arbEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;

        // Deploy kUSD OFT on Base
        KerneOFTV2 kusdBase = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", baseEndpoint, delegate);
        
        // Deploy $KERNE OFT on Base
        KerneOFTV2 kerneBase = new KerneOFTV2("Kerne", "KERNE", baseEndpoint, delegate);

        // Deploy kUSD OFT on Arbitrum
        // KerneOFTV2 kusdArb = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", arbEndpoint, delegate);
        
        // Deploy $KERNE OFT on Arbitrum
        // KerneOFTV2 kerneArb = new KerneOFTV2("Kerne", "KERNE", arbEndpoint, delegate);

        vm.stopBroadcast();
    }
}
