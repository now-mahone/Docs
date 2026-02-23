// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneInsuranceFund.sol";
import "../src/KerneVault.sol";

contract DeployAndSetupInsurance is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address admin = vm.addr(deployerPrivateKey);
        
        // Base Mainnet WETH
        address weth = 0x4200000000000000000000000000000000000006;
        
        // KerneVault address
        address vaultAddress = 0xDA9765F84208F8E94225889B2C9331DCe940fB20;

        vm.startBroadcast(deployerPrivateKey);
        
        // 1. Deploy KerneInsuranceFund
        KerneInsuranceFund insuranceFund = new KerneInsuranceFund(weth, admin);
        console.log("KerneInsuranceFund deployed at:", address(insuranceFund));
        
        // 2. Authorize the vault in the insurance fund
        insuranceFund.setAuthorization(vaultAddress, true);
        console.log("Vault authorized in Insurance Fund");
        
        // 3. Set the insurance fund in the vault
        KerneVault vault = KerneVault(vaultAddress);
        vault.setInsuranceFund(address(insuranceFund));
        console.log("Insurance Fund set in Vault");
        
        // 4. Set the insurance fund contribution (e.g., 1000 bps = 10%)
        vault.setInsuranceFundBps(1000);
        console.log("Insurance Fund contribution set to 10%");
        
        vm.stopBroadcast();
    }
}