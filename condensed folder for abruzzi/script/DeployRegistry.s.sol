// SPDX-License-Identifier: MIT
// Created: 2026-01-12
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneVaultRegistry.sol";

contract DeployRegistry is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        KerneVaultRegistry registry = new KerneVaultRegistry();
        
        console.log("KerneVaultRegistry deployed at:", address(registry));

        vm.stopBroadcast();
    }
}
