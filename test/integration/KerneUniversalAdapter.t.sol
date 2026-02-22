// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneUniversalAdapter } from "src/KerneUniversalAdapter.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";

contract MockERC20 is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract MockVault is ERC4626 {
    constructor(IERC20 asset) ERC4626(asset) ERC20("Mock Vault", "mv") { }
}

contract KerneUniversalAdapterTest is Test {
    KerneUniversalAdapter public adapter;
    MockVault public targetVault;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public bot = address(0x2);
    address public user = address(0x3);
    address public exchange = makeAddr("exchange");

    function setUp() public {
        asset = new MockERC20("Mock USDC", "USDC");
        targetVault = new MockVault(asset);
        adapter = new KerneUniversalAdapter(
            asset,
            targetVault,
            "Kerne Adapter Token",
            "kAT",
            admin,
            bot
        );

        asset.mint(user, 1000 ether);

        vm.label(admin, "Admin");
        vm.label(bot, "Bot");
        vm.label(user, "User");
        vm.label(exchange, "Exchange");
    }

    function testDepositAndWithdraw() public {
        // 1. Deposit into adapter
        vm.startPrank(user);
        asset.approve(address(adapter), 100 ether);
        adapter.deposit(100 ether, user);
        vm.stopPrank();

        // Adapter should have minted shares to user
        assertEq(adapter.balanceOf(user), 100 ether);
        // Target vault should have minted shares to adapter
        assertEq(targetVault.balanceOf(address(adapter)), 100 ether);
        // Total assets should be 100 ether
        assertEq(adapter.totalAssets(), 100 ether);

        // 2. Withdraw from adapter
        vm.startPrank(user);
        adapter.withdraw(50 ether, user, user);
        vm.stopPrank();

        assertEq(adapter.balanceOf(user), 50 ether);
        assertEq(asset.balanceOf(user), 900 ether + 50 ether);
        assertEq(targetVault.balanceOf(address(adapter)), 50 ether);
    }

    function testOffChainYield() public {
        // 1. Deposit
        vm.startPrank(user);
        asset.approve(address(adapter), 100 ether);
        adapter.deposit(100 ether, user);
        vm.stopPrank();

        // 2. Update off-chain assets (simulating profit from hedging)
        vm.prank(bot);
        adapter.updateOffChainAssets(10 ether);

        // totalAssets = 100 (in target vault) + 10 (off-chain) = 110 ether
        // Use approx eq due to potential rounding in convertToAssets
        assertApproxEqAbs(adapter.totalAssets(), 110 ether, 1);

        // 3. Check share price increase
        // 100 shares represent 110 assets
        assertApproxEqAbs(adapter.convertToAssets(100 ether), 110 ether, 1);
    }

    function testHarvest() public {
        // 1. Deposit
        vm.startPrank(user);
        asset.approve(address(adapter), 100 ether);
        adapter.deposit(100 ether, user);
        vm.stopPrank();

        // 2. Harvest (should not revert even without integrations set)
        vm.prank(bot);
        adapter.harvest("");
        
        // Verify state is unchanged after harvest with no integrations
        assertEq(adapter.totalAssets(), 100 ether);
    }
}
