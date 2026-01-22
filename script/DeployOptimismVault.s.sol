// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "../src/KerneVault.sol";
import "../src/KerneOFTV2.sol";
import "../src/KerneZINPool.sol";
import "../src/KerneIntentExecutorV2.sol";

/**
 * @title DeployOptimismVault
 * @notice Deploys KerneVault on Optimism Mainnet
 * @dev Run with: forge script script/DeployOptimismVault.s.sol:DeployOptimismVault --rpc-url $OPTIMISM_RPC_URL --broadcast --verify
 */
contract DeployOptimismVault is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // OPTIMISM MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    // Lido wstETH on Optimism
    address constant WSTETH = 0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb;
    
    // LayerZero V2 Endpoint on Optimism
    address constant LZ_ENDPOINT = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Base chain LayerZero EID
    uint32 constant BASE_EID = 30184;
    
    // Arbitrum chain LayerZero EID
    uint32 constant ARBITRUM_EID = 30110;
    
    // Deployer/Strategist
    address constant STRATEGIST = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    // Treasury (same as deployer for now)
    address constant TREASURY = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=================================================================");
        console.log("       KERNE OPTIMISM DEPLOYMENT - VAULT                         ");
        console.log("=================================================================");
        console.log("");
        console.log("Deployer:", deployer);
        console.log("Asset (wstETH):", WSTETH);
        console.log("");
        
        // Step 1: Deploy KerneVault
        // Constructor: (IERC20 asset, name, symbol, admin, strategist, exchangeDepositAddress)
        console.log("Step 1: Deploying KerneVault...");
        KerneVault vault = new KerneVault(
            IERC20(WSTETH),
            "Kerne wstETH Vault",
            "kvWSTETH",
            deployer,           // admin
            deployer,           // strategist (same as admin initially)
            TREASURY            // exchangeDepositAddress (sweep destination)
        );
        console.log("  -> KerneVault:", address(vault));
        
        // Step 2: Configure vault settings
        console.log("");
        console.log("Step 2: Configuring vault...");
        vault.setPerformanceFee(500); // 5% performance fee
        console.log("  -> Performance Fee: 5%");
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=================================================================");
        console.log("                    DEPLOYMENT SUMMARY                          ");
        console.log("=================================================================");
        console.log("");
        console.log("KerneVault:", address(vault));
        console.log("Asset:", WSTETH);
        console.log("Network: Optimism Mainnet");
        console.log("");
        console.log("=================================================================");
        console.log("                    NEXT STEPS                                  ");
        console.log("=================================================================");
        console.log("");
        console.log("1. Deploy OFT V2 bridges for kUSD and KERNE on Optimism");
        console.log("2. Wire OFT peers between Base <-> Optimism");
        console.log("3. Deploy ZIN infrastructure on Optimism");
        console.log("4. Update TREASURY_LEDGER.md with new addresses");
        console.log("5. Apply for Optimism Foundation grant");
        console.log("");
    }
}

/**
 * @title DeployOptimismOFT
 * @notice Deploys kUSD and KERNE OFT V2 bridges on Optimism
 * @dev Run with: forge script script/DeployOptimismVault.s.sol:DeployOptimismOFT --rpc-url $OPTIMISM_RPC_URL --broadcast --verify
 */
