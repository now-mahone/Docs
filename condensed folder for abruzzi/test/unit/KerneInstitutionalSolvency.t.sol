// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "src/KerneVault.sol";
import { KerneVerificationNode } from "src/KerneVerificationNode.sol";
import { KerneTrustAnchor } from "src/KerneTrustAnchor.sol";
import { MockERC20 } from "./KerneSolvencyHardening.t.sol";

contract KerneInstitutionalSolvencyTest is Test {
    KerneVault public vault;
    KerneVerificationNode public node;
    KerneTrustAnchor public anchor;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public auditor = address(0x2);
    address public user = address(0x3);

    function setUp() public {
        asset = new MockERC20();
        
        address lzEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
        vm.etch(lzEndpoint, hex"00");

        vault = new KerneVault(asset, "KUSD Vault", "kUSD", admin, admin, address(0x4));
        node = new KerneVerificationNode(lzEndpoint, admin);
        anchor = new KerneTrustAnchor(admin);

        vm.startPrank(admin);
        anchor.setVerificationNode(address(vault), address(node));
        vault.setTrustAnchor(address(anchor));
        vault.setVerificationNode(address(node));
        vault.setFounder(admin);
        
        // Stabilize vault with initial reserve before first deposit
        vault.updateHedgingReserve(1 ether);
        
        // Grant Auditor Role
        anchor.grantRole(anchor.AUDITOR_ROLE(), auditor);
        
        // Submit initial pulse to satisfy freshness check
        vm.startPrank(auditor);
        anchor.submitAuditorPulse(address(vault));
        vm.stopPrank();
        
        // Grant Pauser Role to Anchor so it can pause the vault
        vm.startPrank(admin);
        vault.grantRole(vault.PAUSER_ROLE(), address(anchor));
        vm.stopPrank();

        asset.mint(user, 100 ether);
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vault.deposit(1 ether, user);
        vm.stopPrank();
    }

    function testAuditorPulse() public {
        vm.startPrank(auditor);
        anchor.submitAuditorPulse(address(vault));
        vm.stopPrank();

        KerneTrustAnchor.SolvencyReport memory report = anchor.getSolvencyReport(address(vault));
        assertEq(report.lastAuditorPulse, block.timestamp);
    }

    function testAuditorEmergencyPause() public {
        vm.startPrank(auditor);
        anchor.raiseEmergencyFlag(address(vault));
        vm.stopPrank();

        assertTrue(vault.paused());
        assertFalse(anchor.isSolvent(address(vault)));
    }

    function testUnauthorizedAuditor() public {
        vm.startPrank(user);
        vm.expectRevert();
        anchor.submitAuditorPulse(address(vault));
        
        vm.expectRevert();
        anchor.raiseEmergencyFlag(address(vault));
        vm.stopPrank();
    }

    function testSolvencyWithEmergencyFlag() public {
        // Even if the vault has perfect collateral, emergency flag should make it insolvent
        vm.startPrank(admin);
        vault.updateHedgingReserve(10 ether); // Overcollateralized
        vm.stopPrank();

        KerneTrustAnchor.SolvencyReport memory reportBefore = anchor.getSolvencyReport(address(vault));
        console.log("Total Assets (Vault):", vault.totalAssets());
        console.log("Total Liabilities:", reportBefore.totalLiabilities);
        console.log("On-chain Collateral:", reportBefore.onChainCollateral);
        console.log("Verified Off-chain Equity:", reportBefore.verifiedOffChainEquity);
        console.log("Ratio Before:", reportBefore.solvencyRatio);
        console.log("Is Solvent Before:", reportBefore.isSolvent);
        
        // It should be solvent here
        assertTrue(anchor.isSolvent(address(vault)));

        vm.startPrank(auditor);
        anchor.raiseEmergencyFlag(address(vault));
        vm.stopPrank();

        KerneTrustAnchor.SolvencyReport memory reportAfter = anchor.getSolvencyReport(address(vault));
        console.log("Is Solvent After:", reportAfter.isSolvent);
        console.log("Emergency Flag:", anchor.auditorEmergencyFlag(address(vault)));
        assertFalse(anchor.isSolvent(address(vault)));
    }
}
