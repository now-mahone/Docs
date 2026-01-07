// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Script, console } from "forge-std/Script.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title DeployScript
 * @notice Deploys the KerneVault to the specified network.
 */
contract DeployScript is Script {
    function run() external {
        // Base WETH address
        address weth = 0x4200000000000000000000000000000000000006;

        // Use the deployer's address for initial roles and exchange address
        address deployer = msg.sender;

        console.log("Deploying KerneVault with deployer:", deployer);

        vm.startBroadcast();

        // REAL CEX Deposit Address (Replace with your actual exchange deposit address)
        address exchangeDepositAddress = vm.envAddress("EXCHANGE_DEPOSIT_ADDRESS");

        KerneVault vault = new KerneVault(
            IERC20(weth),
            "Kerne Synthetic Dollar",
            "kUSD",
            deployer, // admin
            deployer, // strategist
            exchangeDepositAddress
        );

        vm.stopBroadcast();

        console.log("KerneVault deployed at:", address(vault));
    }
}
