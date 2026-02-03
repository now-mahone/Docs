// Created: 2026-01-31
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../../src/KerneVault.sol";
import "../../src/KerneVaultFactory.sol";
import "../../src/KerneComplianceHook.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockAsset is ERC20 {
    constructor() ERC20("Mock Asset", "MOCK") {
        _mint(msg.sender, 1000000 * 1e18);
    }
}

contract KerneComplianceTest is Test {
    KerneVaultFactory factory;
    KerneComplianceHook hook;
    KerneVault implementation;
    MockAsset asset;

    address admin = address(0x1);
    address strategist = address(0x2);
    address compliantUser = address(0x3);
    address nonCompliantUser = address(0x4);
    address exchange = address(0x5);

    function setUp() public {
        asset = new MockAsset();
        implementation = new KerneVault(asset, "Impl", "IMPL", admin, strategist, exchange);
        
        vm.startPrank(admin);
        factory = new KerneVaultFactory(address(implementation), address(0));
        hook = new KerneComplianceHook(admin);

        // Configure INSTITUTIONAL tier with compliance hook
        factory.setTierConfig(
            KerneVaultFactory.VaultTier.INSTITUTIONAL,
            1 ether,
            500,
            true, // complianceRequired
            address(hook),
            10000 ether
        );
        vm.stopPrank();
    }

    function testInstitutionalComplianceGating() public {
        // 1. Deploy Institutional Vault
        vm.deal(admin, 10 ether);
        vm.startPrank(admin);
        address vaultAddr = factory.deployVault{value: 1 ether}(
            address(asset),
            "Institutional Vault",
            "iVault",
            admin,
            1000, // 10% performance fee
            false, // whitelistEnabled (tier will override to true)
            KerneVaultFactory.VaultTier.INSTITUTIONAL
        );
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);
        assertTrue(vault.whitelistEnabled(), "Whitelist should be enabled by tier");
        assertEq(address(vault.complianceHook()), address(hook), "Hook should be set by tier");

        // Enable strict compliance for this vault
        vm.startPrank(admin);
        hook.setStrictCompliance(address(vault), true);
        vm.stopPrank();

        // 2. Non-compliant user tries to deposit
        uint256 amount = 100 * 1e18;
        asset.transfer(nonCompliantUser, amount);
        
        vm.startPrank(nonCompliantUser);
        asset.approve(address(vault), amount);
        vm.expectRevert("Not whitelisted or compliant");
        vault.deposit(amount, nonCompliantUser);
        vm.stopPrank();

        // 3. Make user compliant (Vault-specific)
        vm.startPrank(admin);
        hook.setComplianceStatus(address(vault), compliantUser, true);
        vm.stopPrank();

        // 4. Compliant user deposits
        asset.transfer(compliantUser, amount);
        vm.startPrank(compliantUser);
        asset.approve(address(vault), amount);
        vault.deposit(amount, compliantUser);
        assertEq(vault.balanceOf(compliantUser), amount * 1000, "Deposit should succeed (with offset)");
        vm.stopPrank();
    }

    function testGlobalCompliance() public {
        // 1. Deploy Institutional Vault
        vm.deal(admin, 10 ether);
        vm.startPrank(admin);
        address vaultAddr = factory.deployVault{value: 1 ether}(
            address(asset),
            "Institutional Vault",
            "iVault",
            admin,
            1000,
            false,
            KerneVaultFactory.VaultTier.INSTITUTIONAL
        );
        
        // Set strict compliance on hook for this vault
        hook.setStrictCompliance(vaultAddr, true);
        
        // Set global compliance for user
        hook.setGlobalCompliance(compliantUser, true);
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);

        // 2. User with global compliance deposits
        uint256 amount = 100 * 1e18;
        asset.transfer(compliantUser, amount);
        vm.startPrank(compliantUser);
        asset.approve(address(vault), amount);
        vault.deposit(amount, compliantUser);
        assertTrue(vault.balanceOf(compliantUser) > 0);
        vm.stopPrank();
    }

    function testComplianceOverride() public {
        // 1. Deploy Basic Vault (No compliance)
        vm.deal(admin, 10 ether);
        vm.startPrank(admin);
        address vaultAddr = factory.deployVault{value: 0.05 ether}(
            address(asset),
            "Basic Vault",
            "bVault",
            admin,
            1000,
            false,
            KerneVaultFactory.VaultTier.BASIC
        );
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);
        assertFalse(vault.whitelistEnabled());

        // 2. Any user can deposit
        uint256 amount = 100 * 1e18;
        asset.transfer(nonCompliantUser, amount);
        vm.startPrank(nonCompliantUser);
        asset.approve(address(vault), amount);
        vault.deposit(amount, nonCompliantUser);
        assertTrue(vault.balanceOf(nonCompliantUser) > 0);
        vm.stopPrank();
    }
}