// Created: 2026-01-09
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/kUSD.sol";
import "../src/kUSDMinter.sol";
import "../src/KerneVault.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneStressTest is Test {
    kUSD public kusd;
    kUSDMinter public minter;
    KerneVault public vault;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public user = address(0x2);
    address public exchange = makeAddr("exchange");

    function setUp() public {
        vm.startPrank(admin);
        asset = new MockERC20();
        kusd = new kUSD(admin);
        vault = new KerneVault(IERC20(address(asset)), "Kerne LP", "kLP", admin, admin, exchange);
        minter = new kUSDMinter(address(kusd), address(vault), admin);

        kusd.grantRole(kusd.MINTER_ROLE(), address(minter));
        vm.stopPrank();

        asset.mint(user, 10000e18);
    }

    /**
     * @notice Stress test the folding logic with various leverage levels.
     */
    function testStressFolding() public {
        vm.startPrank(user);
        asset.approve(address(vault), 1000e18);
        vault.deposit(1000e18, user);
        uint256 initialKLP = vault.balanceOf(user);
        vault.approve(address(minter), initialKLP);

        // Initial mint: 500 kUSD (CR = 200%)
        minter.mint(initialKLP, 500e18);

        // Simulate swap liquidity in minter
        asset.mint(address(minter), 5000e18);

        // Attempt to fold beyond safety limits
        // Current Debt: 500. Collateral: 1000.
        // Max Debt at 150% CR = 1000 / 1.5 = 666.
        // Max Fold = 166.
        // Health Factor check: (1000 * 100 * 1e18) / (700 * 120) = 1.19e18.
        // Wait, 1.19e18 is > 1.1e18. So 200e18 fold might actually be healthy.
        // Let's try a much larger fold to ensure it reverts.

        vm.expectRevert("Position unhealthy after folding");
        minter.fold(500e18, 0);

        // Safe fold: 100 kUSD
        minter.fold(100e18, 0);

        (uint256 collateral, uint256 debt) = minter.positions(user);
        assertEq(debt, 600e18);
        assertTrue(collateral > initialKLP);

        uint256 hf = minter.getHealthFactor(user);
        console.log("Health Factor after safe fold:", hf);
        assertTrue(hf >= 1.1e18);

        vm.stopPrank();
    }

    /**
     * @notice Stress test the "Emergency Unwind" scenario (LST Depeg).
     */
    function testEmergencyUnwindScenario() public {
        // 1. User is leveraged
        vm.startPrank(user);
        asset.approve(address(vault), 1000e18);
        vault.deposit(1000e18, user);
        vault.approve(address(minter), vault.balanceOf(user));
        minter.mint(vault.balanceOf(user), 500e18);

        asset.mint(address(minter), 1000e18);
        minter.fold(100e18, 0);
        vm.stopPrank();

        // 2. LST Depeg / Vault Loss
        // Simulate 20% loss in vault assets
        vm.startPrank(admin);
        vault.setFounder(admin); // Ensure sweep destination exists
        uint256 vaultAssets = vault.totalAssets();
        vault.sweepToExchange(vaultAssets * 20 / 100);
        vm.stopPrank();

        uint256 hf = minter.getHealthFactor(user);
        console.log("Health Factor after 20% depeg:", hf);

        // 3. Rebalance by Manager
        vm.startPrank(admin);
        // Force rebalance by simulating a larger depeg or lower threshold
        // For the test, we'll just call rebalance if HF is below a safer threshold like 1.3e18
        if (hf < 1.3e18) {
            // Simulate swap liquidity for rebalance
            asset.mint(address(minter), 200e18);
            minter.rebalance(user, 200e18);
        }
        vm.stopPrank();

        uint256 hfAfter = minter.getHealthFactor(user);
        console.log("Health Factor after rebalance:", hfAfter);
        assertTrue(hfAfter > hf);
    }

    /**
     * @notice Test the circuit breakers.
     */
    function testCircuitBreakers() public {
        vm.startPrank(admin);
        vault.setCircuitBreakers(10e18, 5e18, 0); // Disable solvency for initial deposit
        vm.stopPrank();

        vm.startPrank(user);
        asset.approve(address(vault), 20e18);

        // 1. Deposit limit
        vm.expectRevert("Deposit limit exceeded");
        vault.deposit(11e18, user);

        vault.deposit(10e18, user);
        vm.stopPrank();

        vm.startPrank(admin);
        vault.setCircuitBreakers(10e18, 5e18, 0); // Keep solvency disabled for withdraw test
        vm.stopPrank();

        vm.startPrank(user);

        // 2. Withdraw limit
        vm.expectRevert("Withdraw limit exceeded");
        vault.withdraw(6e18, user, user);

        vault.withdraw(5e18, user, user);
        vm.stopPrank();

        // 3. Solvency threshold
        // Simulate insolvency by decreasing assets.
        vm.startPrank(admin);
        vault.setFounder(admin);
        vault.sweepToExchange(4 ether); // totalAssets = 5 - 4 = 1. liabilities = ~10e18. ratio = ~0.01%
        
        // Now enable solvency threshold
        vault.setCircuitBreakers(10e18, 5e18, 10100);
        vm.stopPrank();

        vm.startPrank(user);
        vm.expectRevert("Solvency below threshold");
        vault.deposit(1e18, user);
        vm.stopPrank();
    }

    /**
     * @notice Test the dynamic deposit caps.
     */
    function testVaultCap() public {
        vm.startPrank(admin);
        vault.setMaxTotalAssets(100e18);
        vm.stopPrank();

        vm.startPrank(user);
        asset.approve(address(vault), 200e18);

        // Should succeed
        vault.deposit(50e18, user);

        // Should fail (50 + 60 = 110 > 100)
        vm.expectRevert("Vault cap exceeded");
        vault.deposit(60e18, user);

        vm.stopPrank();
    }
}
