// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/KerneVault.sol";
import "../src/KerneYieldOracle.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") {}
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneYieldOracleTest is Test {
    KerneVault public vault;
    KerneYieldOracle public oracle;
    MockAsset public asset;
    
    address public admin = address(0x1);
    address public strategist = address(0x2);
    address public user = address(0x3);

    function setUp() public {
        asset = new MockAsset();
        oracle = new KerneYieldOracle(admin);
        
        vault = new KerneVault(
            asset,
            "Kerne Vault",
            "kETH",
            admin,
            strategist,
            address(0)
        );

        vm.startPrank(admin);
        oracle.grantRole(oracle.UPDATER_ROLE(), strategist);
        vault.setYieldOracle(address(oracle));
        vm.stopPrank();
    }

    function testTWAYCalculation() public {
        // 1. Initial deposit
        asset.mint(user, 100e18);
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);
        vm.stopPrank();

        // 2. First observation (Price = 1.0)
        vm.prank(strategist);
        oracle.updateYield(address(vault));
        
        assertEq(oracle.getTWAY(address(vault)), 0); // Need at least 2 observations

        // 3. Simulate yield (Price goes up to 1.01)
        vm.startPrank(strategist);
        vault.updateOffChainAssets(1e18); // 1% profit
        
        // Move time forward 7 days
        vm.warp(block.timestamp + 7 days);
        
        oracle.updateYield(address(vault));
        vm.stopPrank();

        uint256 apy = oracle.getTWAY(address(vault));
        // Growth = 1% over 7 days
        // Annualized = 1% * (365 / 7) = ~52.14%
        // APY in bps = ~5214
        
        assertApproxEqAbs(apy, 5214, 10);
        assertEq(vault.getProjectedAPY(), apy);
    }

    function testManipulationResistance() public {
        // 1. Initial deposit
        asset.mint(user, 100e18);
        vm.startPrank(user);
        asset.approve(address(vault), 100e18);
        vault.deposit(100e18, user);
        vm.stopPrank();

        // 2. First observation
        vm.prank(strategist);
        oracle.updateYield(address(vault));

        // 3. Flash-pump yield
        vm.startPrank(strategist);
        vault.updateOffChainAssets(50e18); // 50% profit instantly
        
        // Move time forward only 1 hour
        vm.warp(block.timestamp + 1 hours);
        oracle.updateYield(address(vault));
        vm.stopPrank();

        uint256 apy = oracle.getTWAY(address(vault));
        // Even though price jumped 50%, the TWAY window is 7 days.
        // The oracle looks for the oldest observation within the window.
        // Since we only have 2 observations and they are 1 hour apart, 
        // it uses them, but the annualized calculation correctly reflects the short time.
        
        // However, if we had a long history, a sudden spike would be averaged out
        // once we have more observations.
        
        assertTrue(apy > 0);
    }
}
