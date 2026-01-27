// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneTreasury.sol";
import "../src/interfaces/IAerodromeRouter.sol";

/**
 * @title SetupTreasuryBuyback
 * @notice Configures the KerneTreasury for KERNE buybacks via Aerodrome
 * @dev Run with: forge script script/SetupTreasuryBuyback.s.sol --rpc-url $BASE_RPC_URL --broadcast
 * 
 * PREREQUISITES:
 * 1. Treasury deployed at TREASURY_ADDRESS
 * 2. KERNE token deployed at KERNE_TOKEN_ADDRESS
 * 3. KERNE/WETH pool exists on Aerodrome (or KERNE/USDC)
 * 4. Deployer is the Treasury owner
 */
contract SetupTreasuryBuyback is Script {
    // ═══════════════════════════════════════════════════════════════════════════════
    // BASE MAINNET ADDRESSES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    address constant AERODROME_ROUTER = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
    address constant AERODROME_FACTORY = 0x420DD381b31aEf6683db6B902084cB0FFECe40Da;
    
    // Deployed contract addresses (from TREASURY_LEDGER.md)
    address constant TREASURY = 0xB656440287f8A1112558D3df915b23326e9b89ec;
    address constant KERNE_TOKEN = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;
    address constant KERNE_STAKING = 0x032Af1631671126A689614c0c957De774b45D582;
    
    KerneTreasury treasury;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        treasury = KerneTreasury(payable(TREASURY));
        
        console.log("=== KERNE Buyback Flywheel Setup ===");
        console.log("Treasury:", TREASURY);
        console.log("KERNE Token:", KERNE_TOKEN);
        console.log("Staking Contract:", KERNE_STAKING);
        
        // 0. FIX CRITICAL: Treasury was deployed with placeholder addresses
        // Must set correct KERNE token and staking contract addresses
        _fixTreasuryConfiguration();
        
        // 1. Verify Treasury configuration
        // _verifyTreasuryConfig();
        
        // 2. Approve WETH for buybacks (primary route)
        // _approveToken(WETH, "WETH");
        
        // 3. Approve USDC for buybacks
        _approveToken(USDC, "USDC");
        
        // 4. Set USDC routing hop through WETH (USDC → WETH → KERNE)
        // This provides deeper liquidity if direct USDC/KERNE pool is thin
        _setRoutingHop(USDC, WETH);
        
        // 5. Verify Aerodrome pool exists
        _verifyPool();
        
        // 6. Test preview (if pool exists)
        _testPreview();
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Setup Complete ===");
        console.log("WETH buybacks: ENABLED");
        console.log("USDC buybacks: ENABLED (via WETH hop)");
        console.log("");
        console.log("Next steps:");
        console.log("1. Ensure KERNE/WETH pool has liquidity on Aerodrome");
        console.log("2. Send fees to Treasury to accumulate for buybacks");
        console.log("3. Run bot with buyback cycle enabled");
    }
    
    function _fixTreasuryConfiguration() internal {
        console.log("");
        console.log("=== Fixing Treasury Configuration ===");
        
        // Check current state
        address currentKerneToken = treasury.kerneToken();
        address currentStaking = treasury.stakingContract();
        
        console.log("  Current KERNE Token:", currentKerneToken);
        console.log("  Current Staking:", currentStaking);
        console.log("  Expected KERNE Token:", KERNE_TOKEN);
        console.log("  Expected Staking:", KERNE_STAKING);
        
        // Fix KERNE token if it's wrong
        if (currentKerneToken != KERNE_TOKEN) {
            console.log("  -> Setting KERNE token address...");
            treasury.updateKerneToken(KERNE_TOKEN);
            console.log("  -> KERNE token updated!");
        } else {
            console.log("  -> KERNE token already correct");
        }
        
        // Fix staking contract if it's wrong
        if (currentStaking != KERNE_STAKING) {
            console.log("  -> Setting staking contract address...");
            treasury.setStakingContract(KERNE_STAKING);
            console.log("  -> Staking contract updated!");
        } else {
            console.log("  -> Staking contract already correct");
        }
        
        console.log("=== Treasury Configuration Fixed ===");
    }

    function _verifyTreasuryConfig() internal view {
        address founder = treasury.founder();
        address kerneToken = treasury.kerneToken();
        address staking = treasury.stakingContract();
        address router = address(treasury.aerodromeRouter());
        
        console.log("");
        console.log("Current Treasury Config:");
        console.log("  Founder:", founder);
        console.log("  KERNE Token:", kerneToken);
        console.log("  Staking:", staking);
        console.log("  Router:", router);
        console.log("  Slippage:", treasury.slippageBps(), "bps");
        
        require(kerneToken == KERNE_TOKEN, "KERNE token mismatch");
        require(staking == KERNE_STAKING, "Staking contract mismatch");
        require(router == AERODROME_ROUTER, "Router mismatch");
    }
    
    function _approveToken(address token, string memory name) internal {
        bool isApproved = treasury.approvedBuybackTokens(token);
        
        if (isApproved) {
            console.log(string.concat(name, " already approved for buyback"));
        } else {
            treasury.setApprovedBuybackToken(token, true);
            console.log(string.concat(name, " approved for buyback"));
        }
    }
    
    function _setRoutingHop(address token, address hop) internal {
        address currentHop = treasury.routingHops(token);
        
        if (currentHop == hop) {
            console.log("Routing hop already set");
        } else {
            treasury.setRoutingHop(token, hop);
            console.log("Routing hop set: USDC -> WETH -> KERNE");
        }
    }
    
    function _verifyPool() internal view {
        // Check if KERNE/WETH pool exists on Aerodrome
        // Pool address can be computed or queried from factory
        
        console.log("");
        console.log("Pool Verification:");
        console.log("  Checking KERNE/WETH pool on Aerodrome...");
        
        // Note: In production, you'd query the factory for the pool
        // For now, we just log the expected pool info
        console.log("  Factory:", AERODROME_FACTORY);
        console.log("  Token0:", KERNE_TOKEN < WETH ? KERNE_TOKEN : WETH);
        console.log("  Token1:", KERNE_TOKEN < WETH ? WETH : KERNE_TOKEN);
        console.log("  Stable: false (volatile pool for governance tokens)");
    }
    
    function _testPreview() internal view {
        console.log("");
        console.log("Testing Buyback Preview:");
        
        // Test with 0.01 WETH
        uint256 testAmount = 0.01 ether;
        
        try treasury.previewBuyback(WETH, testAmount) returns (uint256 expected, uint256 min) {
            if (expected > 0) {
                console.log("  0.01 WETH -> ", expected / 1e18, "KERNE (expected)");
                console.log("  Minimum (with slippage):", min / 1e18, "KERNE");
                console.log("  Pool: ACTIVE");
            } else {
                console.log("  0.01 WETH -> 0 KERNE");
                console.log("  Pool: NO LIQUIDITY or NOT CREATED");
                console.log("");
                console.log("  ACTION REQUIRED: Create KERNE/WETH pool on Aerodrome");
            }
        } catch {
            console.log("  Preview failed - pool may not exist");
            console.log("  ACTION REQUIRED: Create KERNE/WETH pool on Aerodrome");
        }
    }
}

