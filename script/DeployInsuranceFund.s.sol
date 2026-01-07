// Created: 2026-01-04
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneInsuranceFund.sol";

contract DeployInsuranceFund is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address asset = vm.envAddress("WETH_ADDRESS"); // Base WETH

        vm.startBroadcast(deployerPrivateKey);

        KerneInsuranceFund insuranceFund = new KerneInsuranceFund(asset);

        console.log("KerneInsuranceFund deployed at:", address(insuranceFund));

        vm.stopBroadcast();
    }
}
