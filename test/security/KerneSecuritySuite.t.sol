// Created: 2026-01-07
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "src/KerneVault.sol";
import "src/KernePrime.sol";
import "src/KerneInsuranceFund.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") {
        _mint(msg.sender, 1000000 * 1e18);
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
        insurance = new KerneInsuranceFund(address(asset));

        prime.transferOwnership(admin);
        insurance.transferOwnership(admin);

        vm.startPrank(admin);
        vault.setInsuranceFund(address(insurance));
        insurance.setAuthorization(address(vault), true);
        vm.stopPrank();
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
        asset.transfer(address(insurance), amount);

        vm.startPrank(strategist);
        vault.drawFromInsuranceFund(amount);
        vm.stopPrank();

        assertEq(asset.balanceOf(address(vault)), amount);
    }
}
