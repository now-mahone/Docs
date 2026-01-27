// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneTreasury.sol";

contract TestTreasury is Script {
    address constant TREASURY = 0xB656440287f8A1112558D3df915b23326e9b89ec;
    address constant KERNE_TOKEN = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        KerneTreasury treasury = KerneTreasury(payable(TREASURY));
        console.log("Current KERNE Token:", treasury.kerneToken());
        
        console.log("Setting KERNE Token to:", KERNE_TOKEN);
        treasury.updateKerneToken(KERNE_TOKEN);
        
        console.log("New KERNE Token:", treasury.kerneToken());
        
        vm.stopBroadcast();
    }
}
