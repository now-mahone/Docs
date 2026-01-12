// SPDX-License-Identifier: MIT
// Created: 2026-01-10
// Updated: 2026-01-12 - Institutional Deep Hardening: Advanced arbitrage, flash loans, and liquidity routing
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
 * Allows 1:1 swaps between kUSD and other major stables to maintain the peg.
 * Hardened with flash loans and tiered institutional fees.
 */
contract KUSDPSM is AccessControl, ReentrancyGuard, IERC3156FlashLender {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");
    bytes32 public constant ARBITRAGEUR_ROLE = keccak256("ARBITRAGEUR_ROLE");

    IERC20 public immutable kUSD;
    
    mapping(address => uint256) public swapFees;
    mapping(address => bool) public supportedStables;

    struct TieredFee {
        uint256 threshold;
        uint256 feeBps;
    }
    mapping(address => TieredFee[]) public tieredFees;

    bool public virtualPegEnabled;
    uint256 public virtualPegFeeBps;
    uint256 public flashFeeBps;
    
    /// @notice Circuit breaker for total exposure per stable
    mapping(address => uint256) public stableCaps;
    mapping(address => uint256) public currentExposure;

    event StableAdded(address indexed stable, uint256 fee, uint256 cap);
    event Swap(address indexed user, address indexed fromToken, address indexed toToken, uint256 amount, uint256 fee);
    event TieredFeeAdded(address indexed stable, uint256 threshold, uint256 feeBps);
    event ExposureUpdated(address indexed stable, uint256 newExposure);

    constructor(address _kUSD, address _admin) {
        kUSD = IERC20(_kUSD);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MANAGER_ROLE, _admin);
    }

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

    function swapStableForKUSD(address stable, uint256 amount) external nonReentrant {
        require(supportedStables[stable], "Stable not supported");
        require(currentExposure[stable] + amount <= stableCaps[stable], "Stable cap exceeded");
        
        uint256 fee = getFee(stable, amount);
        uint256 amountAfterFee = amount - fee;

        currentExposure[stable] += amount;
        IERC20(stable).safeTransferFrom(msg.sender, address(this), amount);
        kUSD.safeTransfer(msg.sender, amountAfterFee);

        emit Swap(msg.sender, stable, address(kUSD), amount, fee);
        emit ExposureUpdated(stable, currentExposure[stable]);
    }

    function swapKUSDForStable(address stable, uint256 amount) external nonReentrant {
        require(supportedStables[stable], "Stable not supported");
        require(currentExposure[stable] >= amount, "Insufficient stable exposure");
        
        uint256 fee = getFee(stable, amount);
        uint256 amountAfterFee = amount - fee;

        currentExposure[stable] -= amount;
        kUSD.safeTransferFrom(msg.sender, address(this), amount);
        IERC20(stable).safeTransfer(msg.sender, amountAfterFee);

        emit Swap(msg.sender, address(kUSD), stable, amount, fee);
        emit ExposureUpdated(stable, currentExposure[stable]);
    }

    // --- Admin Functions ---

    function addStable(address stable, uint256 feeBps, uint256 cap) external onlyRole(MANAGER_ROLE) {
        require(feeBps <= 500, "Fee too high");
        supportedStables[stable] = true;
        swapFees[stable] = feeBps;
        stableCaps[stable] = cap;
        emit StableAdded(stable, feeBps, cap);
    }

    function setStableCap(address stable, uint256 cap) external onlyRole(MANAGER_ROLE) {
        stableCaps[stable] = cap;
    }

    function setTieredFees(address stable, TieredFee[] calldata fees) external onlyRole(MANAGER_ROLE) {
        delete tieredFees[stable];
        for (uint256 i = 0; i < fees.length; i++) {
            require(fees[i].feeBps <= 500, "Fee too high");
            tieredFees[stable].push(fees[i]);
            emit TieredFeeAdded(stable, fees[i].threshold, fees[i].feeBps);
        }
    }

    function setFlashFee(uint256 bps) external onlyRole(MANAGER_ROLE) {
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
        // 0% fee for authorized arbitrageurs
        if (hasRole(ARBITRAGEUR_ROLE, msg.sender)) return 0;
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
