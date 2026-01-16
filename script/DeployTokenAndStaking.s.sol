// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneToken.sol";
import "../src/KerneStaking.sol";

contract DeployTokenAndStaking is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        // Base Mainnet WETH
        address weth = 0x4200000000000000000000000000000000000006;

        console.log("Deploying from:", admin);

        vm.startBroadcast(deployerPrivateKey);

        KerneToken token = new KerneToken(admin);
        console.log("KerneToken deployed at:", address(token));

        KerneStaking staking = new KerneStaking(address(token), weth, admin);
        console.log("KerneStaking deployed at:", address(staking));

        vm.stopBroadcast();
    }
}
