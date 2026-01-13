// Created: 2026-01-07
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "src/KerneVault.sol";
import "src/KernePrime.sol";
import "src/KerneInsuranceFund.sol";
import "src/KerneYieldOracle.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") {
        _mint(msg.sender, 1000000 * 1e18);
    }
}

contract KerneSecuritySuite is Test {
    KerneVault vault;
    KernePrime prime;
    KerneInsuranceFund insurance;
    MockAsset asset;

    address admin = address(0x1);
    address strategist = address(0x2);
    address partner = address(0x3);
    address user = address(0x4);

    function setUp() public {
        asset = new MockAsset();

        vault = new KerneVault(asset, "Kerne Vault", "kVault", admin, strategist, address(0x5));

        prime = new KernePrime();
        insurance = new KerneInsuranceFund(address(asset));

        prime.transferOwnership(admin);
        insurance.transferOwnership(admin);

        vm.startPrank(admin);
        vault.setInsuranceFund(address(insurance));
        insurance.setAuthorization(address(vault), true);
        vm.stopPrank();
    }

    function testPrimeLiquidation() public {
        // 1. Setup Prime Account
        vm.startPrank(admin);
        // createPrimeAccount now requires an explicit credit line
        prime.createPrimeAccount(partner, address(vault), 100_000e18);
        vm.stopPrank();

        // 2. Allocate funds to Prime
        uint256 amount = 10 * 1e18;
        asset.transfer(address(vault), amount);

        vm.startPrank(partner);
        prime.allocateToPrime(amount);
        assertEq(prime.getHealthFactor(partner), 100e18);
        vm.stopPrank();

        // 3. Simulate Debt (Manual for test)
        // In real scenario, this would be via a borrow function
        // We'll use vm.store to simulate debt for the health factor check
        // PrimeAccount struct: active(bool), balance(uint256), debt(uint256)...
        // mapping is at slot 1 (Ownable=0)
        // debt is at struct offset 2 (active=0, balance=1)
        bytes32 partnerSlot = keccak256(abi.encode(partner, uint256(1))); // mapping slot
        vm.store(address(prime), bytes32(uint256(partnerSlot) + 2), bytes32(uint256(10 * 1e18))); // 10 kUSD debt

        // Health factor should now be ~0.9 (10 collateral / 1.1 threshold / 10 debt)
        uint256 hf = prime.getHealthFactor(partner);
        assertTrue(hf < 1e18);

        // 4. Liquidate
        uint256 liquidatorBalanceBefore = asset.balanceOf(address(this));
        prime.liquidate(partner);
        uint256 liquidatorBalanceAfter = asset.balanceOf(address(this));

        assertTrue(liquidatorBalanceAfter > liquidatorBalanceBefore);
        assertEq(prime.getHealthFactor(partner), 100e18); // Debt cleared
    }

    function testInsuranceFundClaim() public {
        uint256 amount = 5 * 1e18;
        asset.transfer(address(insurance), amount * 2); // Deposit 10 ETH to allow 5 ETH claim (50% limit)

        // Move time forward to bypass cooldown
        vm.warp(block.timestamp + 2 hours);

        vm.startPrank(strategist);
        vault.drawFromInsuranceFund(amount);
        vm.stopPrank();

        assertEq(asset.balanceOf(address(vault)), amount);
    }

    /**
     * @notice Invariant: Total Assets >= Total Liabilities (Solvency)
     */
    function testSolvencyInvariant() public {
        // Initial state: 1000 dead shares minted to admin
        // totalAssets() = 0
        // totalSupply() = 1000
        
        // Back the dead shares first to ensure 1:1 exchange rate
        asset.transfer(address(vault), 1000);
        
        uint256 depositAmount = 100 * 1e18;
        asset.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user);

        uint256 assets = vault.totalAssets();
        uint256 supply = vault.totalSupply();
        
        // Solvency ratio: (assets * 10000) / supply
        // With 1000 dead shares backed and 100e18 deposit, assets should be 100e18 + 1000
        // and supply should be 100e18 + 1000.
        
        assertTrue(assets >= supply, "Assets must cover supply");
        assertTrue(vault.getSolvencyRatio() >= 10000, "Solvency ratio must be >= 100%");
    }

    /**
     * @notice Invariant: Oracle updates must be bounded by maxPriceDeviationBps
     */
    function testOracleDeviationInvariant() public {
        KerneYieldOracle oracle = new KerneYieldOracle(admin);
        vm.startPrank(admin);
        oracle.grantRole(oracle.UPDATER_ROLE(), strategist);
        oracle.grantRole(oracle.UPDATER_ROLE(), admin); // Grant to admin for multi-sig simulation
        oracle.grantRole(oracle.UPDATER_ROLE(), address(this));
        vault.setYieldOracle(address(oracle));
        vm.stopPrank();

        // Initial observation - needs requiredConfirmations (default 3)
        vm.startPrank(strategist);
        oracle.updateYield(address(vault));
        vm.stopPrank();
        
        vm.startPrank(admin);
        oracle.updateYield(address(vault));
        vm.stopPrank();
        
        oracle.updateYield(address(vault));

        // Simulate massive profit (outlier)
        asset.transfer(address(vault), 1000 * 1e18);
        
        vm.startPrank(strategist);
        vm.expectRevert("Outlier rejected: Price deviation too high");
        oracle.updateYield(address(vault));
        vm.stopPrank();
    }

    /**
     * @notice Invariant: Minimum solvency threshold enforcement
     */
    function testMinSolvencyThresholdInvariant() public {
        vm.startPrank(admin);
        vault.setCircuitBreakers(0, 0, 10100); // 101% min solvency
        vm.stopPrank();

        uint256 depositAmount = 100 * 1e18;
        asset.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user);

        // Simulate loss (off-chain assets drop)
        vm.startPrank(strategist);
        vault.updateOffChainAssets(0); 
        vm.stopPrank();

        // If assets < liabilities * 1.01, deposit should fail
        vm.expectRevert("Solvency below threshold");
        vault.deposit(10 * 1e18, user);
    }

    /**
     * @notice Invariant: Redemption liquidity buffer
     */
    function testRedemptionLiquidityInvariant() public {
        // Set exchange deposit address to avoid "No sweep destination"
        vm.startPrank(admin);
        vault.setTreasury(address(0x6));
        vm.stopPrank();

        uint256 depositAmount = 100 * 1e18;
        asset.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user);

        // Sweep 95% to exchange
        vm.startPrank(admin);
        vault.sweepToExchange(95 * 1e18);
        vm.stopPrank();

        // Try to withdraw 10 ETH (only 5 ETH left on-chain)
        vm.startPrank(user);
        vm.expectRevert("Insufficient liquid buffer");
        vault.withdraw(10 * 1e18, user, user);
        vm.stopPrank();
    }
}
