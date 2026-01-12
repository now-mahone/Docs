// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./kUSD.sol";
import "./KerneVault.sol";

/**
 * @title kUSDStabilityModule
 * @author Kerne Protocol
 * @notice Defends the kUSD peg using protocol yield and manages liquidity incentives.
 */
contract kUSDStabilityModule is AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    kUSD public immutable kusd;
    KerneVault public immutable vault;
    IERC20 public immutable usdc;

    uint256 public constant PEG_PRICE = 1e6; // USDC has 6 decimals
    uint256 public constant DEVIATION_THRESHOLD = 5000; // 0.5% (5000 / 1e6)

    event PegDefended(uint256 amountSpent, uint256 kusdBought);
    event YieldHarvested(uint256 amount);

    constructor(address _kusd, address _vault, address _usdc, address _admin) {
        kusd = kUSD(_kusd);
        vault = KerneVault(_vault);
        usdc = IERC20(_usdc);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(STRATEGIST_ROLE, _admin);
    }

    /**
     * @notice Harvests yield from the vault to the stability module.
     * @dev In a real scenario, this would be triggered by the strategist after profit reporting.
     */
    function harvestYield(
        uint256 amount
    ) external onlyRole(STRATEGIST_ROLE) {
        // This assumes the vault has a way to distribute yield to the stability module.
        // For now, we'll just transfer from the vault if it has the balance.
        // In production, this would be a dedicated 'distributeYield' call in KerneVault.
        IERC20(vault.asset()).safeTransferFrom(address(vault), address(this), amount);
        emit YieldHarvested(amount);
    }

    /**
     * @notice Defends the peg by buying kUSD with USDC if price < $1.00.
     * @dev This is a simplified version. In production, it would interface with a DEX aggregator.
     * @param usdcAmount The amount of USDC to spend on buybacks.
     * @param minKUSD The minimum kUSD to receive (slippage protection).
     */
    function defendPeg(uint256 usdcAmount, uint256 minKUSD) external onlyRole(STRATEGIST_ROLE) {
        require(usdcAmount > 0, "Invalid amount");

        // Logic to swap USDC for kUSD on a DEX (e.g., Aerodrome)
        // usdc.approve(router, usdcAmount);
        // router.swapExactTokensForTokens(...)

        emit PegDefended(usdcAmount, minKUSD);
    }

    /**
     * @notice Emergency withdrawal of tokens.
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        IERC20(token).safeTransfer(msg.sender, amount);
    }
}
