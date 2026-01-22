// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test } from "forge-std/Test.sol";
import { KerneVault } from "../../src/KerneVault.sol";
import { kUSD } from "../../src/kUSD.sol";
import { kUSDMinter } from "../../src/kUSDMinter.sol";
import { MockERC20 } from "../../src/mocks/MockERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract kUSDMinterTest is Test {
    MockERC20 internal asset;
    KerneVault internal vault;
    kUSD internal kusd;
    kUSDMinter internal minter;

    address internal admin = address(0xA11CE);
    address internal strategist = address(0xB0B);
    address internal user = address(0xCAFE);
    address internal aggregator = address(0xF00D);

    function setUp() public {
        asset = new MockERC20("Mock WETH", "WETH", 18);
        vault = new KerneVault(asset, "Kerne Vault", "kLP", admin, strategist, address(0xDEAD));
        kusd = new kUSD(admin);

        minter = new kUSDMinter(address(kusd), address(vault), admin);

        vm.startPrank(admin);
        kusd.grantRole(kusd.MINTER_ROLE(), address(minter));
        minter.setDexAggregator(aggregator);
        vm.stopPrank();

        asset.mint(user, 100 ether);
    }

    function testMintAndBurn() public {
        vm.startPrank(user);
        asset.approve(address(vault), 20 ether);
        uint256 shares = vault.deposit(20 ether, user);

        IERC20(address(vault)).approve(address(minter), shares);
        minter.mint(shares, 10 ether);

        assertEq(kusd.balanceOf(user), 10 ether);

        kusd.approve(address(minter), 10 ether);
        minter.burn(10 ether, shares);
        vm.stopPrank();

        assertEq(kusd.balanceOf(user), 0);
    }
}
