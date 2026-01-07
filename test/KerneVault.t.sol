// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock WETH", "WETH") { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneVaultTest is Test {
    KerneVault public vault;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public bot = address(0x2);
    address public user = address(0x3);
    address public exchange = makeAddr("exchange");

    function setUp() public {
        asset = new MockERC20();
        vault = new KerneVault(asset, "Kerne Vault Token", "kUSD", admin, bot, exchange);

        vm.prank(admin);
        vault.setFounder(admin);

        asset.mint(user, 100 ether);

        vm.label(admin, "Admin");
        vm.label(bot, "Bot");
        vm.label(user, "User");
        vm.label(exchange, "Exchange");
    }

    function testYieldAccrual() public {
        // 1. Deposit
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vault.deposit(10 ether, user);
        vm.stopPrank();

        // Account for 1000 dead shares minted to admin on first deposit
        uint256 userShares = vault.balanceOf(user);
        assertGt(userShares, 0);
        // totalAssets should be 10 ether
        assertEq(vault.totalAssets(), 10 ether);

        // 2. Sweep
        vm.startPrank(admin);
        vault.setTreasury(exchange); // Set treasury to exchange to match test expectations
        vault.sweepToExchange(5 ether);
        vm.stopPrank();

        assertEq(asset.balanceOf(address(vault)), 5 ether);
        // Since exchangeDepositAddress is set in constructor, it should be used
        assertEq(asset.balanceOf(exchange), 5 ether);

        // 3. Profit
        vm.prank(bot);
        vault.updateOffChainAssets(5.5 ether);
        // totalAssets = on-chain (5 ether) + off-chain (5.5 ether) = 10.5 ether
        assertEq(vault.totalAssets(), 10.5 ether);

        // 4. Withdraw (Should fail due to buffer)
        vm.startPrank(user);
        vm.expectRevert("Insufficient liquid buffer");
        vault.withdraw(10.5 ether, user, user);
        vm.stopPrank();

        // 5. Return funds AND update off-chain assets to 0
        asset.mint(address(vault), 5.5 ether); // Simulate return from CEX
        vm.prank(bot);
        vault.updateOffChainAssets(0);

        // 6. Withdraw all
        vm.startPrank(user);
        vault.redeem(userShares, user, user);
        vm.stopPrank();

        // User should get their proportional share of 10.5 ether
        // userShares / (userShares + 1000) * 10.5 ether
        // Since userShares is huge, it's almost exactly 10.5 ether
        assertApproxEqAbs(asset.balanceOf(user), 90 ether + 10.5 ether, 1e10);
    }

    function testInsufficientBuffer() public {
        // 1. Deposit
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vault.deposit(10 ether, user);
        vm.stopPrank();

        // 2. Sweep
        vm.startPrank(admin);
        vault.setTreasury(exchange);
        vault.sweepToExchange(9 ether);
        vm.stopPrank();

        // 3. Withdraw 5 ether (only 1 ether left)
        vm.startPrank(user);
        vm.expectRevert("Insufficient liquid buffer");
        vault.withdraw(5 ether, user, user);
        vm.stopPrank();
    }

    function testUnauthorizedAccess() public {
        // 1. Hack updateOffChainAssets
        vm.startPrank(user);
        vm.expectRevert(); // AccessControlUnauthorizedAccount
        vault.updateOffChainAssets(100 ether);

        // 2. Hack sweepToExchange
        vm.expectRevert(); // AccessControlUnauthorizedAccount
        vault.sweepToExchange(10 ether);
        vm.stopPrank();
    }
}
