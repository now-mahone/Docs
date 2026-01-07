// SPDX-License-Identifier: MIT
// Created: 2026-01-04
pragma solidity 0.8.24;

import { Script, console } from "forge-std/Script.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { KerneVaultFactory } from "../src/KerneVaultFactory.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title DeployInstitutionalFactory
 * @notice Deploys the KerneVault implementation and factory for institutional scaling.
 */
contract DeployInstitutionalFactory is Script {
    function run() external {
        address weth = 0x4200000000000000000000000000000000000006;
        address deployer = msg.sender;
        address exchangeDepositAddress = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
        address founder = 0x683c088050556463DbdCaF7f2930bE433a368Bcf;

        console.log("Deploying Institutional Infrastructure...");

        vm.startBroadcast();

        // 1. Deploy Implementation
        KerneVault implementation = new KerneVault(
            IERC20(weth), "Kerne Institutional Implementation", "kINST-IMP", deployer, deployer, exchangeDepositAddress
        );

        // 2. Deploy Factory
        KerneVaultFactory factory = new KerneVaultFactory(address(implementation));

        // 3. Deploy Genesis Institutional Vault
        address genesisVault = factory.deployVault(
            weth,
            "Kerne Genesis Institutional",
            "kGEN-INST",
            deployer,
            founder,
            500, // 5% founder fee for white-label
            1500, // 15% performance fee
            true // whitelist enabled
        );

        // 4. Configure Genesis Vault
        KerneVault(genesisVault).setWhitelisted(deployer, true);

        vm.stopBroadcast();

        console.log("Implementation deployed at:", address(implementation));
        console.log("Factory deployed at:", address(factory));
        console.log("Genesis Institutional Vault deployed at:", genesisVault);
    }
}
