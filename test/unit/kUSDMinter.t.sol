// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test } from "forge-std/Test.sol";
import { KerneVault } from "../../src/KerneVault.sol";
import { kUSD } from "../../src/kUSD.sol";
import { kUSDMinter } from "../../src/kUSDMinter.sol";
import { MockERC20 } from "../../src/mocks/MockERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockYieldOracle {
    uint256 public apy;
    function setAPY(uint256 _apy) external { apy = _apy; }
    function getTWAY(address) external view returns (uint256) { return apy; }
}

contract kUSDMinterTest is Test {
    MockERC20 internal asset;
    KerneVault internal vault;
    kUSD internal kusd;
    kUSDMinter internal minter;
    MockYieldOracle internal oracle;

    address internal admin = address(0xA11CE);
    address internal strategist = address(0xB0B);
    address internal user = address(0xCAFE);
    MockAggregator internal mockAggregator;

    function setUp() public {
        asset = new MockERC20("Mock WETH", "WETH", 18);
        vault = new KerneVault(asset, "Kerne Vault", "kLP", admin, strategist, address(0xDEAD));
        kusd = new kUSD(admin);
        oracle = new MockYieldOracle();
        mockAggregator = new MockAggregator(address(asset));

        minter = new kUSDMinter(address(kusd), address(vault), admin);

        vm.startPrank(admin);
        kusd.grantRole(kusd.MINTER_ROLE(), address(minter));
        minter.setDexAggregator(address(mockAggregator));
        minter.setYieldOracle(address(oracle));
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

    function testFoldToTargetAPY() public {
        // Setup: Base APY 5% (500 bps), Target 10% (1000 bps)
        // Leverage = 2x
        // Collateral = 10 ETH
        // Debt = 10 ETH (approx)
        
        oracle.setAPY(500); // 5%

        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        uint256 shares = vault.deposit(10 ether, user);
        IERC20(address(vault)).approve(address(minter), shares);
        
        // Initial deposit into minter (0 debt)
        minter.mint(shares, 0); // Just deposit collateral
        
        // Execute Fold
        // Target 10% APY
        minter.foldToTargetAPY(1000, 0);
        
        (uint256 collateral, uint256 debt) = minter.positions(user);
        
        // Expected Debt:
        // Collateral Value = 10 ETH (since 1 share = 1 asset initially)
        // Debt = (1000 - 500) * 10 / 500 = 10 ETH
        assertEq(debt, 10 ether);
        
        // Expected Collateral:
        // Initial 10 + 10 (borrowed & swapped & deposited) = 20 ETH assets
        // But vault has 3 decimals offset, so 20 ETH assets = 20,000 ETH shares
        assertEq(collateral, 20000 ether);
        
        vm.stopPrank();
    }
}

contract MockAggregator {
    IERC20 asset;
    constructor(address _asset) { asset = IERC20(_asset); }
    
    function swap(address from, address to, uint256 amount, uint256) external returns (uint256) {
        // Burn input (simulated) or just ignore
        // Mint output to caller
        MockERC20(address(asset)).mint(msg.sender, amount);
        return amount;
    }
}
