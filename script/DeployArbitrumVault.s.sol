// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Script } from "forge-std/Script.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { console } from "forge-std/console.sol";

contract DeployArbitrumVault is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        // Arbitrum wstETH
        address wstETH = 0x5979D7b546E38E414F7E9822514be443A4800529;
        
        // Use a placeholder or the same address for exchange deposit if needed
        address exchangeDeposit = 0x57D400cED462a01Ed51a5De038F204Df49690A99;

        vm.startBroadcast(deployerPrivateKey);

        KerneVault vault = new KerneVault(
            IERC20(wstETH),
            "Kerne wstETH Vault",
            "k-wstETH",
            admin,
            admin,
            exchangeDeposit
        );

        console.log("Arbitrum KerneVault deployed at:", address(vault));

        vm.stopBroadcast();
    }
}
