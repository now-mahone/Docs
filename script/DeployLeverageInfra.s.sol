// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneDexAdapter.sol";
import "../src/kUSDMinter.sol";

/**
 * @title DeployLeverageInfra
 * @notice Deploys KerneDexAdapter and configures kUSDMinter for leverage/folding
 * @dev Run with: forge script script/DeployLeverageInfra.s.sol:DeployDexAdapter --rpc-url $BASE_RPC_URL --broadcast --verify
 */
contract DeployDexAdapter is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // BASE MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    address constant AERODROME_ROUTER = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    
    // kUSD OFT V2 (from TREASURY_LEDGER.md)
    address constant KUSD = 0x257579db2702BAeeBFAC5c19d354f2FF39831299;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=== Deploying KerneDexAdapter ===");
        console.log("Deployer:", deployer);
        console.log("Aerodrome Router:", AERODROME_ROUTER);
        
        // Deploy the DEX Adapter
        KerneDexAdapter adapter = new KerneDexAdapter(AERODROME_ROUTER);
        
        console.log("KerneDexAdapter deployed at:", address(adapter));
        
        // Configure routing: kUSD -> WETH for folding operations
        // kUSD typically doesn't have deep liquidity, so we might need to route kUSD -> USDC -> WETH
        // For now, let's set up kUSD/WETH direct and kUSD/USDC/WETH hop
        
        // Configure kUSD -> WETH to possibly route through USDC if pool is thin
        // adapter.setNeedsHop(KUSD, WETH, true);  // Uncomment if kUSD/WETH pool is thin
        
        console.log("");
        console.log("=== Configuration ===");
        console.log("Router:", address(adapter.router()));
        console.log("Factory:", adapter.factory());
        console.log("WETH:", WETH);
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Deployment Complete ===");
        console.log("KerneDexAdapter:", address(adapter));
        console.log("");
        console.log("Next steps:");
        console.log("1. Configure kUSDMinter to use this adapter");
        console.log("2. Set up routing hops if needed for thin liquidity pairs");
        console.log("3. Test swap functionality on fork before mainnet");
    }
}

/**
 * @title DeployKUSDMinter
 * @notice Deploys kUSDMinter for leverage operations
 * @dev Run with: forge script script/DeployLeverageInfra.s.sol:DeployKUSDMinter --rpc-url $BASE_RPC_URL --broadcast --verify
 */
contract DeployKUSDMinter is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // BASE MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    // kUSD OFT V2 (from TREASURY_LEDGER.md)
    address constant KUSD = 0x257579db2702BAeeBFAC5c19d354f2FF39831299;
    
    // KerneVault (from TREASURY_LEDGER.md)
    address constant KERNE_VAULT = 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=== Deploying kUSDMinter ===");
        console.log("Deployer:", deployer);
        console.log("kUSD:", KUSD);
        console.log("KerneVault:", KERNE_VAULT);
        
        // Deploy kUSDMinter
        kUSDMinter minter = new kUSDMinter(KUSD, KERNE_VAULT, deployer);
        
        console.log("kUSDMinter deployed at:", address(minter));
        
        // Log initial configuration
        console.log("");
        console.log("=== Initial Configuration ===");
        console.log("Mint Collateral Ratio:", minter.MINT_COLLATERAL_RATIO() / 1e16, "%");
        console.log("Liquidation Threshold:", minter.LIQUIDATION_THRESHOLD() / 1e16, "%");
        console.log("Min Health Factor:", minter.minHealthFactor() / 1e16, "%");
        console.log("Liquidation Bonus:", minter.LIQUIDATION_BONUS() / 1e16, "%");
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Deployment Complete ===");
        console.log("kUSDMinter:", address(minter));
        console.log("");
        console.log("Next steps:");
        console.log("1. Deploy KerneDexAdapter");
        console.log("2. Call kUSDMinter.setDexAggregator() with adapter address");
        console.log("3. Grant MINTER_ROLE on kUSD to kUSDMinter");
    }
}

/**
 * @title ConfigureKUSDMinter
 * @notice Configures an existing kUSDMinter with DEX aggregator
 * @dev Run with: forge script script/DeployLeverageInfra.s.sol:ConfigureKUSDMinter --rpc-url $BASE_RPC_URL --broadcast
 */
