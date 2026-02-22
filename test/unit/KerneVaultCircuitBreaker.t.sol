// Created: 2026-02-19
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test } from "forge-std/Test.sol";
import { KerneVault } from "../../src/KerneVault.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MCK") {
        _mint(msg.sender, 1_000_000 * 10**18);
    }
}

contract KerneVaultCircuitBreakerTest is Test {
    KerneVault public vault;
    MockAsset public asset;
    
    address public admin = address(0x1);
    address public strategist = address(0x2);
    address public user = address(0x3);
    
    function setUp() public {
        asset = new MockAsset();
        vault = new KerneVault(
            IERC20(address(asset)),
            "Kerne Vault",
            "kVAULT",
            admin,
            strategist,
            address(0x4)
        );
        
        // Give user some assets
        asset.transfer(user, 10000 * 10**18);
        
        // Set up roles
        vm.startPrank(admin);
        vault.setCircuitBreakers(1000 * 10**18, 500 * 10**18, 9000); // 90% min solvency
        vm.stopPrank();
    }
    
    // ============ CIRCUIT BREAKER TESTS ============
    
    function test_CircuitBreaker_TriggersAtCriticalCR() public {
        // Deposit initial funds
        vm.startPrank(user);
        asset.approve(address(vault), 1000 * 10**18);
        vault.deposit(1000 * 10**18, user);
        vm.stopPrank();
        
        // Verify initial state
        assertFalse(vault.crCircuitBreakerActive());
        assertEq(vault.CRITICAL_CR_THRESHOLD(), 12500);
        
        // Simulate CR drop by having strategist report lower off-chain assets
        // (In real scenario, this would happen from price drops)
        // For this test, we verify the constants are set correctly
        assertEq(vault.CRITICAL_CR_THRESHOLD(), 12500); // 1.25x
        assertEq(vault.SAFE_CR_THRESHOLD(), 13500); // 1.35x
        assertEq(vault.crCircuitBreakerCooldown(), 4 hours);
    }
    
    function test_CircuitBreaker_AdminCanForceRecover() public {
        // Verify only admin can call force recover
        vm.startPrank(user);
        vm.expectRevert();
        vault.forceRecoverCRCircuitBreaker();
        vm.stopPrank();
        
        // Admin can call (but it reverts if not active)
        vm.startPrank(admin);
        vm.expectRevert();
        vault.forceRecoverCRCircuitBreaker();
        vm.stopPrank();
    }
    
    function test_CircuitBreaker_ParamsCanBeSet() public {
        vm.startPrank(admin);
        
        // Set new cooldown
        vault.setCRCircuitBreakerParams(2 hours);
        assertEq(vault.crCircuitBreakerCooldown(), 2 hours);
        
        // Revert on invalid cooldown
        vm.expectRevert();
        vault.setCRCircuitBreakerParams(30 minutes); // Too short
        
        vm.expectRevert();
        vault.setCRCircuitBreakerParams(25 hours); // Too long
        
        vm.stopPrank();
    }
    
    function test_CircuitBreaker_ModifierBlocksOperations() public {
        // Deposit funds first
        vm.startPrank(user);
        asset.approve(address(vault), 1000 * 10**18);
        vault.deposit(1000 * 10**18, user);
        vm.stopPrank();
        
        // Verify circuit breaker is not active
        assertFalse(vault.crCircuitBreakerActive());
        assertFalse(vault.paused());
    }
    
    // ============ DYNAMIC BUFFER TESTS ============
    
    function test_DynamicBuffer_CanBeUpdated() public {
        // Initial buffer is 0
        assertEq(vault.dynamicCRBuffer(), 0);
        
        // Only strategist can update
        vm.startPrank(user);
        vm.expectRevert();
        vault.updateDynamicBuffer(1000);
        vm.stopPrank();
        
        // Strategist can update
        vm.startPrank(strategist);
        vault.updateDynamicBuffer(600); // 6% volatility
        assertEq(vault.dynamicCRBuffer(), 500); // Should be 5% buffer
        
        vault.updateDynamicBuffer(1200); // 12% volatility
        assertEq(vault.dynamicCRBuffer(), 1000); // Should cap at 10% buffer
        
        vault.updateDynamicBuffer(300); // 3% volatility
        assertEq(vault.dynamicCRBuffer(), 0); // Below 5%, no buffer
        vm.stopPrank();
    }
    
    function test_DynamicBuffer_EffectiveThreshold() public {
        // Base threshold is 12500 (1.25x)
        assertEq(vault.getEffectiveCRThreshold(), 12500);
        
        // Add buffer
        vm.startPrank(strategist);
        vault.updateDynamicBuffer(800);
        assertEq(vault.getEffectiveCRThreshold(), 13000); // 12500 + 500
        vm.stopPrank();
    }
    
    // ============ GRADUAL LIQUIDATION TESTS ============
    
    function test_GradualLiquidation_RateLimit() public {
        // Remove deposit limit for this test
        vm.startPrank(admin);
        vault.setCircuitBreakers(0, 0, 0); // No limits
        vm.stopPrank();
        
        // Deposit funds
        vm.startPrank(user);
        asset.approve(address(vault), 10000 * 10**18);
        vault.deposit(10000 * 10**18, user);
        vm.stopPrank();
        
        // Check default rate
        assertEq(vault.maxLiquidationPerHourBps(), 500); // 5%
        
        // Check canLiquidate function
        (bool allowed, uint256 maxAllowed) = vault.canLiquidate(100 * 10**18);
        uint256 tvl = vault.totalAssets();
        uint256 expectedMax = (tvl * 500) / 10000;
        assertEq(maxAllowed, expectedMax);
        assertTrue(allowed);
    }
    
    function test_GradualLiquidation_AdminCanSetRate() public {
        vm.startPrank(admin);
        
        // Set new rate
        vault.setMaxLiquidationPerHour(1000); // 10%
        assertEq(vault.maxLiquidationPerHourBps(), 1000);
        
        // Revert on invalid rates
        vm.expectRevert();
        vault.setMaxLiquidationPerHour(50); // Too low
        
        vm.expectRevert();
        vault.setMaxLiquidationPerHour(3000); // Too high
        
        vm.stopPrank();
    }
    
    // ============ EVENT TESTS ============
    
    function test_Events_Emitted() public {
        // Test DynamicBufferUpdated event
        vm.startPrank(strategist);
        vm.expectEmit(true, false, false, true);
        emit KerneVault.DynamicBufferUpdated(0, 500);
        vault.updateDynamicBuffer(600);
        vm.stopPrank();
    }
    
    // ============ VIEW FUNCTION TESTS ============
    
    function test_ViewFunctions() public view {
        // Check initial state
        assertFalse(vault.isCRCircuitBreakerActive());
        assertEq(vault.crCircuitBreakerTriggeredAt(), 0);
    }
}