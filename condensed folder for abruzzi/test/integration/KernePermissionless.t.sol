// SPDX-License-Identifier: MIT
// Created: 2026-01-09
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneVaultFactory.sol";
import "src/KerneVault.sol";
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
        factory = new KerneVaultFactory(address(implementation), address(0));
        vm.stopPrank();
    }

    function testPermissionlessDeployment() public {
        vm.deal(partner, 1 ether);
        vm.startPrank(partner);

        // TierConfig has 5 fields: deploymentFee, protocolFounderFeeBps, complianceRequired, complianceHook, maxTotalAssets
        (uint256 fee, , , , ) = factory.tierConfigs(KerneVaultFactory.VaultTier.BASIC);

        address vaultAddr = factory.deployVault{ value: fee }(
            address(asset), "Partner Vault", "PVT", partner, 1500, false, KerneVaultFactory.VaultTier.BASIC
        );

        assertTrue(vaultAddr != address(0));
        KerneVault vault = KerneVault(vaultAddr);
        assertEq(vault.name(), "Partner Vault");
        assertEq(vault.symbol(), "PVT");
        assertEq(vault.founder(), owner);
        
        // vaultsByDeployer is a mapping, access via index
        address partnerVault = factory.vaultsByDeployer(partner, 0);
        assertEq(partnerVault, vaultAddr);
        
        vm.stopPrank();
    }

    function testInsufficientFee() public {
        vm.deal(partner, 1 ether);
        vm.startPrank(partner);

        vm.expectRevert("Insufficient deployment fee");
        factory.deployVault{ value: 0.01 ether }(
            address(asset), "Fail Vault", "FAIL", partner, 1500, false, KerneVaultFactory.VaultTier.BASIC
        );
        vm.stopPrank();
    }
}