contract ConfigureKUSDMinter is Script {
    // UPDATE THESE AFTER DEPLOYMENT
    address constant KUSD_MINTER = address(0); // TODO: Set after deployment
    address constant DEX_ADAPTER = address(0); // TODO: Set after deployment
    
    function run() external {
        require(KUSD_MINTER != address(0), "Set KUSD_MINTER address");
        require(DEX_ADAPTER != address(0), "Set DEX_ADAPTER address");
        
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=== Configuring kUSDMinter ===");
        console.log("kUSDMinter:", KUSD_MINTER);
        console.log("DexAdapter:", DEX_ADAPTER);
        
        kUSDMinter minter = kUSDMinter(KUSD_MINTER);
        minter.setDexAggregator(DEX_ADAPTER);
        
        console.log("DEX Aggregator set successfully!");
        
        vm.stopBroadcast();
    }
}

/**
 * @title FullLeverageSetup
 * @notice Complete setup: Deploy adapter, deploy minter, configure everything
 * @dev Run with: forge script script/DeployLeverageInfra.s.sol:FullLeverageSetup --rpc-url $BASE_RPC_URL --broadcast --verify
 */
contract FullLeverageSetup is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // BASE MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    address constant AERODROME_ROUTER = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    address constant KUSD = 0x257579db2702BAeeBFAC5c19d354f2FF39831299;
    address constant KERNE_VAULT = 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=================================================================");
        console.log("       KERNE LEVERAGE INFRASTRUCTURE - FULL DEPLOYMENT          ");
        console.log("=================================================================");
        console.log("");
        console.log("Deployer:", deployer);
        console.log("");
        
        // Step 1: Deploy DEX Adapter
        console.log("Step 1: Deploying KerneDexAdapter...");
        KerneDexAdapter adapter = new KerneDexAdapter(AERODROME_ROUTER);
        console.log("  -> KerneDexAdapter:", address(adapter));
        
        // Step 2: Deploy kUSDMinter
        console.log("");
        console.log("Step 2: Deploying kUSDMinter...");
        kUSDMinter minter = new kUSDMinter(KUSD, KERNE_VAULT, deployer);
        console.log("  -> kUSDMinter:", address(minter));
        
        // Step 3: Configure kUSDMinter with DEX adapter
        console.log("");
        console.log("Step 3: Configuring kUSDMinter with DEX adapter...");
        minter.setDexAggregator(address(adapter));
        console.log("  -> DEX Aggregator set!");
        
        // Step 4: Configure routing if needed (kUSD -> WETH might need hop)
        // Note: This depends on whether kUSD/WETH pool exists with sufficient liquidity
        // For safety, we'll set up the hop route through USDC
        console.log("");
        console.log("Step 4: Configuring swap routing...");
        adapter.setNeedsHop(KUSD, WETH, true);  // kUSD -> USDC -> WETH
        console.log("  -> kUSD/WETH hop routing enabled (via USDC)");
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=================================================================");
        console.log("                    DEPLOYMENT SUMMARY                          ");
        console.log("=================================================================");
        console.log("");
        console.log("KerneDexAdapter:", address(adapter));
        console.log("kUSDMinter:", address(minter));
        console.log("");
        console.log("Parameters:");
        console.log("  Mint Collateral Ratio: 150%");
        console.log("  Liquidation Threshold: 120%");
        console.log("  Min Health Factor: 130%");
        console.log("  Liquidation Bonus: 5%");
        console.log("");
        console.log("=================================================================");
        console.log("                    REMAINING STEPS                             ");
        console.log("=================================================================");
        console.log("");
        console.log("1. Grant MINTER_ROLE on kUSD to kUSDMinter:");
        console.log("   cast send", KUSD);
        console.log("     'grantRole(bytes32,address)'");
        console.log("     <MINTER_ROLE_HASH>", address(minter));
        console.log("");
        console.log("2. Update TREASURY_LEDGER.md with new addresses");
        console.log("");
        console.log("3. Test leverage() and fold() on local fork before mainnet");
        console.log("");
        console.log("=================================================================");
    }
}