contract DeployOptimismOFT is Script {
    // LayerZero V2 Endpoint on Optimism
    address constant LZ_ENDPOINT = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Deployer
    address constant DEPLOYER = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=================================================================");
        console.log("       KERNE OPTIMISM DEPLOYMENT - OFT V2                        ");
        console.log("=================================================================");
        console.log("");
        console.log("Deployer:", deployer);
        console.log("LayerZero Endpoint:", LZ_ENDPOINT);
        console.log("");
        
        // Deploy kUSD OFT V2
        console.log("Deploying kUSD OFT V2...");
        KerneOFTV2 kusdOft = new KerneOFTV2(
            "Kerne USD",
            "kUSD",
            LZ_ENDPOINT,
            DEPLOYER
        );
        console.log("  -> kUSD OFT V2:", address(kusdOft));
        
        // Deploy KERNE OFT V2
        console.log("");
        console.log("Deploying KERNE OFT V2...");
        KerneOFTV2 kerneOft = new KerneOFTV2(
            "Kerne",
            "KERNE",
            LZ_ENDPOINT,
            DEPLOYER
        );
        console.log("  -> KERNE OFT V2:", address(kerneOft));
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=================================================================");
        console.log("                    OFT DEPLOYMENT SUMMARY                      ");
        console.log("=================================================================");
        console.log("");
        console.log("kUSD OFT V2 (Optimism):", address(kusdOft));
        console.log("KERNE OFT V2 (Optimism):", address(kerneOft));
        console.log("");
        console.log("=================================================================");
        console.log("                    PEER WIRING COMMANDS                        ");
        console.log("=================================================================");
        console.log("");
        console.log("After deployment, wire peers with these commands:");
        console.log("");
        console.log("# Base -> Optimism (kUSD)");
        console.log("cast send 0x257579db2702BAeeBFAC5c19d354f2FF39831299 'setPeer(uint32,bytes32)' 30111 <OPTIMISM_KUSD_BYTES32>");
        console.log("");
        console.log("# Optimism -> Base (kUSD)");
        console.log("cast send", address(kusdOft), "'setPeer(uint32,bytes32)' 30184 0x000000000000000000000000257579db2702BAeeBFAC5c19d354f2FF39831299");
        console.log("");
        console.log("# Base -> Optimism (KERNE)");
        console.log("cast send 0x4E1ce62F571893eCfD7062937781A766ff64F14e 'setPeer(uint32,bytes32)' 30111 <OPTIMISM_KERNE_BYTES32>");
        console.log("");
        console.log("# Optimism -> Base (KERNE)");
        console.log("cast send", address(kerneOft), "'setPeer(uint32,bytes32)' 30184 0x0000000000000000000000004E1ce62F571893eCfD7062937781A766ff64F14e");
        console.log("");
    }
}

/**
 * @title DeployOptimismZIN
 * @notice Deploys ZIN infrastructure on Optimism
 * @dev Run with: forge script script/DeployOptimismVault.s.sol:DeployOptimismZIN --rpc-url $OPTIMISM_RPC_URL --broadcast --verify
 */
contract DeployOptimismZIN is Script {
    // Optimism token addresses
    address constant USDC = 0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85; // Native USDC on Optimism
    address constant USDC_E = 0x7F5c764cBc14f9669B88837ca1490cCa17c31607; // Bridged USDC.e
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant WSTETH = 0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb;
    
    // Deployer
    address constant DEPLOYER = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=================================================================");
        console.log("       KERNE OPTIMISM DEPLOYMENT - ZIN                           ");
        console.log("=================================================================");
        console.log("");
        console.log("Deployer:", deployer);
        console.log("");
        
        // Deploy ZIN Pool first (needed as profit vault for executor)
        console.log("Step 1: Deploying KerneZINPool...");
        // Constructor: (admin, _profitRecipient)
        KerneZINPool pool = new KerneZINPool(DEPLOYER, DEPLOYER);
        console.log("  -> ZIN Pool:", address(pool));
        
        // Deploy ZIN Executor
        console.log("");
        console.log("Step 2: Deploying KerneIntentExecutorV2...");
        // Constructor: (admin, solver, _profitVault)
        KerneIntentExecutorV2 executor = new KerneIntentExecutorV2(DEPLOYER, DEPLOYER, address(pool));
        console.log("  -> ZIN Executor:", address(executor));
        
        // Configure supported tokens
        console.log("");
        console.log("Step 3: Configuring supported tokens...");
        pool.supportToken(USDC);
        console.log("  -> USDC supported");
        pool.supportToken(USDC_E);
        console.log("  -> USDC.e supported");
        pool.supportToken(WETH);
        console.log("  -> WETH supported");
        pool.supportToken(WSTETH);
        console.log("  -> wstETH supported");
        
        // Grant SOLVER_ROLE to deployer
        console.log("");
        console.log("Step 4: Granting SOLVER_ROLE to bot wallet...");
        bytes32 solverRole = pool.SOLVER_ROLE();
        pool.grantRole(solverRole, DEPLOYER);
        console.log("  -> SOLVER_ROLE granted to:", DEPLOYER);
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=================================================================");
        console.log("                    ZIN DEPLOYMENT SUMMARY                      ");
        console.log("=================================================================");
        console.log("");
        console.log("ZIN Executor:", address(executor));
        console.log("ZIN Pool:", address(pool));
        console.log("Network: Optimism Mainnet");
        console.log("");
        console.log("Supported Tokens:");
        console.log("  - USDC (native):", USDC);
        console.log("  - USDC.e (bridged):", USDC_E);
        console.log("  - WETH:", WETH);
        console.log("  - wstETH:", WSTETH);
        console.log("");
        console.log("=================================================================");
        console.log("                    NEXT STEPS                                  ");
        console.log("=================================================================");
        console.log("");
        console.log("1. Fund ZIN Pool with USDC and WETH");
        console.log("2. Update bot/.env with Optimism ZIN addresses");
        console.log("3. Add Optimism to ZIN_CHAINS in bot configuration");
        console.log("");
    }
}

