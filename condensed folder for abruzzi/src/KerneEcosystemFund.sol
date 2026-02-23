// Created: 2026-01-06
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title KerneEcosystemFund
 * @author Kerne Protocol
 * @notice Manages grants, investments, and revenue sharing for the Kerne ecosystem.
 */
contract KerneEcosystemFund is Ownable, ReentrancyGuard {
    struct Grant {
        address recipient;
        uint256 amount;
        uint256 released;
        uint256 startTime;
        uint256 duration;
        bool active;
    }

    mapping(uint256 => Grant) public grants;
    uint256 public grantCount;

    address public kerneToken;
    uint256 public totalRevenueShared;

    event GrantCreated(uint256 indexed grantId, address indexed recipient, uint256 amount);
    event GrantReleased(uint256 indexed grantId, uint256 amount);
    event RevenueShared(address indexed token, uint256 amount);

    constructor(
        address _kerneToken
    ) Ownable(msg.sender) {
        kerneToken = _kerneToken;
    }

    /**
     * @notice Creates a new ecosystem grant with linear vesting.
     */
    function createGrant(address _recipient, uint256 _amount, uint256 _duration) external onlyOwner {
        require(_recipient != address(0), "Invalid recipient");
        require(_amount > 0, "Invalid amount");

        grants[grantCount] = Grant({
            recipient: _recipient,
            amount: _amount,
            released: 0,
            startTime: block.timestamp,
            duration: _duration,
            active: true
        });

        emit GrantCreated(grantCount, _recipient, _amount);
        grantCount++;
    }

    /**
     * @notice Releases vested grant tokens to the recipient.
     */
    function releaseGrant(
        uint256 _grantId
    ) external nonReentrant {
        Grant storage grant = grants[_grantId];
        require(grant.active, "Grant not active");

        uint256 vested = _calculateVestedAmount(_grantId);
        uint256 releasable = vested - grant.released;
        require(releasable > 0, "Nothing to release");

        grant.released += releasable;
        IERC20(kerneToken).transfer(grant.recipient, releasable);

        emit GrantReleased(_grantId, releasable);
    }

    /**
     * @notice Shares protocol revenue with $KERNE holders (simulated via fund accumulation).
     */
    function shareRevenue(address _token, uint256 _amount) external {
        IERC20(_token).transferFrom(msg.sender, address(this), _amount);
        totalRevenueShared += _amount;
        emit RevenueShared(_token, _amount);
    }

    function _calculateVestedAmount(
        uint256 _grantId
    ) internal view returns (uint256) {
        Grant storage grant = grants[_grantId];
        if (block.timestamp < grant.startTime) return 0;
        if (block.timestamp >= grant.startTime + grant.duration) return grant.amount;

        return (grant.amount * (block.timestamp - grant.startTime)) / grant.duration;
    }

    /**
     * @notice Emergency withdrawal of tokens.
     */
    function emergencyWithdraw(address _token, uint256 _amount) external onlyOwner {
        IERC20(_token).transfer(owner(), _amount);
    }
}
