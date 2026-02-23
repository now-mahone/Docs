// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../../src/KerneInsuranceFund.sol";
import "../../src/mocks/MockERC20.sol";

contract MockVault is IKerneVault {
    uint256 public solvencyRatio;
    uint256 public totalLiabilities;
    uint256 public totalAssetsAmount;

    function setSolvencyRatio(uint256 _ratio) external {
        solvencyRatio = _ratio;
    }

    function setTotalSupply(uint256 _supply) external {
        totalLiabilities = _supply;
    }

    function setTotalAssets(uint256 _assets) external {
        totalAssetsAmount = _assets;
    }

    function getSolvencyRatio() external view override returns (uint256) {
        return solvencyRatio;
    }

    function totalSupply() external view override returns (uint256) {
        return totalLiabilities;
    }

    function totalAssets() external view override returns (uint256) {
        return totalAssetsAmount;
    }

    function offChainAssets() external view override returns (uint256) {
        return 0;
    }

    function hedgingReserve() external view override returns (uint256) {
        return 0;
    }

    function trustAnchor() external view override returns (address) {
        return address(0);
    }

    function verificationNode() external view override returns (address) {
        return address(0);
    }

    function pause() external override {}
}

contract KerneInsuranceFundTest is Test {
    KerneInsuranceFund public insuranceFund;
    MockERC20 public asset;
    MockVault public vault;
    address public admin = address(1);
    address public manager = address(2);

    function setUp() public {
        asset = new MockERC20("Mock Asset", "MOCK", 18);
        
        vm.startPrank(admin);
        insuranceFund = new KerneInsuranceFund(address(asset), admin);
        insuranceFund.grantRole(insuranceFund.MANAGER_ROLE(), manager);
        vm.stopPrank();

        vault = new MockVault();
        
        vm.startPrank(manager);
        insuranceFund.setAuthorization(address(vault), true);
        vm.stopPrank();

        // Fund the insurance fund
        asset.mint(address(this), 1000000 ether);
        asset.approve(address(insuranceFund), 1000000 ether);
        insuranceFund.deposit(1000000 ether);
    }

    function testCheckAndInject_AboveThreshold() public {
        // Set vault state above threshold (1.35x)
        vault.setSolvencyRatio(13500);
        vault.setTotalSupply(1000 ether);
        vault.setTotalAssets(1350 ether);

        uint256 initialVaultBalance = asset.balanceOf(address(vault));
        uint256 initialFundBalance = asset.balanceOf(address(insuranceFund));

        insuranceFund.checkAndInject(address(vault));

        assertEq(asset.balanceOf(address(vault)), initialVaultBalance);
        assertEq(asset.balanceOf(address(insuranceFund)), initialFundBalance);
    }

    function testCheckAndInject_BelowThreshold() public {
        // Set vault state below threshold (1.25x)
        vault.setSolvencyRatio(12500);
        vault.setTotalSupply(1000 ether);
        vault.setTotalAssets(1250 ether);

        uint256 initialVaultBalance = asset.balanceOf(address(vault));
        uint256 initialFundBalance = asset.balanceOf(address(insuranceFund));

        // Target assets for 1.30x = 1000 * 13000 / 10000 = 1300 ether
        // Deficit = 1300 - 1250 = 50 ether
        uint256 expectedInjection = 50 ether;

        insuranceFund.checkAndInject(address(vault));

        assertEq(asset.balanceOf(address(vault)), initialVaultBalance + expectedInjection);
        assertEq(asset.balanceOf(address(insuranceFund)), initialFundBalance - expectedInjection);
    }

    function testCheckAndInject_InsufficientFundBalance() public {
        // Drain insurance fund to 10 ether
        vm.warp(block.timestamp + 2 hours);
        vm.startPrank(admin);
        insuranceFund.setMaxClaimPercentage(10000);
        insuranceFund.claim(address(this), 999990 ether);
        vm.stopPrank();

        // Set vault state below threshold (1.25x)
        vault.setSolvencyRatio(12500);
        vault.setTotalSupply(1000 ether);
        vault.setTotalAssets(1250 ether);

        uint256 initialVaultBalance = asset.balanceOf(address(vault));
        uint256 initialFundBalance = asset.balanceOf(address(insuranceFund));

        // Target assets for 1.30x = 1000 * 13000 / 10000 = 1300 ether
        // Deficit = 1300 - 1250 = 50 ether
        // But fund only has 10 ether
        uint256 expectedInjection = 10 ether;

        insuranceFund.checkAndInject(address(vault));

        assertEq(asset.balanceOf(address(vault)), initialVaultBalance + expectedInjection);
        assertEq(asset.balanceOf(address(insuranceFund)), initialFundBalance - expectedInjection);
    }

    function testCheckAndInject_UnauthorizedVault() public {
        MockVault unauthorizedVault = new MockVault();
        
        vm.expectRevert("Vault not authorized");
        insuranceFund.checkAndInject(address(unauthorizedVault));
    }
}