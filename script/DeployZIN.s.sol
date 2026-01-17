// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { KerneIntentExecutorV2 } from "../src/KerneIntentExecutorV2.sol";
import { KerneZINPool } from "../src/KerneZINPool.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title DeployZIN
 * @notice Deploys the Zero-Fee Intent Network (ZIN) system
 * @dev This script deploys:
 *      1. KerneIntentExecutorV2 (Core intent fulfillment engine)
 *      2. KerneZINPool (Liquidity aggregation pool)
 *      3. Configures vaults for ZIN operations
 */
contract DeployZIN is Script {
    // Base Mainnet addresses
    address constant USDC_ADDRESS = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    address constant WETH_ADDRESS = 0x4200000000000000000000000000000000000006;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        vm.startBroadcast(deployerPrivateKey);
        
        address deployer = vm.addr(deployerPrivateKey);
        console.log("Deployer:", deployer);
        console.log("");
        
        // ============================================================
        // STEP 1: Deploy KerneIntentExecutorV2
        // ============================================================
        console.log("=== Deploying KerneIntentExecutorV2 ===");
        
        // We'll use deployer as profit vault initially (will update later)
        KerneIntentExecutorV2 zinExecutor = new KerneIntentExecutorV2(
            deployer,  // admin
            deployer,  // solver (will update later)
            deployer   // profitVault (will update later)
        );
        
        console.log("KerneIntentExecutorV2 deployed:", address(zinExecutor));
        console.log("");
        
        // ============================================================
        // STEP 2: Deploy KerneZINPool
        // ============================================================
        console.log("=== Deploying KerneZINPool ===");
        
        KerneZINPool zinPool = new KerneZINPool(
            deployer,  // admin
            deployer   // profitRecipient (will update later)
        );
        
        console.log("KerneZINPool deployed:", address(zinPool));
        console.log("");
        
        // ============================================================
        // STEP 3: Configure ZIN Pool
        // ============================================================
        console.log("=== Configuring KerneZINPool ===");
        
        // Support USDC and WETH
        zinPool.supportToken(USDC_ADDRESS);
        console.log("Supported USDC");
        
        zinPool.supportToken(WETH_ADDRESS);
        console.log("Supported WETH");
        
        console.log("");
        
        // ============================================================
        // STEP 4: Update ZIN Executor Configuration
        // ============================================================
        console.log("=== Updating ZIN Executor Configuration ===");
        
        // Update profit vault to actual vault (will be deployed separately)
        // zinExecutor.setProfitVault(<VAULT_ADDRESS>);
        console.log("Profit vault: (set to deployer, update to actual vault)");
        
        console.log("");
        
        // ============================================================
        // STEP 5: Vault Configuration (to be done manually)
        // ============================================================
        console.log("=== Manual Vault Configuration Required ===");
        console.log("After deploying vaults, run:");
        console.log("  vault.setZINExecutor(address(zinExecutor));");
        console.log("");
        
        // ============================================================
        // STEP 6: Summary
        // ============================================================
        console.log("=== Deployment Summary ===");
        console.log("ZIN Executor:", address(zinExecutor));
        console.log("ZIN Pool:", address(zinPool));
        console.log("");
        
        console.log("=== Next Steps ===");
        console.log("1. Deploy KerneVault(s) for USDC/WETH");
        console.log("2. Set ZIN executor on each vault:");
        console.log("   vault.setZINExecutor(address(zinExecutor))");
        console.log("3. Add vaults as liquidity sources to ZIN pool:");
        console.log("   zinPool.addLiquiditySource(token, vault, priority)");
        console.log("4. Update ZIN executor profit vault:");
        console.log("   zinExecutor.setProfitVault(<PROFIT_VAULT_ADDRESS>)");
        console.log("5. Grant SOLVER_ROLE to solver bot:");
        console.log("   zinExecutor.grantRole(zinExecutor.SOLVER_ROLE(), <SOLVER_ADDRESS>)");
        console.log("");
        
        // ============================================================
        // STEP 7: Deployment Complete
        // ============================================================
        console.log("=== ZIN Deployment Complete ===");
        console.log("Save these addresses for configuration:");
        console.log("ZIN Executor:", vm.toString(address(zinExecutor)));
        console.log("ZIN Pool:", vm.toString(address(zinPool)));
        
        vm.stopBroadcast();
    }
    
    /**
     * @notice Verify deployment
     */
    function verifyDeployment(
        address payable zinExecutorAddress,
        address payable zinPoolAddress
    ) external view {
        console.log("=== Verification ===");
        console.log("ZIN Executor:", zinExecutorAddress);
        console.log("ZIN Pool:", zinPoolAddress);
        
        KerneIntentExecutorV2 zinExecutor = KerneIntentExecutorV2(zinExecutorAddress);
        KerneZINPool zinPool = KerneZINPool(zinPoolAddress);
        
        (uint256 totalSpread, uint256 totalIntents, address profitVault) = zinExecutor.getZINMetrics();
        console.log("Total Spread:", totalSpread);
        console.log("Total Intents:", totalIntents);
        console.log("Profit Vault:", profitVault);
    }
}
