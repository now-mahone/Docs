// SPDX-License-Identifier: MIT
// Created: 2026-01-20
pragma solidity 0.8.24;

import { Script, console2 } from "forge-std/Script.sol";
import { KerneZINPool } from "../src/KerneZINPool.sol";

/**
 * @title GrantSolverRoleArbitrum
 * @notice Grants SOLVER_ROLE to the bot wallet for zero-fee flash loans on Arbitrum ZIN Pool.
 * @dev This enables the ZIN solver to execute intent fulfillment without internal friction.
 * 
 * Usage:
 *   forge script script/GrantSolverRoleArbitrum.s.sol:GrantSolverRoleArbitrum \
 *     --rpc-url https://arb1.arbitrum.io/rpc \
 *     --broadcast \
 *     --private-key $PRIVATE_KEY
 */
contract GrantSolverRoleArbitrum is Script {
    // ZIN Pool on Arbitrum One (deployed 2026-01-20)
    address constant ZIN_POOL = 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD;
    
    // Bot wallet address (same as deployer/Trezor hot wallet)
    address constant BOT_WALLET = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    // SOLVER_ROLE hash
    bytes32 constant SOLVER_ROLE = keccak256("SOLVER_ROLE");

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        console2.log("=== Grant SOLVER_ROLE Script (Arbitrum) ===");
        console2.log("Network: Arbitrum One");
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
        console2.log("Bot wallet now has SOLVER_ROLE for zero-fee flash loans on Arbitrum.");
    }
}
