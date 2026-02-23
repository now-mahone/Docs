// SPDX-License-Identifier: MIT
// Created: 2026-01-12
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneComplianceHook.sol";
import "../src/KerneVaultFactory.sol";

contract DeployCompliance is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        address factoryAddress = vm.envAddress("VAULT_FACTORY_ADDRESS");
        
        vm.startBroadcast(deployerPrivateKey);

        // 1. Deploy Compliance Hook
        KerneComplianceHook hook = new KerneComplianceHook(admin);
        console.log("KerneComplianceHook deployed at:", address(hook));

        // 2. Update Factory Tier Configs to use the hook
        KerneVaultFactory factory = KerneVaultFactory(factoryAddress);
        
        // Update PRO tier
        factory.setTierConfig(
            KerneVaultFactory.VaultTier.PRO,
            0.2 ether,
            750,
            true,
            address(hook),
            1000 ether
        );

        // Update INSTITUTIONAL tier
        factory.setTierConfig(
            KerneVaultFactory.VaultTier.INSTITUTIONAL,
            1 ether,
            500,
            true,
            address(hook),
            10000 ether
        );

        console.log("VaultFactory tiers updated with compliance hook.");

        vm.stopBroadcast();
    }
}
