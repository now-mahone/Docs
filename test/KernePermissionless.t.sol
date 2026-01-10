// SPDX-License-Identifier: MIT
// Created: 2026-01-09
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../src/KerneVaultFactory.sol";
import "../src/KerneVault.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") {
        _mint(msg.sender, 1000000e18);
    }
}

contract KernePermissionlessTest is Test {
    KerneVaultFactory factory;
    KerneVault implementation;
    MockAsset asset;
    address owner = address(0x1);
    address partner = address(0x2);
    address user = address(0x3);

    function setUp() public {
        vm.startPrank(owner);
        asset = new MockAsset();
        implementation = new KerneVault(
            IERC20(address(0)),
            "",
            "",
            address(this),
            address(this),
            address(0)
        );
        factory = new KerneVaultFactory(address(implementation));
        vm.stopPrank();
    }

    function testPermissionlessDeployment() public {
        vm.deal(partner, 1 ether);
        vm.startPrank(partner);
        
        uint256 fee = factory.deploymentFee();
        
        address vaultAddr = factory.deployVault{value: fee}(
            address(asset),
            "Partner Vault",
            "PVT",
            partner,
            owner,
            500,
            1500,
            false,
            0
        );

        assertTrue(vaultAddr != address(0));
        KerneVault vault = KerneVault(vaultAddr);
        assertEq(vault.name(), "Partner Vault");
        assertEq(vault.symbol(), "PVT");
        assertEq(vault.founder(), owner);
        
        address[] memory partnerVaults = factory.getUserVaults(partner);
        assertEq(partnerVaults.length, 1);
        assertEq(partnerVaults[0], vaultAddr);
        
        vm.stopPrank();
    }

    function testInsufficientFee() public {
        vm.deal(partner, 1 ether);
        vm.startPrank(partner);
        
        vm.expectRevert("Insufficient deployment fee");
        factory.deployVault{value: 0.01 ether}(
            address(asset),
            "Fail Vault",
            "FAIL",
            partner,
            owner,
            500,
            1500,
            false,
            0
        );
        vm.stopPrank();
    }
}
