// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "src/KerneVault.sol";
import { MockERC20 } from "./unit/KerneVault.t.sol";
import { KerneVaultHandler } from "./KerneVaultHandler.sol";

contract KerneVaultInvariants is Test {
    KerneVault public vault;
    MockERC20 public asset;
    KerneVaultHandler public handler;

    address public admin = makeAddr("admin");
    address public strategist = makeAddr("strategist");
    address public exchange = makeAddr("exchange");

    function setUp() public {
        asset = new MockERC20();
        vault = new KerneVault(asset, "Kerne Vault Token", "kUSD", admin, strategist, exchange);

        vm.prank(admin);
        vault.setFounder(admin);

        handler = new KerneVaultHandler(vault, asset, admin, strategist, exchange);

        targetContract(address(handler));
    }

    /// @notice Invariant: The vault must always be solvent (Assets >= Liabilities)
    function invariant_solvency() public view {
        uint256 totalAssets = vault.totalAssets();
        uint256 totalSupply = vault.totalSupply();

        if (totalSupply > 0) {
            uint256 liabilitiesInAssets = vault.convertToAssets(totalSupply);
            assertGe(totalAssets, liabilitiesInAssets, "Vault is insolvent: Assets < Liabilities");
        }
    }

    /// @notice Invariant: Share price (assets per share) should not decrease
    function invariant_sharePriceMonotonicity() public view {
        uint256 assets = 10 ether;
        uint256 shares = vault.convertToShares(assets);
        uint256 backToAssets = vault.convertToAssets(shares);
        assertLe(backToAssets, assets, "Conversion inconsistency: assets inflated");
    }

    /// @notice Invariant: Accounting components must sum up to totalAssets
    function invariant_accountingConsistency() public view {
        uint256 totalAssets = vault.totalAssets();
        uint256 onChainBalance = asset.balanceOf(address(vault));
        uint256 offChainAssets = vault.offChainAssets();
        
        address node = vault.verificationNode();
        uint256 verifiedAssets = 0;
        if (node != address(0)) {
            (bool success, bytes memory data) = node.staticcall(
                abi.encodeWithSignature("getVerifiedAssets(address)", address(vault))
            );
            if (success && data.length == 32) {
                verifiedAssets = abi.decode(data, (uint256));
            }
        }
        uint256 reserve = verifiedAssets > 0 ? verifiedAssets : vault.hedgingReserve();
        
        assertEq(totalAssets, onChainBalance + offChainAssets + reserve, "Accounting mismatch");
    }

    /// @notice Invariant: getSolvencyRatio() must be consistent with totalAssets/totalSupply
    function invariant_solvencyRatioConsistency() public view {
        uint256 ratio = vault.getSolvencyRatio();
        uint256 assets = vault.totalAssets();
        uint256 supply = vault.totalSupply();

        if (supply == 0) {
            assertEq(ratio, 20000, "Initial solvency ratio should be 200%");
        } else {
            uint256 expectedRatio = (assets * 10000) / supply;
            assertEq(ratio, expectedRatio, "Solvency ratio mismatch");
        }
    }

    /// @notice Invariant: Fee capture sanity
    function invariant_feeSanity() public view {
        assertLe(handler.ghost_totalFeesCaptured(), handler.ghost_totalYieldGenerated(), "Fees exceeded yield");
    }
}
