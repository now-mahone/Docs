// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneVault.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract SentinelDefenseTest is Test {
    KerneVault vault;
    MockERC20 asset;
    address admin = address(0x1);
    address strategist = address(0x2);
    address user = address(0x3);

    function setUp() public {
        vm.startPrank(admin);
        asset = new MockERC20("WETH", "WETH");
        
        // KerneVault constructor: (IERC20 asset_, string name_, string symbol_, address admin_, address strategist_, address exchangeDepositAddress_)
        vault = new KerneVault(
            IERC20(address(asset)),
            "Kerne WETH Vault",
            "kWETH",
            admin,
            strategist,
            address(0) // exchangeDepositAddress
        );
        
        // Grant PAUSER_ROLE to strategist (Sentinel)
        vault.grantRole(vault.PAUSER_ROLE(), strategist);
        vm.stopPrank();
    }

    function testSentinelPause() public {
        // 1. Verify vault is not paused
        assertFalse(vault.paused());

        // 2. Simulate Sentinel triggering circuit breaker
        vm.prank(strategist);
        vault.pause();

        // 3. Verify vault is paused
        assertTrue(vault.paused());

        // 4. Verify deposits are blocked
        asset.mint(user, 10 ether);
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vm.expectRevert(abi.encodeWithSignature("EnforcedPause()"));
        vault.deposit(10 ether, user);
        vm.stopPrank();
    }

    function testUnauthorizedPause() public {
        vm.prank(user);
        vm.expectRevert(); // AccessControl: account ... is missing role ...
        vault.pause();
    }
}
