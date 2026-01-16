// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneArbSettler } from "../src/KerneArbSettler.sol";

contract DeployArbSettler is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        address kusdOFT = vm.envAddress("KUSD_OFT_ADDRESS");
        address baseTreasury = vm.envAddress("BASE_TREASURY_ADDRESS");

        vm.startBroadcast(deployerPrivateKey);

        KerneArbSettler settler = new KerneArbSettler(kusdOFT, baseTreasury, admin);
        console.log("KerneArbSettler deployed at:", address(settler));

        vm.stopBroadcast();
    }
}
