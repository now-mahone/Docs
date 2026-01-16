// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneTreasury.sol";

contract DeployTreasuryOnly is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        address aeroRouter = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
        
        // Placeholders
        address kerneToken = admin; 
        address staking = admin;

        vm.startBroadcast(deployerPrivateKey);
        KerneTreasury treasury = new KerneTreasury(admin, kerneToken, staking, aeroRouter);
        console.log("KerneTreasury deployed at:", address(treasury));
        vm.stopBroadcast();
    }
}
