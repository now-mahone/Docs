// Created: 2026-02-05
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../../src/KerneAirdrop.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockToken is ERC20 {
    constructor() ERC20("Kerne", "KERNE") {}
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

contract KerneAirdropAuditTest is Test {
    KerneAirdrop public airdrop;
    MockToken public token;
    
    address public admin = address(1);
    address public user1 = address(2);
    address public user2 = address(3);
    address public user3 = address(4);
    
    bytes32 public root;
    
    function setUp() public {
        token = new MockToken();
        airdrop = new KerneAirdrop(address(token), admin);
        
        vm.startPrank(admin);
        airdrop.setClaimWindow(block.timestamp, block.timestamp + 7 days);
        vm.stopPrank();
        
        token.mint(address(airdrop), 1_000_000 ether);
    }

    /// @notice Test the pro-rata bonus distribution logic
    function test_ProRataBonusDistribution() public {
        uint256 alloc1 = 1000 ether;
        uint256 alloc2 = 1000 ether;
        uint256 alloc3 = 2000 ether;

        // User 1: Mercenary (Creates Penalty Pool)
        _performClaim(user1, KerneAirdrop.ClaimType.MERCENARY, alloc1);
        
        // Penalty Pool should be 750 ether
        assertEq(airdrop.penaltyPool(), 750 ether);

        // User 2: Loyalist (1000 locked)
        _performClaim(user2, KerneAirdrop.ClaimType.LOYALIST, alloc2);
        
        // User 3: Loyalist (2000 locked)
        _performClaim(user3, KerneAirdrop.ClaimType.LOYALIST, alloc3);

        assertEq(airdrop.totalLoyalistLocked(), 3000 ether);

        // Fast forward 1 year
        vm.warp(block.timestamp + 366 days);

        // User 2 Bonus: (750 * 1000) / 3000 = 250
        uint256 bonus2 = airdrop.previewLoyalistBonus(user2);
        assertEq(bonus2, 250 ether);

        // User 3 Bonus: (750 * 2000) / 3000 = 500
        uint256 bonus3 = airdrop.previewLoyalistBonus(user3);
        assertEq(bonus3, 500 ether);
        
        // Total distributed = 750 (Matches penalty pool)
        assertEq(bonus2 + bonus3, airdrop.penaltyPool());
    }

    /// @notice Test edge case: Zero Loyalists
    function test_ZeroLoyalistsEdgeCase() public {
        uint256 alloc1 = 1000 ether;
        _performClaim(user1, KerneAirdrop.ClaimType.MERCENARY, alloc1);
        
        // No loyalists, bonus should be 0 and not revert
        uint256 bonus = airdrop.previewLoyalistBonus(user2);
        assertEq(bonus, 0);
    }

    /// @notice Test rounding errors with small amounts
    function test_RoundingErrors() public {
        _performClaim(user1, KerneAirdrop.ClaimType.MERCENARY, 1000 ether); // 750 penalty
        
        // 3 Loyalists with 1 wei each
        _performClaim(user2, KerneAirdrop.ClaimType.LOYALIST, 1);
        _performClaim(user3, KerneAirdrop.ClaimType.LOYALIST, 1);
        _performClaim(address(5), KerneAirdrop.ClaimType.LOYALIST, 1);

        // (750e18 * 1) / 3 = 250e18
        assertEq(airdrop.previewLoyalistBonus(user2), 250 ether);
    }

    /// @notice Helper to perform a real claim with a valid Merkle proof
    function _performClaim(address user, KerneAirdrop.ClaimType cType, uint256 amount) internal {
        bytes32 leaf = keccak256(abi.encodePacked(user, amount));
        
        vm.prank(admin);
        airdrop.setMerkleRoot(leaf);
        
        bytes32[] memory proof = new bytes32[](0);
        
        vm.prank(user);
        airdrop.claim(cType, amount, proof);
    }
}