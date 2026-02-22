// Created: 2026-01-16
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { KerneVerificationNode } from "../src/KerneVerificationNode.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title OmnichainActivation
 * @notice Master script for Institutional Arbitrum Expansion & Peer Wiring.
 */
contract OmnichainActivation is Script {
    // LayerZero V2 Endpoint (Mainnet)
    address constant LZ_ENDPOINT = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Endpoint IDs
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;

    // Arbitrum Assets
    address constant ARB_WSTETH = 0x5979D7b546E38E414F7E9822514be443A4800529;
    address constant ARB_EXCHANGE_DEPOSIT = 0x57D400cED462a01Ed51a5De038F204Df49690A99;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);

        if (block.chainid == 42161) {
            _deployArbitrumSuite(admin);
        } else if (block.chainid == 8453) {
            _configureBasePeers(admin);
        } else {
            revert("Unsupported chain for OmnichainActivation");
        }

        vm.stopBroadcast();
    }

    function _deployArbitrumSuite(address admin) internal {
        console.log("--- Deploying Arbitrum Suite ---");
        
        // 1. Deploy OFTs
        KerneOFTV2 kusd = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", LZ_ENDPOINT, admin);
        console.log("kUSD OFT (Arb) deployed at:", address(kusd));

        KerneOFTV2 kerne = new KerneOFTV2("Kerne", "KERNE", LZ_ENDPOINT, admin);
        console.log("KERNE OFT (Arb) deployed at:", address(kerne));

        // 2. Deploy VerificationNode
        KerneVerificationNode node = new KerneVerificationNode(LZ_ENDPOINT, admin);
        console.log("KerneVerificationNode (Arb) deployed at:", address(node));

        // 3. Deploy Vault
        KerneVault vault = new KerneVault(
            IERC20(ARB_WSTETH),
            "Kerne wstETH Vault",
            "k-wstETH",
            admin,
            admin,
            ARB_EXCHANGE_DEPOSIT
        );
        vault.setVerificationNode(address(node));
        console.log("KerneVault (Arb) deployed at:", address(vault));

        // 4. Set Peer (Base)
        address baseKusd = vm.envAddress("BASE_KUSD_OFT");
        address baseKerne = vm.envAddress("BASE_KERNE_OFT");
        address baseNode = vm.envAddress("BASE_VERIFICATION_NODE");
        
        kusd.setPeer(BASE_EID, bytes32(uint256(uint160(baseKusd))));
        kerne.setPeer(BASE_EID, bytes32(uint256(uint160(baseKerne))));
        node.setPeer(BASE_EID, bytes32(uint256(uint160(baseNode))));
        
        console.log("Peers set on Arbitrum for Base EID:", BASE_EID);
    }

    function _configureBasePeers(address /*admin*/) internal {
        console.log("--- Configuring Base Peers ---");
        
        address baseKusd = vm.envAddress("BASE_KUSD_OFT");
        address baseKerne = vm.envAddress("BASE_KERNE_OFT");
        address baseNode = vm.envAddress("BASE_VERIFICATION_NODE");
        
        address arbKusd = vm.envAddress("ARB_KUSD_OFT");
        address arbKerne = vm.envAddress("ARB_KERNE_OFT");
        address arbNode = vm.envAddress("ARB_VERIFICATION_NODE");

        KerneOFTV2(baseKusd).setPeer(ARBITRUM_EID, bytes32(uint256(uint160(arbKusd))));
        KerneOFTV2(baseKerne).setPeer(ARBITRUM_EID, bytes32(uint256(uint160(arbKerne))));
        KerneVerificationNode(baseNode).setPeer(ARBITRUM_EID, bytes32(uint256(uint160(arbNode))));

        console.log("Peers set on Base for Arbitrum EID:", ARBITRUM_EID);
    }
}
