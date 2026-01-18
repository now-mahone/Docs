// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneIntentExecutorV2 } from "../src/KerneIntentExecutorV2.sol";
import { KerneZINPool } from "../src/KerneZINPool.sol";

/**
 * @title DeployZINArbitrum
 * @notice Deploys the Zero-Fee Intent Network (ZIN) system to Arbitrum
 * @dev Arbitrum has 3-5x higher intent volume than Base via UniswapX Dutch_V2 orders
 *      
 *      Deploy command:
 *      forge script script/DeployZINArbitrum.s.sol:DeployZINArbitrum \
 *          --rpc-url $ARBITRUM_RPC_URL \
 *          --broadcast \
 *          --verify \
 *          --etherscan-api-key $ARBISCAN_API_KEY
 */
contract DeployZINArbitrum is Script {
    // Arbitrum Mainnet addresses
    address constant USDC_ADDRESS = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831; // Native USDC
    address constant USDC_E_ADDRESS = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8; // Bridged USDC.e
    address constant WETH_ADDRESS = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address constant ARB_ADDRESS = 0x912CE59144191C1204E64559FE8253a0e49E6548;
    address constant WSTETH_ADDRESS = 0x5979D7b546E38E414F7E9822514be443A4800529;
    
    // UniswapX Reactor on Arbitrum (Dutch_V2)
    address constant UNISWAPX_REACTOR = 0x1bd1aAdc9E230626C44a139d7E70d842749351eb;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        address deployer = vm.addr(deployerPrivateKey);
        console.log("=== ZIN Arbitrum Deployment ===");
        console.log("Deployer:", deployer);
        console.log("Chain ID: 42161 (Arbitrum One)");
        console.log("");
        
        // ============================================================
        // STEP 1: Deploy KerneIntentExecutorV2
        // ============================================================
        console.log("=== Deploying KerneIntentExecutorV2 ===");
        
        KerneIntentExecutorV2 zinExecutor = new KerneIntentExecutorV2(
            deployer,  // admin
            deployer,  // solver (will grant to bot later)
            deployer   // profitVault (will update to actual vault)
        );
        
        console.log("KerneIntentExecutorV2 deployed:", address(zinExecutor));
        console.log("");
        
        // ============================================================
        // STEP 2: Deploy KerneZINPool
        // ============================================================
        console.log("=== Deploying KerneZINPool ===");
        
        KerneZINPool zinPool = new KerneZINPool(
            deployer,  // admin
            deployer   // profitRecipient
        );
        
        console.log("KerneZINPool deployed:", address(zinPool));
        console.log("");
        
        // ============================================================
        // STEP 3: Configure ZIN Pool with Arbitrum tokens
        // ============================================================
        console.log("=== Configuring KerneZINPool ===");
        
        // Support native USDC
        zinPool.supportToken(USDC_ADDRESS);
        console.log("Supported USDC (native):", USDC_ADDRESS);
        
        // Support bridged USDC.e
        zinPool.supportToken(USDC_E_ADDRESS);
        console.log("Supported USDC.e (bridged):", USDC_E_ADDRESS);
        
        // Support WETH
        zinPool.supportToken(WETH_ADDRESS);
        console.log("Supported WETH:", WETH_ADDRESS);
        
        // Support wstETH
        zinPool.supportToken(WSTETH_ADDRESS);
        console.log("Supported wstETH:", WSTETH_ADDRESS);
        
        console.log("");
        
        // ============================================================
        // STEP 4: Summary & Next Steps
        // ============================================================
        console.log("=== Deployment Summary ===");
        console.log("ZIN Executor:", address(zinExecutor));
        console.log("ZIN Pool:", address(zinPool));
        console.log("");
        
        console.log("=== Bot Configuration ===");
        console.log("Add to bot/.env:");
        console.log("  ARBITRUM_ZIN_EXECUTOR_ADDRESS=", vm.toString(address(zinExecutor)));
        console.log("  ARBITRUM_ZIN_POOL_ADDRESS=", vm.toString(address(zinPool)));
        console.log("  ARBITRUM_RPC_URL=https://arb1.arbitrum.io/rpc");
        console.log("");
        
        console.log("=== Next Steps ===");
        console.log("1. Grant SOLVER_ROLE to bot address:");
        console.log("   zinExecutor.grantRole(SOLVER_ROLE, <BOT_ADDRESS>)");
        console.log("2. Seed ZIN Pool with initial liquidity");
        console.log("3. Update zin_solver.py ACTIVE_CHAIN=arbitrum");
        console.log("4. Monitor UniswapX Dutch_V2 orders");
        
        vm.stopBroadcast();
    }
}
