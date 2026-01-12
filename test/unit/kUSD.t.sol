// Created: 2025-12-29
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

contract kUSDTest is Test {
    kUSD public kusd;
    kUSDMinter public minter;
    KerneVault public vault;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public user = address(0x2);
    address public liquidator = address(0x3);
    address public exchange = makeAddr("exchange");

    function setUp() public {
        vm.startPrank(admin);
        asset = new MockERC20();
        kusd = new kUSD(admin);
        vault = new KerneVault(IERC20(address(asset)), "Kerne LP", "kLP", admin, admin, exchange);
        minter = new kUSDMinter(address(kusd), address(vault), admin);

        kusd.grantRole(kusd.MINTER_ROLE(), address(minter));
        vm.stopPrank();

        asset.mint(user, 1000e18);
        asset.mint(liquidator, 1000e18);
    }

    function testMintKUSD() public {
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);

        uint256 kLPAmount = vault.balanceOf(user);
        vault.approve(address(minter), kLPAmount);

        // Mint 50 kUSD (100 kLP collateral, price 1:1, CR = 200%)
        minter.mint(kLPAmount, 50e18);

        assertEq(kusd.balanceOf(user), 50e18);
        (uint256 collateral, uint256 debt) = minter.positions(user);
        assertEq(collateral, kLPAmount);
        assertEq(debt, 50e18);
        vm.stopPrank();
    }

    function testMintInsufficientCollateralReverts() public {
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);

        uint256 kLPAmount = vault.balanceOf(user);
        vault.approve(address(minter), kLPAmount);

        // Try to mint 80 kUSD (100 kLP collateral, price 1:1, CR = 125% < 150%)
        vm.expectRevert("Insufficient collateral");
        minter.mint(kLPAmount, 80e18);
        vm.stopPrank();
    }

    function testBurnKUSD() public {
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);
        uint256 kLPAmount = vault.balanceOf(user);
        vault.approve(address(minter), kLPAmount);
        minter.mint(kLPAmount, 50e18);

        kusd.approve(address(minter), 50e18);
        minter.burn(50e18, kLPAmount);

        assertEq(kusd.balanceOf(user), 0);
        assertEq(vault.balanceOf(user), kLPAmount);
        (uint256 collateral, uint256 debt) = minter.positions(user);
        assertEq(collateral, 0);
        assertEq(debt, 0);
        vm.stopPrank();
    }

    function testLiquidation() public {
        // 1. User deposits and mints at 200% CR to be safe
        vm.startPrank(user);
        asset.approve(address(vault), 200e18);
        vault.deposit(200e18, user);
        uint256 kLPAmount = vault.balanceOf(user);
        vault.approve(address(minter), kLPAmount);
        minter.mint(kLPAmount, 100e18);
        vm.stopPrank();

        // 2. Price of kLP drops
        vm.startPrank(admin);
        vault.setTreasury(admin); // Set treasury to avoid "No sweep destination"
        vault.sweepToExchange(150e18);
        vm.stopPrank();

        // totalAssets = 50e18. totalSupply ~ 200e18. Price ~ 0.25.
        // Collateral Value = 200e18 * 0.25 = 50e18.
        // Debt = 100e18. CR = 50% < 120%.

        assertTrue(!minter.isHealthy(user, 120));

        // 3. Liquidator repays debt
        vm.startPrank(liquidator);
        deal(address(kusd), liquidator, 100e18);
        kusd.approve(address(minter), 100e18);
        minter.liquidate(user);
        vm.stopPrank();

        (, uint256 debt) = minter.positions(user);
        assertEq(debt, 0);
        assertTrue(vault.balanceOf(liquidator) > 0);
    }

    function testFolding() public {
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);
        uint256 kLPAmount = vault.balanceOf(user);
        vault.approve(address(minter), kLPAmount);

        // Initial mint to establish position
        minter.mint(kLPAmount, 50e18);

        // Provide WETH to minter to simulate swap result
        asset.mint(address(minter), 150e18);

        // Fold: Flash-mint 100 kUSD to get more kLP
        vm.expectRevert("Position unhealthy after folding");
        minter.fold(100e18, 0);

        // Try a smaller fold: 40 kUSD
        minter.fold(40e18, 0);

        (uint256 collateral, uint256 debt) = minter.positions(user);
        assertTrue(collateral > kLPAmount);
        assertEq(debt, 90e18);

        uint256 hf = minter.getHealthFactor(user);
        assertTrue(hf > 1e18);
        vm.stopPrank();
    }
}
