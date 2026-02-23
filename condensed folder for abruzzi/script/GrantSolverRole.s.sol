// SPDX-License-Identifier: MIT
// Created: 2026-01-20
pragma solidity 0.8.24;

import { Script, console2 } from "forge-std/Script.sol";
import { KerneZINPool } from "../src/KerneZINPool.sol";

/**
 * @title GrantSolverRole
 * @notice Grants SOLVER_ROLE to the bot wallet for zero-fee flash loans on ZIN Pool.
 * @dev This enables the ZIN solver to execute intent fulfillment without internal friction.
 * 
 * Usage:
 *   forge script script/GrantSolverRole.s.sol:GrantSolverRole \
 *     --rpc-url base \
 *     --broadcast \
 *     --private-key $PRIVATE_KEY
 */
contract GrantSolverRole is Script {
    // ZIN Pool on Base Mainnet
    address constant ZIN_POOL = 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7;
    
    // Bot wallet address (same as deployer/Trezor hot wallet)
    address constant BOT_WALLET = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    // SOLVER_ROLE hash
    bytes32 constant SOLVER_ROLE = keccak256("SOLVER_ROLE");

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        console2.log("=== Grant SOLVER_ROLE Script ===");
        console2.log("Deployer:", deployer);
        console2.log("ZIN Pool:", ZIN_POOL);
        console2.log("Bot Wallet:", BOT_WALLET);
        console2.log("SOLVER_ROLE hash:", vm.toString(SOLVER_ROLE));
        
        KerneZINPool zinPool = KerneZINPool(payable(ZIN_POOL));
        
        // Check if role is already granted
        bool alreadyHasRole = zinPool.hasRole(SOLVER_ROLE, BOT_WALLET);
        console2.log("Bot already has SOLVER_ROLE:", alreadyHasRole);
        
        if (alreadyHasRole) {
            console2.log("SOLVER_ROLE already granted. No action needed.");
            return;
        }
        
        // Check if deployer has admin role
        bytes32 adminRole = zinPool.DEFAULT_ADMIN_ROLE();
        bool isAdmin = zinPool.hasRole(adminRole, deployer);
        console2.log("Deployer is admin:", isAdmin);
        require(isAdmin, "Deployer must be admin to grant roles");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Grant SOLVER_ROLE to bot wallet
        zinPool.grantRole(SOLVER_ROLE, BOT_WALLET);
        
        vm.stopBroadcast();
        
        // Verify the role was granted
        bool hasRoleNow = zinPool.hasRole(SOLVER_ROLE, BOT_WALLET);
        console2.log("SOLVER_ROLE granted successfully:", hasRoleNow);
        require(hasRoleNow, "Failed to grant SOLVER_ROLE");
        
        console2.log("");
        console2.log("=== SUCCESS ===");
        console2.log("Bot wallet now has SOLVER_ROLE for zero-fee flash loans.");
        console2.log("Flash loan fee for bot:", zinPool.flashFee(address(0), 1e18), "(should be 0 for supported tokens)");
    }
}
