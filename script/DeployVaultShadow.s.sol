// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Script.sol";
import "../src/KerneVault.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract DeployVaultShadow is Script {
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);

        // Base WETH address
        address weth = 0x4200000000000000000000000000000000000006;
        
        KerneVault vault = new KerneVault(
            IERC20(weth),
            "Kerne WETH Vault",
            "kWETH",
            deployer, // admin
            deployer, // strategist
            0x57D400cED462a01Ed51a5De038F204Df49690A99 // exchangeDepositAddress
        );
        
        console.log("KerneVault deployed at:", address(vault));

        vm.stopBroadcast();
    }
}
