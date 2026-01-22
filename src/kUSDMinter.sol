// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

interface IKerneVault {
    function asset() external view returns (address);
    function totalAssets() external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function deposit(uint256 assets, address receiver) external returns (uint256);
    function redeem(uint256 shares, address receiver, address owner) external returns (uint256);
}

interface IKUSD is IERC20 {
    function mint(address to, uint256 amount) external;
    function burnFrom(address account, uint256 amount) external;
}

/**
 * @title kUSDMinter
 * @author Kerne Protocol
 * @notice Manages the minting and burning of kUSD against KerneVault shares (kLP).
 * @dev Includes leveraged yield loop (folding) with on-chain guardrails.
 */
contract kUSDMinter is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    struct Position {
        uint256 collateralAmount; // kLP shares
        uint256 debtAmount; // kUSD debt
    }

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    uint256 public constant PRECISION = 1e18;

    // 150% minting collateral ratio
    uint256 public MINT_COLLATERAL_RATIO = 1_500_000_000_000_000_000;
    // 120% liquidation threshold
    uint256 public LIQUIDATION_THRESHOLD = 1_200_000_000_000_000_000;
    // 5% liquidation bonus
    uint256 public LIQUIDATION_BONUS = 50_000_000_000_000_000;

    // Minimum health factor enforced after leverage/fold
    uint256 public minHealthFactor = 1_300_000_000_000_000_000;

    IKUSD public immutable kusd;
    IKerneVault public immutable vault;
    IERC20 public immutable kLP;

    address public dexAggregator;

    mapping(address => Position) public positions;

    event Minted(address indexed user, uint256 collateralAmount, uint256 kusdAmount);
    event Burned(address indexed user, uint256 collateralAmount, uint256 kusdAmount);
    event Liquidated(address indexed user, address indexed liquidator, uint256 collateralLiquidated, uint256 debtRepaid);
    event Folded(address indexed user, uint256 debtAdded, uint256 collateralAdded, uint256 healthFactor);
    event LeverageExecuted(address indexed user, uint256 assetDeposited, uint256 collateralAdded, uint256 kusdMinted);
    event DexAggregatorUpdated(address indexed previousAggregator, address indexed newAggregator);
    event RiskParamsUpdated(uint256 mintRatio, uint256 liquidationThreshold, uint256 liquidationBonus, uint256 minHealthFactor);

    constructor(address _kusd, address _vault, address _admin) {
        require(_kusd != address(0), "Invalid kUSD address");
        require(_vault != address(0), "Invalid vault address");
        require(_admin != address(0), "Invalid admin address");

        kusd = IKUSD(_kusd);
        vault = IKerneVault(_vault);
        kLP = IERC20(_vault);

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MANAGER_ROLE, _admin);
    }

    function pause() external onlyRole(MANAGER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    function setDexAggregator(address _aggregator) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address previous = dexAggregator;
        dexAggregator = _aggregator;
        emit DexAggregatorUpdated(previous, _aggregator);
    }

    function setRiskParams(
        uint256 mintRatio,
        uint256 liquidationThreshold,
        uint256 liquidationBonus,
        uint256 minHealthFactor_
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(mintRatio >= 1_200_000_000_000_000_000, "Mint ratio too low");
        require(liquidationThreshold >= 1_050_000_000_000_000_000, "Threshold too low");
        require(liquidationBonus <= 200_000_000_000_000_000, "Bonus too high");
        require(minHealthFactor_ >= liquidationThreshold, "Min HF too low");

        MINT_COLLATERAL_RATIO = mintRatio;
        LIQUIDATION_THRESHOLD = liquidationThreshold;
        LIQUIDATION_BONUS = liquidationBonus;
        minHealthFactor = minHealthFactor_;

        emit RiskParamsUpdated(mintRatio, liquidationThreshold, liquidationBonus, minHealthFactor_);
    }

    function getKLPPrice() public view returns (uint256) {
        uint256 supply = vault.totalSupply();
        if (supply == 0) {
            return PRECISION;
        }
        return (vault.totalAssets() * PRECISION) / supply;
    }

    function mint(uint256 kLPAmount, uint256 kusdAmount) external nonReentrant whenNotPaused {
        require(kLPAmount > 0, "Invalid collateral");
        require(kusdAmount > 0, "Invalid mint amount");

        kLP.safeTransferFrom(msg.sender, address(this), kLPAmount);

        Position storage position = positions[msg.sender];
        position.collateralAmount += kLPAmount;
        position.debtAmount += kusdAmount;

        _enforceMintRatio(position);
        _enforceMinHealth(position);

        kusd.mint(msg.sender, kusdAmount);

        emit Minted(msg.sender, kLPAmount, kusdAmount);
    }

    function burn(uint256 kusdAmount, uint256 kLPAmount) external nonReentrant whenNotPaused {
        require(kusdAmount > 0 || kLPAmount > 0, "Invalid burn");

        Position storage position = positions[msg.sender];

        if (kusdAmount > 0) {
            require(position.debtAmount >= kusdAmount, "Debt too low");
            kusd.burnFrom(msg.sender, kusdAmount);
            position.debtAmount -= kusdAmount;
        }

        if (kLPAmount > 0) {
            require(position.collateralAmount >= kLPAmount, "Collateral too low");
            position.collateralAmount -= kLPAmount;
            kLP.safeTransfer(msg.sender, kLPAmount);
        }

        if (position.debtAmount > 0) {
            _enforceMinHealth(position);
        }

        emit Burned(msg.sender, kLPAmount, kusdAmount);
    }

    function leverage(uint256 assetAmount, uint256 kusdAmount) external nonReentrant whenNotPaused {
        require(assetAmount > 0, "Invalid asset amount");
        require(kusdAmount > 0, "Invalid mint amount");

        address asset = vault.asset();
        IERC20(asset).safeTransferFrom(msg.sender, address(this), assetAmount);
        IERC20(asset).safeIncreaseAllowance(address(vault), assetAmount);

        uint256 shares = vault.deposit(assetAmount, address(this));

        Position storage position = positions[msg.sender];
        position.collateralAmount += shares;
        position.debtAmount += kusdAmount;

        _enforceMintRatio(position);
        _enforceMinHealth(position);

        kusd.mint(msg.sender, kusdAmount);

        emit LeverageExecuted(msg.sender, assetAmount, shares, kusdAmount);
    }

    function fold(uint256 amountToBorrow, uint256 minKLPOut) external nonReentrant whenNotPaused {
        require(amountToBorrow > 0, "Invalid borrow");
        require(dexAggregator != address(0), "Aggregator not set");

        Position storage position = positions[msg.sender];
        position.debtAmount += amountToBorrow;

        kusd.mint(address(this), amountToBorrow);
        IERC20(address(kusd)).safeIncreaseAllowance(dexAggregator, amountToBorrow);

        address asset = vault.asset();
        uint256 assetReceived = _swap(address(kusd), asset, amountToBorrow);
        IERC20(asset).safeIncreaseAllowance(address(vault), assetReceived);

        uint256 shares = vault.deposit(assetReceived, address(this));
        require(shares >= minKLPOut, "Slippage exceeded");

        position.collateralAmount += shares;

        _enforceMintRatio(position);
        uint256 healthFactor = _enforceMinHealth(position);

        emit Folded(msg.sender, amountToBorrow, shares, healthFactor);
    }

    function liquidate(address user) external nonReentrant whenNotPaused {
        Position storage position = positions[user];
        require(position.debtAmount > 0, "No debt");
        require(getHealthFactor(user) < PRECISION, "Position healthy");

        uint256 debtToCover = position.debtAmount;
        uint256 collateralValue = _collateralValue(position.collateralAmount);
        uint256 repayValue = (debtToCover * (PRECISION + LIQUIDATION_BONUS)) / PRECISION;

        uint256 seizeValue = repayValue > collateralValue ? collateralValue : repayValue;
        uint256 seizeShares = (seizeValue * PRECISION) / getKLPPrice();
        if (seizeShares > position.collateralAmount) {
            seizeShares = position.collateralAmount;
        }

        kusd.burnFrom(msg.sender, debtToCover);

        position.debtAmount = 0;
        position.collateralAmount -= seizeShares;

        kLP.safeTransfer(msg.sender, seizeShares);

        emit Liquidated(user, msg.sender, seizeShares, debtToCover);
    }

    function isHealthy(address user) external view returns (bool) {
        return getHealthFactor(user) >= PRECISION;
    }

    function isHealthy(address user, uint256 threshold) external view returns (bool) {
        return _healthFactor(positions[user], threshold) >= PRECISION;
    }

    function getHealthFactor(address user) public view returns (uint256) {
        return _healthFactor(positions[user], LIQUIDATION_THRESHOLD);
    }

    function _healthFactor(Position memory position, uint256 threshold) internal view returns (uint256) {
        if (position.debtAmount == 0) return 100 * PRECISION;
        uint256 ratio = (_collateralValue(position.collateralAmount) * PRECISION) / position.debtAmount;
        return (ratio * PRECISION) / threshold;
    }

    function _collateralValue(uint256 collateralAmount) internal view returns (uint256) {
        return (collateralAmount * getKLPPrice()) / PRECISION;
    }

    function _enforceMintRatio(Position memory position) internal view {
        uint256 required = (position.debtAmount * MINT_COLLATERAL_RATIO) / PRECISION;
        require(_collateralValue(position.collateralAmount) >= required, "Insufficient collateral");
    }

    function _enforceMinHealth(Position memory position) internal view returns (uint256) {
        uint256 healthFactor = _healthFactor(position, LIQUIDATION_THRESHOLD);
        require(healthFactor >= minHealthFactor, "Health factor too low");
        return healthFactor;
    }

    function _swap(address fromAsset, address toAsset, uint256 amount) internal returns (uint256 receivedAmount) {
        (bool success, bytes memory data) = dexAggregator.call(
            abi.encodeWithSignature(
                "swap(address,address,uint256,uint256)",
                fromAsset,
                toAsset,
                amount,
                0
            )
        );
        require(success && data.length >= 32, "Swap failed");
        receivedAmount = abi.decode(data, (uint256));
    }
}
