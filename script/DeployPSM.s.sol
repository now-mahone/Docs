// SPDX-License-Identifier: MIT
// Created: 2026-01-12
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KUSDPSM.sol";

contract DeployPSM is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        address kusd = 0x742d35cC6634C053200053200053200053200053; // Placeholder - need actual kUSD address

        vm.startBroadcast(deployerPrivateKey);

        KUSDPSM psm = new KUSDPSM(kusd, admin);
        
        // Add initial stables (USDC on Base)
        address usdc = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
        psm.addStable(usdc, 10); // 10 bps fee

        vm.stopBroadcast();
    }
}
