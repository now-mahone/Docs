// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "src/KerneToken.sol";
import "src/KerneStaking.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockRewardToken is ERC20 {
    constructor() ERC20("Reward Token", "REWARD") { }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KerneGovernanceTest is Test {
    KerneToken public kerne;
    KerneStaking public staking;
    MockRewardToken public rewardToken;

    address public admin = address(0x1);
    address public user1 = address(0x2);
    address public user2 = address(0x3);

    function setUp() public {
        vm.startPrank(admin);
        kerne = new KerneToken(admin);
        rewardToken = new MockRewardToken();
        staking = new KerneStaking(address(kerne), address(rewardToken), admin);

        staking.grantRole(staking.DISTRIBUTOR_ROLE(), admin);
        vm.stopPrank();

        vm.prank(admin);
        kerne.transfer(user1, 1000e18);
        vm.prank(admin);
        kerne.transfer(user2, 1000e18);
    }

    function testStakingAndRewards() public {
        // 1. Users stake
        vm.startPrank(user1);
        kerne.approve(address(staking), 500e18);
        staking.stake(500e18, 7 days);
        vm.stopPrank();

        vm.startPrank(user2);
        kerne.approve(address(staking), 500e18);
        staking.stake(500e18, 7 days);
        vm.stopPrank();

        // 2. Admin distributes rewards
        vm.startPrank(admin);
        rewardToken.mint(admin, 100e18);
        rewardToken.approve(address(staking), 100e18);
        staking.distributeRewards(100e18);
        vm.stopPrank();

        // 3. Check pending rewards (should be 50/50)
        assertEq(staking.getPendingRewards(user1), 50e18);
        assertEq(staking.getPendingRewards(user2), 50e18);

        // 4. User1 claims
        vm.prank(user1);
        staking.claimRewards();
        assertEq(rewardToken.balanceOf(user1), 50e18);
        assertEq(staking.getPendingRewards(user1), 0);
    }

    function testWithdrawalLock() public {
        vm.startPrank(user1);
        kerne.approve(address(staking), 500e18);
        staking.stake(500e18, 7 days);

        vm.expectRevert("Lock not expired");
        staking.withdraw();

        vm.warp(block.timestamp + 8 days);
        staking.withdraw();
        assertEq(kerne.balanceOf(user1), 1000e18);
        vm.stopPrank();
    }
}
