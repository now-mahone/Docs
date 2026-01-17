// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test } from "forge-std/Test.sol";
import { console } from "forge-std/console.sol";
import { KerneOFTV2 } from "../src/KerneOFTV2.sol";
import { KerneVault } from "../src/KerneVault.sol";
import { KerneVerificationNode } from "../src/KerneVerificationNode.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { MessageHashUtils } from "@openzeppelin/contracts/utils/cryptography/MessageHashUtils.sol";

contract OmnichainExpansionTest is Test {
    KerneOFTV2 baseKusd;
    KerneOFTV2 baseKerne;
    KerneVerificationNode baseNode;
    
    KerneOFTV2 arbKusd;
    KerneOFTV2 arbKerne;
    KerneVerificationNode arbNode;
    KerneVault arbVault;

    address admin = address(0xAD);
    uint256 adminPrivateKey = 0xAD;
    address lzEndpoint = 0x1a44076050125825900e736c501f859c50fE728c;
    
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;

    function setUp() public {
        // Mock LayerZero Endpoint
        vm.etch(lzEndpoint, hex"00");

        // Deploy on "Base"
        vm.startPrank(admin);
        baseKusd = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", lzEndpoint, admin);
        baseKerne = new KerneOFTV2("Kerne", "KERNE", lzEndpoint, admin);
        baseNode = new KerneVerificationNode(lzEndpoint, admin);
        vm.stopPrank();

        // Deploy on "Arbitrum"
        vm.startPrank(admin);
        arbKusd = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", lzEndpoint, admin);
        arbKerne = new KerneOFTV2("Kerne", "KERNE", lzEndpoint, admin);
        arbNode = new KerneVerificationNode(lzEndpoint, admin);
        
        // Deploy Arbitrum Vault (wstETH placeholder)
        address wstETH = address(0x123);
        vm.etch(wstETH, hex"00");
        arbVault = new KerneVault(
            IERC20(wstETH),
            "Kerne wstETH Vault",
            "k-wstETH",
            admin,
            admin,
            address(0x456)
        );
        arbVault.setVerificationNode(address(arbNode));
        vm.stopPrank();
    }

    function testPeerWiring() public {
        vm.startPrank(admin);

        // Wire Base -> Arbitrum
        baseKusd.setPeer(ARBITRUM_EID, bytes32(uint256(uint160(address(arbKusd)))));
        baseKerne.setPeer(ARBITRUM_EID, bytes32(uint256(uint160(address(arbKerne)))));
        baseNode.setPeer(ARBITRUM_EID, bytes32(uint256(uint160(address(arbNode)))));

        // Wire Arbitrum -> Base
        arbKusd.setPeer(BASE_EID, bytes32(uint256(uint160(address(baseKusd)))));
        arbKerne.setPeer(BASE_EID, bytes32(uint256(uint160(address(baseKerne)))));
        arbNode.setPeer(BASE_EID, bytes32(uint256(uint160(address(baseNode)))));

        vm.stopPrank();

        // Verify
        assertEq(baseKusd.peers(ARBITRUM_EID), bytes32(uint256(uint160(address(arbKusd)))));
        assertEq(arbKusd.peers(BASE_EID), bytes32(uint256(uint160(address(baseKusd)))));
        assertEq(baseNode.peers(ARBITRUM_EID), bytes32(uint256(uint160(address(arbNode)))));
        
        console.log("Peer wiring verified successfully.");
    }

    function testInstitutionalVaultDeployment() public {
        assertEq(arbVault.name(), "Kerne wstETH Vault");
        assertEq(arbVault.symbol(), "k-wstETH");
        assertTrue(arbVault.hasRole(arbVault.DEFAULT_ADMIN_ROLE(), admin));
        assertEq(arbVault.verificationNode(), address(arbNode));
        console.log("Arbitrum Vault deployment verified.");
    }
}
