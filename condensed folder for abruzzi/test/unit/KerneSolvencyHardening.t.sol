// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneVault } from "src/KerneVault.sol";
import { KerneVerificationNode } from "src/KerneVerificationNode.sol";
import { KerneTrustAnchor } from "src/KerneTrustAnchor.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor() ERC20("Mock WETH", "WETH") { }
    function mint(address to, uint256 amount) public { _mint(to, amount); }
}

contract MockLZEndpoint {
    function setDelegate(address) external { }
}

contract KerneSolvencyHardeningTest is Test {
    KerneVault public vault;
    KerneVerificationNode public node;
    KerneTrustAnchor public anchor;
    MockERC20 public asset;

    address public admin = address(0x1);
    address public verifier = address(0x2);
    address public user = address(0x3);
    uint256 public verifierKey = 0x1234;

    function setUp() public {
        asset = new MockERC20();
        verifier = vm.addr(verifierKey);
        
        address lzEndpoint = address(new MockLZEndpoint());

        vault = new KerneVault(asset, "KUSD Vault", "kUSD", admin, admin, address(0x4));
        node = new KerneVerificationNode(lzEndpoint, admin);
        anchor = new KerneTrustAnchor(admin);

        vm.startPrank(admin);
        node.setSigner(verifier, true);
        anchor.setVerificationNode(address(vault), address(node));
        vault.setTrustAnchor(address(anchor));
        vault.setFounder(admin);
        vault.updateHedgingReserve(1000); // Match dead shares to keep 1:1 ratio
        
        // Satisfy auditor pulse
        anchor.grantRole(anchor.AUDITOR_ROLE(), admin);
        anchor.submitAuditorPulse(address(vault));
        vm.stopPrank();

        asset.mint(user, 100 ether);
        
        // Initial deposit to get past dead shares
        vm.startPrank(user);
        asset.approve(address(vault), 10 ether);
        vault.deposit(10 ether, user);
        vm.stopPrank();
    }

    function _signAttestation(uint256 amount, uint256 delta, uint256 equity, uint256 timestamp) internal view returns (bytes memory) {
        bytes32 messageHash = keccak256(abi.encodePacked(
            block.chainid,
            address(node),
            address(vault), 
            amount, 
            delta, 
            equity, 
            timestamp
        ));
        bytes32 ethSignedMessageHash = keccak256(abi.encodePacked("\x19Ethereum Signed Message:\n32", messageHash));
        (uint8 v, bytes32 r, bytes32 s) = vm.sign(verifierKey, ethSignedMessageHash);
        return abi.encodePacked(r, s, v);
    }

    function testSolventAttestation() public {
        uint256 amount = 10 ether;
        uint256 delta = 0.02e18; // 2%
        uint256 equity = 5 ether;
        uint256 ts = block.timestamp;
        bytes memory sig = _signAttestation(amount, delta, equity, ts);

        node.submitVerifiedAttestation(address(vault), amount, delta, equity, ts, sig);

        assertTrue(anchor.isSolvent(address(vault)));
    }

    function testInsolventDueToDelta() public {
        uint256 amount = 10 ether;
        uint256 delta = 0.06e18; // 6% > 5% threshold
        uint256 equity = 5 ether;
        uint256 ts = block.timestamp;
        bytes memory sig = _signAttestation(amount, delta, equity, ts);

        node.submitVerifiedAttestation(address(vault), amount, delta, equity, ts, sig);

        assertFalse(anchor.isSolvent(address(vault)));
    }

    function testCircuitBreakerRevert() public {
        // 1. Initial deposit works (no trust anchor check if no liabilities or no anchor set)
        
        // Submit insolvent attestation
        uint256 amount = 10 ether;
        uint256 delta = 0.1e18; // 10%
        uint256 equity = 5 ether;
        uint256 ts = block.timestamp;
        bytes memory sig = _signAttestation(amount, delta, equity, ts);
        node.submitVerifiedAttestation(address(vault), amount, delta, equity, ts, sig);

        // Call checkAndPause to start insolvency timer (requires PAUSER_ROLE)
        vm.prank(admin);
        vault.checkAndPause();
        
        // Warp past grace period (4 hours)
        vm.warp(block.timestamp + 5 hours);

        vm.startPrank(user);
        asset.approve(address(vault), 1 ether);
        // Should revert because Trust Anchor says insolvent and grace period passed
        // Note: deposit calls _checkSolvency(false) which pauses, then super.deposit checks maxDeposit
        // If paused, maxDeposit returns 0, and super.deposit reverts with ERC4626ExceededMaxDeposit
        vm.expectRevert(); 
        vault.deposit(1 ether, user);
        vm.stopPrank();
    }

    function testGracePeriodAutomaticPause() public {
        // 1. Make it insolvent
        uint256 amount = 10 ether;
        uint256 delta = 0.1e18;
        uint256 equity = 5 ether;
        uint256 ts = block.timestamp;
        bytes memory sig = _signAttestation(amount, delta, equity, ts);
        node.submitVerifiedAttestation(address(vault), amount, delta, equity, ts, sig);

        // 2. Call checkAndPause once to record insolvency start (requires PAUSER_ROLE)
        vm.prank(admin);
        vault.checkAndPause();
        assertEq(vault.insolventSince(), block.timestamp);
        
        // 3. Warp past grace period (4 hours)
        vm.warp(block.timestamp + 5 hours);
        
        // 4. Call checkAndPause again, should pause the vault
        // Note: checkAndPause calls _updateSolvency(false) which reverts if paused or grace period passed
        // But we want to check if it paused.
        vm.prank(admin);
        try vault.checkAndPause() {} catch {}

        assertTrue(vault.paused());
    }
}
