// Created: 2026-01-04
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title KerneInsuranceFund
 * @notice Protocol-owned insurance fund to cover depeg events or exchange failures.
 * @dev Funded by a 5% diversion of protocol yield.
 */
contract KerneInsuranceFund is Ownable, ReentrancyGuard {
    address public immutable asset; // Usually WETH or USDC
    uint256 public totalCovered;

    mapping(address => bool) public isAuthorized;

    event FundsDeposited(uint256 amount);
    event AuthorizationUpdated(address indexed caller, bool status);
    event CoverageClaimed(address indexed recipient, uint256 amount);

    constructor(
        address _asset
    ) Ownable(msg.sender) {
        asset = _asset;
    }

    /**
     * @notice Deposits funds into the insurance pool.
     * @param amount The amount of asset to deposit.
     */
    function deposit(
        uint256 amount
    ) external nonReentrant {
        IERC20(asset).transferFrom(msg.sender, address(this), amount);
        emit FundsDeposited(amount);
    }

    /**
     * @notice Sets authorization for a vault or contract to claim funds.
     */
    function setAuthorization(address caller, bool status) external onlyOwner {
        isAuthorized[caller] = status;
        emit AuthorizationUpdated(caller, status);
    }

    /**
     * @notice Claims coverage in case of a verified protocol loss.
     * @dev Only callable by the owner (Multisig) or authorized vault.
     */
    function claim(address recipient, uint256 amount) external nonReentrant {
        require(msg.sender == owner() || isAuthorized[msg.sender], "Not authorized");
        uint256 balance = IERC20(asset).balanceOf(address(this));
        require(amount <= balance, "Insufficient insurance balance");

        IERC20(asset).transfer(recipient, amount);
        totalCovered += amount;

        emit CoverageClaimed(recipient, amount);
    }

    /**
     * @notice Returns the current insurance fund balance.
     */
    function getBalance() external view returns (uint256) {
        return IERC20(asset).balanceOf(address(this));
    }
}
