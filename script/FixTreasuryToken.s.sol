// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";

contract FixTreasuryToken is Script {
    address constant TREASURY = 0xB656440287f8A1112558D3df915b23326e9b89ec;
    address constant KERNE_TOKEN = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        (bool success, bytes memory data) = TREASURY.call(abi.encodeWithSignature("updateKerneToken(address)", KERNE_TOKEN));
        console.log("Success:", success);
        if (!success) {
            console.logBytes(data);
        }
        
        vm.stopBroadcast();
    }
}
