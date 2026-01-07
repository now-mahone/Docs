// Created: 2026-01-04
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../src/KerneVaultFactory.sol";
import "../src/KerneVault.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock", "MCK") { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneVaultFactoryTest is Test {
    KerneVaultFactory public factory;
    KerneVault public implementation;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public founder = address(0x2);
    address public partner = address(0x3);

    function setUp() public {
        asset = new MockERC20();
        implementation = new KerneVault(asset, "Implementation", "IMP", admin, admin, admin);
        factory = new KerneVaultFactory(address(implementation));
    }

    function testDeployVault() public {
        vm.startPrank(factory.owner());
        address vaultAddr =
            factory.deployVault(address(asset), "Partner Vault", "PVT", partner, founder, 500, 1500, true);
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);
        assertEq(vault.name(), "Partner Vault");
        assertEq(vault.symbol(), "PVT");
        assertEq(vault.founder(), founder);
        assertEq(vault.founderFeeBps(), 500);
        assertTrue(vault.hasRole(vault.DEFAULT_ADMIN_ROLE(), partner));
    }

    function testDeployVaultNonOwner() public {
        vm.prank(partner);
        vm.expectRevert(abi.encodeWithSignature("OwnableUnauthorizedAccount(address)", partner));
        factory.deployVault(address(asset), "Partner Vault", "PVT", partner, founder, 500, 1500, true);
    }
}
