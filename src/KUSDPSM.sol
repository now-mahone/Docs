// SPDX-License-Identifier: MIT
// Created: 2026-01-10
// Updated: 2026-01-12 - Fixed syntax and added flash loan support
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";

/**
 * @title KUSDPSM
 * @author Kerne Protocol
 * @notice Peg Stability Module for kUSD.
 * Allows 1:1 swaps between kUSD and other major stables (e.g., USDC, cbBTC) to maintain the peg.
 */
contract KUSDPSM is AccessControl, ReentrancyGuard, IERC3156FlashLender {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    IERC20 public immutable kUSD;
    
    /// @notice Mapping of supported stablecoins and their swap fees (in bps)
    mapping(address => uint256) public swapFees;
    mapping(address => bool) public supportedStables;

    /// @notice Tiered fee thresholds for institutional volume (amount => feeBps)
    struct TieredFee {
        uint256 threshold;
        uint256 feeBps;
    }
    mapping(address => TieredFee[]) public tieredFees;

    bool public virtualPegEnabled;
    uint256 public virtualPegFeeBps;
    uint256 public flashFeeBps;

    event StableAdded(address indexed stable, uint256 fee);
    event Swap(address indexed user, address indexed fromToken, address indexed toToken, uint256 amount, uint256 fee);
    event TieredFeeAdded(address indexed stable, uint256 threshold, uint256 feeBps);

    constructor(address _kUSD, address _admin) {
        kUSD = IERC20(_kUSD);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
    }

    /**
     * @notice Calculates the fee for a given amount and stablecoin.
     */
    function getFee(address stable, uint256 amount) public view returns (uint256) {
        if (virtualPegEnabled) {
            return (amount * virtualPegFeeBps) / 10000;
        }

        uint256 feeBps = swapFees[stable];
        TieredFee[] storage tiers = tieredFees[stable];
        
        for (uint256 i = 0; i < tiers.length; i++) {
            if (amount >= tiers[i].threshold) {
                feeBps = tiers[i].feeBps;
                break;
            }
        }
        return (amount * feeBps) / 10000;
    }

    function setVirtualPeg(bool _enabled, uint256 _feeBps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        virtualPegEnabled = _enabled;
        virtualPegFeeBps = _feeBps;
    }

    /**
     * @notice Swaps a supported stablecoin for kUSD 1:1.
     */
    function swapStableForKUSD(address stable, uint256 amount) external nonReentrant {
        require(supportedStables[stable], "Stable not supported");
        uint256 fee = getFee(stable, amount);
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
        uint256 fee = getFee(stable, amount);
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

    function setTieredFees(address stable, TieredFee[] calldata fees) external onlyRole(DEFAULT_ADMIN_ROLE) {
        delete tieredFees[stable];
        for (uint256 i = 0; i < fees.length; i++) {
            require(fees[i].feeBps <= 500, "Fee too high");
            tieredFees[stable].push(fees[i]);
            emit TieredFeeAdded(stable, fees[i].threshold, fees[i].feeBps);
        }
    }

    function setFlashFee(uint256 bps) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(bps <= 100, "Fee too high");
        flashFeeBps = bps;
    }

    // --- IERC3156FlashLender Implementation ---

    function maxFlashLoan(address token) external view override returns (uint256) {
        if (token != address(kUSD) && !supportedStables[token]) return 0;
        return IERC20(token).balanceOf(address(this));
    }

    function flashFee(address token, uint256 amount) public view override returns (uint256) {
        require(token == address(kUSD) || supportedStables[token], "Unsupported token");
        return (amount * flashFeeBps) / 10000;
    }

    function flashLoan(
        IERC3156FlashBorrower receiver,
        address token,
        uint256 amount,
        bytes calldata data
    ) external override nonReentrant returns (bool) {
        require(token == address(kUSD) || supportedStables[token], "Unsupported token");
        uint256 fee = flashFee(token, amount);

        IERC20(token).safeTransfer(address(receiver), amount);

        require(
            receiver.onFlashLoan(msg.sender, token, amount, fee, data) == keccak256("ERC3156FlashBorrower.onFlashLoan"),
            "Flash loan callback failed"
        );

        IERC20(token).safeTransferFrom(address(receiver), address(this), amount + fee);

        return true;
    }
}
