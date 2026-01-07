// SPDX-License-Identifier: MIT
// Created: 2025-12-28
pragma solidity 0.8.24;

import { Script } from "forge-std/Script.sol";
import { KerneVault } from "../src/KerneVault.sol";

/**
 * @title TransferOwnership
 * @notice Script to transfer DEFAULT_ADMIN_ROLE to a new address (e.g., Multisig).
 */
contract TransferOwnership is Script {
    function run(address vaultAddress, address newAdmin) external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);

        KerneVault vault = KerneVault(vaultAddress);

        // Grant the new admin role
        vault.grantRole(vault.DEFAULT_ADMIN_ROLE(), newAdmin);

        // Grant PAUSER_ROLE to new admin as well
        vault.grantRole(vault.PAUSER_ROLE(), newAdmin);

        // Renounce the role from the current deployer
        vault.renounceRole(vault.DEFAULT_ADMIN_ROLE(), vm.addr(deployerPrivateKey));
        vault.renounceRole(vault.PAUSER_ROLE(), vm.addr(deployerPrivateKey));

        vm.stopBroadcast();
    }
}