/**
 * @title FullOptimismDeployment
 * @notice Complete deployment of all Kerne infrastructure on Optimism
 * @dev Run with: forge script script/DeployOptimismVault.s.sol:FullOptimismDeployment --rpc-url $OPTIMISM_RPC_URL --broadcast --verify
 */
contract FullOptimismDeployment is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // OPTIMISM MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    address constant WSTETH = 0x1F32b1c2345538c0c6f582fCB022739c4A194Ebb;
    address constant LZ_ENDPOINT = 0x1a44076050125825900e736c501f859c50fE728c;
    address constant USDC = 0x0b2C639c533813f4Aa9D7837CAf62653d097Ff85;
    address constant USDC_E = 0x7F5c764cBc14f9669B88837ca1490cCa17c31607;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant DEPLOYER = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=================================================================");
        console.log("   KERNE OPTIMISM - FULL DEPLOYMENT                              ");
        console.log("=================================================================");
        console.log("");
        console.log("Deployer:", deployer);
        console.log("");
        
        // 1. Deploy Vault
        // Constructor: (IERC20 asset, name, symbol, admin, strategist, exchangeDepositAddress)
        console.log("[1/5] Deploying KerneVault...");
        KerneVault vault = new KerneVault(
            IERC20(WSTETH),
            "Kerne wstETH Vault",
            "kvWSTETH",
            deployer,
            deployer,
            DEPLOYER
        );
        vault.setPerformanceFee(500); // 5%
        console.log("  -> Vault:", address(vault));
        
        // 2. Deploy OFTs
        console.log("");
        console.log("[2/5] Deploying kUSD OFT V2...");
        KerneOFTV2 kusdOft = new KerneOFTV2("Kerne USD", "kUSD", LZ_ENDPOINT, deployer);
        console.log("  -> kUSD OFT:", address(kusdOft));
        
        console.log("");
        console.log("[3/5] Deploying KERNE OFT V2...");
        KerneOFTV2 kerneOft = new KerneOFTV2("Kerne", "KERNE", LZ_ENDPOINT, deployer);
        console.log("  -> KERNE OFT:", address(kerneOft));
        
        // 3. Deploy ZIN Pool first
        console.log("");
        console.log("[4/5] Deploying ZIN Pool...");
        // Constructor: (admin, _profitRecipient)
        KerneZINPool pool = new KerneZINPool(deployer, deployer);
        pool.supportToken(USDC);
        pool.supportToken(USDC_E);
        pool.supportToken(WETH);
        pool.supportToken(WSTETH);
        pool.grantRole(pool.SOLVER_ROLE(), deployer);
        console.log("  -> Pool:", address(pool));
        
        // 4. Deploy ZIN Executor
        console.log("");
        console.log("[5/5] Deploying ZIN Executor...");
        // Constructor: (admin, solver, _profitVault)
        KerneIntentExecutorV2 executor = new KerneIntentExecutorV2(deployer, deployer, address(pool));
        console.log("  -> Executor:", address(executor));
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=================================================================");
        console.log("   OPTIMISM DEPLOYMENT COMPLETE                                  ");
        console.log("=================================================================");
        console.log("");
        console.log("KerneVault:", address(vault));
        console.log("kUSD OFT V2:", address(kusdOft));
        console.log("KERNE OFT V2:", address(kerneOft));
        console.log("ZIN Executor:", address(executor));
        console.log("ZIN Pool:", address(pool));
        console.log("");
        console.log("Add to TREASURY_LEDGER.md and wire OFT peers!");
        console.log("=================================================================");
    }
}
