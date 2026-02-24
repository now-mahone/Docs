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
        vm.warp(1000); // Advance past offChainUpdateCooldown (10 min = 600s)
        asset = new MockERC20();
        vault = new KerneVault(asset, "Kerne Vault Token", "kUSD", admin, bot, exchange);

        vm.startPrank(admin);
        vault.setFounder(admin);
        vault.setOffChainUpdateParams(0, 5 minutes); // Disable rate limit for unit tests (0 = no limit)
        vm.stopPrank();

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

        // CR = 10.5 / ~9.995 ≈ 1.050x which is below CRITICAL_CR_THRESHOLD (1.25x).
        // The circuit breaker fires and pauses the vault — this is correct protocol behavior.
        // For the test to proceed (checking withdrawal queue logic), admin force-recovers.
        vm.prank(admin);
        vault.forceRecoverCRCircuitBreaker();

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

        // 5. Return funds: CEX sends tokens back via returnFromPrime, which properly
        //    increments _trackedOnChainAssets (unlike a direct mint/send which is a donation).
        asset.mint(bot, 5.5 ether); // Mint tokens to bot (representing CEX return)
        vm.startPrank(bot);
        asset.approve(address(vault), 5.5 ether);
        vault.returnFromPrime(5.5 ether); // Updates _trackedOnChainAssets += 5.5 ether
        vm.stopPrank();

        // Update off-chain assets to 0 after CEX return
        vm.warp(block.timestamp + 5 minutes + 1); // Advance past offChainUpdateCooldown
        vm.prank(bot);
        vault.updateOffChainAssets(0);

        // CR drops below CRITICAL (tracked on-chain = 10.5 ether, liabilities ~= 9.995 ether)
        // Force-recover so claimWithdrawal can execute
        if (vault.crCircuitBreakerActive()) {
            vm.prank(admin);
            vault.forceRecoverCRCircuitBreaker();
        }

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

        // CR = (5+95) / ~99.95 ≈ 1.0005x < CRITICAL (1.25x) → circuit breaker fires.
        // Force-recover so requestWithdrawal (whenNotPaused) can proceed.
        vm.prank(admin);
        vault.forceRecoverCRCircuitBreaker();

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
