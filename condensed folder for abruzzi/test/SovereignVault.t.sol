// SPDX-License-Identifier: MIT
// Created: 2026-02-03
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/KerneVault.sol";
import "../src/mocks/MockERC20.sol";

contract SovereignVaultTest is Test {
    KerneVault public vault;
    MockERC20 public asset;
    address public admin = address(0x1);
    address public strategist = address(0x2);
    address public hlBridge = address(0x3);
    address public user = address(0x4);

    function setUp() public {
        asset = new MockERC20("Wrapped ETH", "WETH", 18);
        vault = new KerneVault(
            IERC20(address(asset)),
            "Kerne Vault",
            "kLP",
            admin,
            strategist,
            address(0)
        );

        vm.startPrank(admin);
        vault.setL1DepositAddress(hlBridge);
        vm.stopPrank();

        asset.mint(user, 100 ether);
    }

    function testL1DepositFlow() public {
        // 1. User deposits to vault
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vault.deposit(10 ether, user);
        vm.stopPrank();

        assertEq(vault.totalAssets(), 10 ether);

        // 2. Admin requests L1 deposit (moves funds to HL bridge)
        vm.startPrank(admin);
        vault.requestL1Deposit(9 ether);
        vm.stopPrank();

        assertEq(asset.balanceOf(hlBridge), 9 ether);
        assertEq(asset.balanceOf(address(vault)), 1 ether);
        
        // totalAssets should still be 10 ether (1 on-chain + 9 off-chain/L1)
        // But wait, we haven't updated l1Assets yet.
        // totalAssets() = super.totalAssets() + offChainAssets + l1Assets + hedgingReserve
        // super.totalAssets() is the balance of the vault contract.
        assertEq(vault.totalAssets(), 1 ether); // Correct, because l1Assets is 0

        // 3. Strategist updates L1 assets (simulating bot sync)
        vm.startPrank(strategist);
        vault.updateL1Assets(9.1 ether); // Simulating some yield/PnL on HL
        vm.stopPrank();

        assertEq(vault.l1Assets(), 9.1 ether);
        assertEq(vault.totalAssets(), 10.1 ether); // 1 on-chain + 9.1 L1
    }

    function testUnauthorizedL1Update() public {
        vm.startPrank(user);
        vm.expectRevert();
        vault.updateL1Assets(10 ether);
        vm.stopPrank();
    }
}