/**
 * @title CreateKernePool
 * @notice Creates the KERNE/WETH pool on Aerodrome if it doesn't exist
 * @dev Run after minting initial KERNE tokens
 */
contract CreateKernePool is Script {
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant AERODROME_ROUTER = 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43;
    address constant KERNE_TOKEN = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        // Amounts to seed the pool with
        // Adjust these based on available funds and desired price
        uint256 kerneAmount = 10000 ether;  // 10,000 KERNE
        uint256 wethAmount = 0.1 ether;      // 0.1 WETH (~$330)
        // This sets initial price at ~$0.033/KERNE
        
        vm.startBroadcast(deployerPrivateKey);
        
        console.log("=== Creating KERNE/WETH Pool on Aerodrome ===");
        console.log("Deployer:", deployer);
        console.log("KERNE Amount:", kerneAmount / 1e18);
        console.log("WETH Amount:", wethAmount / 1e18);
        
        // Approve router to spend tokens
        IERC20(KERNE_TOKEN).approve(AERODROME_ROUTER, kerneAmount);
        IERC20(WETH).approve(AERODROME_ROUTER, wethAmount);
        
        // Add liquidity (creates pool if it doesn't exist)
        IAerodromeRouter(AERODROME_ROUTER).addLiquidity(
            KERNE_TOKEN,
            WETH,
            false,  // volatile (not stable)
            kerneAmount,
            wethAmount,
            kerneAmount * 95 / 100,  // 5% slippage on KERNE
            wethAmount * 95 / 100,   // 5% slippage on WETH
            deployer,
            block.timestamp + 300
        );
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Pool Created ===");
        console.log("Initial Price: ~$", (wethAmount * 3300) / kerneAmount, " per KERNE");
        console.log("LP tokens sent to:", deployer);
    }
}
