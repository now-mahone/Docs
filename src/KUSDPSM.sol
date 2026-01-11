// SPDX-License-Identifier: MIT
// Created: 2026-01-10
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title KUSDPSM
 * @author Kerne Protocol
 * @notice Peg Stability Module for kUSD.
 * Allows 1:1 swaps between kUSD and other major stables (e.g., USDC, cbBTC) to maintain the peg.
 */
contract KUSDPSM is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    IERC20 public immutable kUSD;
    
    /// @notice Mapping of supported stablecoins and their swap fees (in bps)
    mapping(address => uint256) public swapFees;
    mapping(address => bool) public supportedStables;

    event StableAdded(address indexed stable, uint256 fee);
    event Swap(address indexed user, address indexed fromToken, address indexed toToken, uint256 amount, uint256 fee);

    constructor(address _kUSD, address _admin) {
        kUSD = IERC20(_kUSD);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /**
     * @notice Swaps a supported stablecoin for kUSD 1:1.
     */
    function swapStableForKUSD(address stable, uint256 amount) external nonReentrant {
        require(supportedStables[stable], "Stable not supported");
        uint256 fee = (amount * swapFees[stable]) / 10000;
        uint256 amountAfterFee = amount - fee;

        IERC20(stable).safeTransferFrom(msg.sender, address(this), amount);
        kUSD.safeTransfer(msg.sender, amountAfterFee);

        emit Swap(msg.sender, stable, address(kUSD), amount, fee);
    }

    /**
     * @notice Swaps kUSD for a supported stablecoin 1:1.
     */
    function swapKUSDForStable(address stable, uint256 amount) external nonReentrant {
        require(supportedStables[stable], "Stable not supported");
        uint256 fee = (amount * swapFees[stable]) / 10000;
        uint256 amountAfterFee = amount - fee;

        kUSD.safeTransferFrom(msg.sender, address(this), amount);
        IERC20(stable).safeTransfer(msg.sender, amountAfterFee);

        emit Swap(msg.sender, address(kUSD), stable, amount, fee);
    }

    // --- Admin Functions ---

    function addStable(address stable, uint256 feeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(feeBps <= 500, "Fee too high");
        supportedStables[stable] = true;
        swapFees[stable] = feeBps;
        emit StableAdded(stable, feeBps);
    }

    function removeStable(address stable) external onlyRole(DEFAULT_ADMIN_ROLE) {
        supportedStables[stable] = false;
    }

    function withdrawReserves(address token, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        IERC20(token).safeTransfer(msg.sender, amount);
    }
}
