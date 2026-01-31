// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console2 } from "forge-std/Test.sol";
import { KerneAirdrop } from "../../src/KerneAirdrop.sol";
import { KerneToken } from "../../src/KerneToken.sol";
import { Merkle } from "lib/murky/src/Merkle.sol";

contract KerneAirdropTest is Test {
    KerneAirdrop public airdrop;
    KerneToken public token;
    Merkle public murky;

    address public admin = address(0x1);
    address public user1 = address(0x2);
    address public user2 = address(0x3);
    address public user3 = address(0x4);

    bytes32[] public leaves;
    bytes32 public root;

    uint256 public constant ALLOCATION = 1000e18;

    function setUp() public {
        murky = new Merkle();
        
        token = new KerneToken(admin);
        airdrop = new KerneAirdrop(address(token), admin);

        // Setup Merkle Tree
        leaves.push(keccak256(abi.encodePacked(user1, ALLOCATION)));
        leaves.push(keccak256(abi.encodePacked(user2, ALLOCATION)));
        leaves.push(keccak256(abi.encodePacked(user3, ALLOCATION)));
        root = murky.getRoot(leaves);

        vm.startPrank(admin);
        airdrop.setMerkleRoot(root);
        airdrop.setClaimWindow(block.timestamp, block.timestamp + 7 days);
        vm.stopPrank();

        token.transfer(address(airdrop), 10000e18);
    }

    function test_MercenaryClaim() public {
        bytes32[] memory proof = murky.getProof(leaves, 0);
        
        vm.prank(user1);
        airdrop.claim(KerneAirdrop.ClaimType.MERCENARY, ALLOCATION, proof);

        uint256 expectedReceived = (ALLOCATION * 2500) / 10000;
        uint256 expectedPenalty = ALLOCATION - expectedReceived;

        assertEq(token.balanceOf(user1), expectedReceived);
        assertEq(airdrop.penaltyPool(), expectedPenalty);
    }

    function test_LoyalistLockAndBonus() public {
        // User 1 is Mercenary (creates penalty pool)
        bytes32[] memory proof1 = murky.getProof(leaves, 0);
        vm.prank(user1);
        airdrop.claim(KerneAirdrop.ClaimType.MERCENARY, ALLOCATION, proof1);
        
        uint256 penalty = airdrop.penaltyPool();

        // User 2 is Loyalist
        bytes32[] memory proof2 = murky.getProof(leaves, 1);
        vm.prank(user2);
        airdrop.claim(KerneAirdrop.ClaimType.LOYALIST, ALLOCATION, proof2);

        assertEq(airdrop.totalLoyalistLocked(), ALLOCATION);
        
        // Fast forward 1 year
        vm.warp(block.timestamp + 366 days);

        vm.prank(user2);
        airdrop.unlockLoyalist();

        // User 2 should get ALLOCATION + 100% of penalty pool (since they are the only loyalist)
        assertEq(token.balanceOf(user2), ALLOCATION + penalty);
    }

    function test_VestingClaim() public {
        bytes32[] memory proof = murky.getProof(leaves, 2);
        
        vm.prank(user3);
        airdrop.claim(KerneAirdrop.ClaimType.VESTING, ALLOCATION, proof);

        // Fast forward 6 months
        vm.warp(block.timestamp + 182.5 days);

        vm.prank(user3);
        airdrop.withdrawVested();

        // Should have ~50%
        assertApproxEqRel(token.balanceOf(user3), ALLOCATION / 2, 0.01e18);
    }
}