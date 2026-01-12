// SPDX-License-Identifier: MIT
// Created: 2026-01-12
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneYieldOracle.sol";

contract DeployYieldOracle is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);

        KerneYieldOracle oracle = new KerneYieldOracle(admin);
        
        console.log("KerneYieldOracle deployed at:", address(oracle));

        vm.stopBroadcast();
    }
}
