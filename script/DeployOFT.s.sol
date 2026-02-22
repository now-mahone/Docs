// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";

contract DeployOFT is Script {
    uint256 private constant BASE_CHAIN_ID = 8453;
    uint256 private constant ARBITRUM_CHAIN_ID = 42161;
    uint256 private constant OPTIMISM_CHAIN_ID = 10;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        vm.startBroadcast(deployerPrivateKey);

        address lzEndpoint = _resolveEndpoint(block.chainid);
        string memory chainName = _resolveChainName(block.chainid);

        // Shared decimals for cross-chain compatibility (6 for USDC-like precision)
        // uint8 sharedDecimals = 6;

        console.log("Deploying OFTs on:", chainName);
        console.log("LayerZero Endpoint:", lzEndpoint);
        console.log("Delegate (Admin):", admin);

        KerneOFTV2 kusd = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", lzEndpoint, admin);
        console.log("kUSD OFT deployed at:", address(kusd));

        KerneOFTV2 kerne = new KerneOFTV2("Kerne", "KERNE", lzEndpoint, admin);
        console.log("KERNE OFT deployed at:", address(kerne));

        vm.stopBroadcast();
    }

    function _resolveEndpoint(uint256 chainId) internal pure returns (address) {
        if (chainId == BASE_CHAIN_ID || chainId == ARBITRUM_CHAIN_ID || chainId == OPTIMISM_CHAIN_ID) {
            return 0x1a44076050125825900e736c501f859c50fE728c;
        }

        revert("Unsupported chain for Kerne OFT deployment");
    }

    function _resolveChainName(uint256 chainId) internal pure returns (string memory) {
        if (chainId == BASE_CHAIN_ID) {
            return "Base";
        }
        if (chainId == ARBITRUM_CHAIN_ID) {
            return "Arbitrum";
        }
        if (chainId == OPTIMISM_CHAIN_ID) {
            return "Optimism";
        }

        return "Unknown";
    }
}
