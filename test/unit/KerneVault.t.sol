// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "src/KerneVault.sol";
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

        asset.mint(user, 1_000_000 ether);

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

        // Account for 1000 dead shares (10^3) due to _decimalsOffset
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

        // 4. Request Withdrawal (Should fail due to buffer when claiming)
        vm.startPrank(user);
        // We can only request what we have. userShares corresponds to ~10 ether.
        // Since it's the only user, they own almost all assets.
        uint256 assetsToWithdraw = vault.convertToAssets(userShares);
        uint256 requestId = vault.requestWithdrawal(assetsToWithdraw);
        
        vm.warp(block.timestamp + 7 days);
        vm.expectRevert("Insufficient liquid buffer");
        vault.claimWithdrawal(requestId);
        vm.stopPrank();

        // 5. Return funds AND update off-chain assets to 0
        asset.mint(address(vault), 5.5 ether); // Simulate return from CEX
        vm.prank(bot);
        vault.updateOffChainAssets(0);

        // 6. Claim Withdrawal
        vm.startPrank(user);
        vault.claimWithdrawal(requestId);
        vm.stopPrank();

        // User should get their assets back
        assertApproxEqAbs(asset.balanceOf(user), 1_000_000 ether - 10 ether + assetsToWithdraw, 1e10);
    }

    function testInsufficientBuffer() public {
        // 1. Deposit
        vm.startPrank(user);
        asset.approve(address(vault), 100 ether);
        vault.deposit(100 ether, user);
        vm.stopPrank();

        // 2. Sweep
        vm.startPrank(admin);
        vault.setTreasury(exchange);
        vault.sweepToExchange(95 ether); // Leave 5 ether
        vm.stopPrank();

        // Update off-chain assets to keep totalAssets consistent
        vm.prank(bot);
        vault.updateOffChainAssets(95 ether);

        // 3. Request Withdrawal 10 ether (only 5 ether left)
        vm.startPrank(user);
        uint256 requestId = vault.requestWithdrawal(10 ether);
        vm.warp(block.timestamp + 7 days);
        vm.expectRevert("Insufficient liquid buffer");
        vault.claimWithdrawal(requestId);
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
