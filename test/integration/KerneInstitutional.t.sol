// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneVault.sol";
import "src/KerneVaultFactory.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock", "MCK") { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneInstitutionalTest is Test {
    KerneVault public implementation;
    KerneVaultFactory public factory;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public strategist = address(0x2);
    address public founder = address(0x3);
    address public user = address(0x4);
    address public exchange = address(0x5);

    function setUp() public {
        asset = new MockERC20();
        implementation = new KerneVault(asset, "Impl", "IMPL", admin, strategist, exchange);
        factory = new KerneVaultFactory(address(implementation), address(0));
    }

    function testBespokeVaultDeployment() public {
        vm.startPrank(factory.owner());
        address vaultAddr = factory.deployVault(
            address(asset),
            "Institutional Vault",
            "kINST",
            admin,
            1500, // 15% performance fee
            true, // whitelist enabled
            KerneVaultFactory.VaultTier.INSTITUTIONAL
        );
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);
        assertEq(vault.name(), "Institutional Vault");
        assertEq(vault.symbol(), "kINST");
        assertEq(vault.founder(), factory.owner());
        assertEq(vault.founderFeeBps(), 500); // From TierConfig
    }

    function testWhitelisting() public {
        vm.startPrank(factory.owner());
        address vaultAddr = factory.deployVault(
            address(asset),
            "Whitelisted Vault",
            "kWL",
            admin,
            1500,
            true,
            KerneVaultFactory.VaultTier.INSTITUTIONAL
        );
        vm.stopPrank();

        KerneVault vault = KerneVault(vaultAddr);

        // Enable whitelist
        vm.prank(admin);
        vault.setWhitelistEnabled(true);

        asset.mint(user, 1000 ether);
        vm.startPrank(user);
        asset.approve(address(vault), 1000 ether);

        // Should fail
        vm.expectRevert("Not whitelisted or compliant");
        vault.deposit(100 ether, user);
        vm.stopPrank();

        // Whitelist user
        vm.prank(admin);
        vault.setWhitelisted(user, true);

        // Should succeed
        vm.prank(user);
        vault.deposit(100 ether, user);

        // Note: KerneVault mints 1000 dead shares to admin on first deposit/init
        // So we check the balance relative to that or just check that it's > 0
        assertGt(vault.balanceOf(user), 0);
    }
}
