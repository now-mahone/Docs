// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "./KerneToken.sol";

/**
 * @title KerneStaking
 * @author Kerne Protocol
 * @notice ve-style staking for $KERNE tokens to receive protocol fees and voting power.
 */
contract KerneStaking is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant DISTRIBUTOR_ROLE = keccak256("DISTRIBUTOR_ROLE");

    KerneToken public immutable kerne;
    IERC20 public immutable rewardToken; // e.g., WETH or kUSD

    struct Stake {
        uint256 amount;
        uint256 lockEnd;
        uint256 rewardDebt;
    }

    mapping(address => Stake) public stakes;
    uint256 public totalStaked;
    uint256 public accRewardPerShare;
    uint256 public constant PRECISION = 1e18;

    event Staked(address indexed user, uint256 amount, uint256 lockDuration);
    event Withdrawn(address indexed user, uint256 amount);
    event RewardClaimed(address indexed user, uint256 amount);
    event RewardDistributed(uint256 amount);

    constructor(address _kerne, address _rewardToken, address _admin) {
        kerne = KerneToken(_kerne);
        rewardToken = IERC20(_rewardToken);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /**
     * @notice Stakes $KERNE tokens for a specified duration.
     * @param amount The amount of $KERNE to stake.
     * @param duration The duration to lock (in seconds).
     */
    function stake(uint256 amount, uint256 duration) external nonReentrant {
        require(amount > 0, "Amount must be > 0");

        updateRewards(msg.sender);

        IERC20(address(kerne)).safeTransferFrom(msg.sender, address(this), amount);

        stakes[msg.sender].amount += amount;
        stakes[msg.sender].lockEnd = block.timestamp + duration;
        totalStaked += amount;

        stakes[msg.sender].rewardDebt = (stakes[msg.sender].amount * accRewardPerShare) / PRECISION;

        emit Staked(msg.sender, amount, duration);
    }

    /**
     * @notice Withdraws staked $KERNE tokens after the lock period.
     */
    function withdraw() external nonReentrant {
        Stake storage s = stakes[msg.sender];
        require(block.timestamp >= s.lockEnd, "Lock not expired");
        require(s.amount > 0, "No stake");

        updateRewards(msg.sender);

        uint256 amount = s.amount;
        s.amount = 0;
        totalStaked -= amount;

        IERC20(address(kerne)).safeTransfer(msg.sender, amount);

        emit Withdrawn(msg.sender, amount);
    }

    /**
     * @notice Distributes rewards to stakers.
     * @param amount The amount of reward tokens to distribute.
     */
    function distributeRewards(
        uint256 amount
    ) external onlyRole(DISTRIBUTOR_ROLE) {
        require(amount > 0, "Amount must be > 0");
        require(totalStaked > 0, "No stakers");

        rewardToken.safeTransferFrom(msg.sender, address(this), amount);
        accRewardPerShare += (amount * PRECISION) / totalStaked;

        emit RewardDistributed(amount);
    }

    /**
     * @notice Claims pending rewards.
     */
    function claimRewards() public nonReentrant {
        updateRewards(msg.sender);
    }

    function updateRewards(
        address user
    ) internal {
        Stake storage s = stakes[user];
        if (s.amount > 0) {
            uint256 pending = (s.amount * accRewardPerShare) / PRECISION - s.rewardDebt;
            if (pending > 0) {
                s.rewardDebt = (s.amount * accRewardPerShare) / PRECISION;
                rewardToken.safeTransfer(user, pending);
                emit RewardClaimed(user, pending);
            }
        }
    }

    function getPendingRewards(
        address user
    ) external view returns (uint256) {
        Stake memory s = stakes[user];
        return (s.amount * accRewardPerShare) / PRECISION - s.rewardDebt;
    }
}
