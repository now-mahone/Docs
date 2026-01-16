// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneInsuranceFund.sol";

contract DeployInsuranceOnly is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        address weth = 0x4200000000000000000000000000000000000006;

        vm.startBroadcast(deployerPrivateKey);
        KerneInsuranceFund insuranceFund = new KerneInsuranceFund(weth, admin);
        console.log("KerneInsuranceFund deployed at:", address(insuranceFund));
        vm.stopBroadcast();
    }
}
