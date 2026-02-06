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

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
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
        insurance = new KerneInsuranceFund(address(asset), address(this));

        prime.transferOwnership(admin);
        // insurance.transferOwnership(admin); // No longer needed as insurance uses AccessControl

        vm.startPrank(admin);
        vault.setInsuranceFund(address(insurance));
        vm.stopPrank();
        
        insurance.grantRole(insurance.DEFAULT_ADMIN_ROLE(), admin);
        insurance.grantRole(keccak256("MANAGER_ROLE"), admin);
        insurance.setAuthorization(address(vault), true);
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
     * This is the core "Anti-Luna" check.
     */
    function testSolvencyInvariant() public {
        // Back the dead shares first to ensure 1:1 exchange rate
        // _decimalsOffset is 3, so 10^3 = 1000 units
        asset.transfer(address(vault), 1000);
        
        uint256 depositAmount = 100 * 1e18;
        asset.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user);

        _checkSolvencyInvariant();
    }

    function _checkSolvencyInvariant() internal {
        uint256 assets = vault.totalAssets();
        uint256 supply = vault.totalSupply();
        
        if (supply > 0) {
            // Solvency ratio: (assets * 10000) / supply
            // Note: convertToAssets(supply) accounts for the offset
            uint256 liabilities = vault.convertToAssets(supply);
            assertTrue(assets >= liabilities, "CRITICAL: Assets must cover supply (Solvency Invariant Broken)");
            assertTrue(vault.getSolvencyRatio() >= 10000, "CRITICAL: Solvency ratio must be >= 100%");
        }
    }

    /**
     * @notice Fuzz test for solvency across various deposit/withdraw/yield scenarios
     */
    function testFuzz_Solvency(uint256 amount, uint256 offChain, uint256 reserve) public {
        // Bound to realistic values to avoid overflow in totalAssets()
        // Max supply of most tokens is < 1e38
        amount = bound(amount, 1e6, 1e27);
        
        // Ensure offChain + reserve >= amount to maintain solvency
        // In a real scenario, the strategist would only report what exists.
        // Here we simulate the strategist reporting enough to cover the deposit.
        offChain = bound(offChain, amount, 1e27);
        reserve = bound(reserve, 0, 1e27);

        // Back the dead shares first to ensure 1:1 exchange rate
        asset.transfer(address(vault), 1000);

        // 1. Deposit
        asset.mint(address(this), amount);
        asset.approve(address(vault), amount);
        vault.deposit(amount, user);

        // 2. Update off-chain assets (Strategist)
        vm.startPrank(strategist);
        vault.updateOffChainAssets(offChain);
        vault.updateHedgingReserve(reserve);
        vm.stopPrank();

        // 3. Check Invariant
        _checkSolvencyInvariant();

        // 4. Partial Withdraw (if liquid)
        uint256 liquid = asset.balanceOf(address(vault));
        if (liquid > 1e6) {
            uint256 withdrawAmount = bound(amount / 2, 1, liquid);
            vm.startPrank(user);
            // Ensure we don't request more than we have in shares
            uint256 userShares = vault.balanceOf(user);
            uint256 maxWithdraw = vault.convertToAssets(userShares);
            if (withdrawAmount > maxWithdraw) withdrawAmount = maxWithdraw;
            
            if (withdrawAmount > 0) {
                uint256 requestId = vault.requestWithdrawal(withdrawAmount);
                vm.warp(block.timestamp + 7 days);
                // Only claim if vault has enough liquid assets
                if (asset.balanceOf(address(vault)) >= withdrawAmount) {
                    vault.claimWithdrawal(requestId);
                }
            }
            vm.stopPrank();
            _checkSolvencyInvariant();
        }
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
        asset.mint(address(this), depositAmount * 2);
        asset.approve(address(vault), depositAmount * 2);
        vault.deposit(depositAmount, user);

        // Simulate loss (off-chain assets drop)
        vm.startPrank(strategist);
        vault.updateOffChainAssets(0); 
        vm.stopPrank();

        // Call checkAndPause to start insolvency timer
        vault.checkAndPause();
        
        // Warp past grace period (4 hours)
        vm.warp(block.timestamp + 5 hours);

        // If assets < liabilities * 1.01 and grace period passed, deposit should fail
        // Note: deposit calls _checkSolvency(false) which pauses if grace period passed.
        // When paused, maxDeposit returns 0, and super.deposit reverts with ERC4626ExceededMaxDeposit.
        vm.expectRevert();
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

        uint256 depositAmount = 1000 * 1e18;
        asset.mint(address(this), depositAmount);
        asset.approve(address(vault), depositAmount);
        vault.deposit(depositAmount, user);

        // Sweep 95% to exchange
        vm.startPrank(admin);
        vault.sweepToExchange(950 * 1e18); // Leave 50 ether
        vm.stopPrank();

        // Update off-chain assets to keep totalAssets consistent
        vm.prank(strategist);
        vault.updateOffChainAssets(950 * 1e18);

        // Try to withdraw 100 ETH (only 50 ETH left on-chain)
        vm.startPrank(user);
        uint256 requestId = vault.requestWithdrawal(100 * 1e18);
        vm.warp(block.timestamp + 7 days);
        vm.expectRevert("Insufficient liquid buffer");
        vault.claimWithdrawal(requestId);
        vm.stopPrank();
    }
}
