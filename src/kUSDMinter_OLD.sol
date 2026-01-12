// Created: 2025-12-29
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "./kUSD.sol";
import "./KerneVault.sol";

/**
 * @title kUSDMinter
 * @author Kerne Protocol
 * @notice Manages the minting and burning of kUSD against KerneVault shares (kLP).
 */
contract kUSDMinter is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    kUSD public immutable kusd;
    KerneVault public immutable vault;

    uint256 public constant PRECISION = 1e18;
    uint256 public constant MINT_COLLATERAL_RATIO = 150; // 150%
    uint256 public constant LIQUIDATION_THRESHOLD = 120; // 120%
    uint256 public constant LIQUIDATION_BONUS = 5; // 5% bonus to liquidators

    struct Position {
        uint256 collateralAmount; // kLP shares
        uint256 debtAmount; // kUSD minted
    }

    mapping(address => Position) public positions;
    uint256 public totalDebt;

    event Minted(address indexed user, uint256 collateralAmount, uint256 kusdAmount);
    event Burned(address indexed user, uint256 collateralAmount, uint256 kusdAmount);
    event Leveraged(address indexed user, uint256 wethAmount, uint256 kLPMinted, uint256 kusdMinted);
    event Liquidated(
        address indexed user, address indexed liquidator, uint256 collateralLiquidated, uint256 debtRepaid
    );

    constructor(address _kusd, address _vault, address _admin) {
        kusd = kUSD(_kusd);
        vault = KerneVault(_vault);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MANAGER_ROLE, _admin);
    }

    /**
     * @notice Mints kUSD by locking KerneVault shares.
     * @param kLPAmount The amount of kLP shares to lock as collateral.
     * @param kusdAmount The amount of kUSD to mint.
     */
    function mint(uint256 kLPAmount, uint256 kusdAmount) public nonReentrant whenNotPaused {
        require(kLPAmount > 0 || kusdAmount > 0, "Invalid amounts");

        if (kLPAmount > 0) {
            IERC20(address(vault)).safeTransferFrom(msg.sender, address(this), kLPAmount);
            positions[msg.sender].collateralAmount += kLPAmount;
        }

        if (kusdAmount > 0) {
            positions[msg.sender].debtAmount += kusdAmount;
            totalDebt += kusdAmount;
            require(isHealthy(msg.sender), "Insufficient collateral");
            kusd.mint(msg.sender, kusdAmount);
        }

        emit Minted(msg.sender, kLPAmount, kusdAmount);
    }

    /**
     * @notice One-click leverage: Deposits WETH, mints kLP, locks kLP, mints kUSD.
     * @param wethAmount The amount of WETH to deposit.
     * @param kusdAmount The amount of kUSD to mint against the new collateral.
     */
    function leverage(uint256 wethAmount, uint256 kusdAmount) external nonReentrant whenNotPaused {
        require(wethAmount > 0, "Invalid WETH amount");

        // 1. Transfer WETH from user
        IERC20 weth = IERC20(vault.asset());
        weth.safeTransferFrom(msg.sender, address(this), wethAmount);

        // 2. Deposit WETH into Vault to get kLP
        weth.approve(address(vault), wethAmount);
        uint256 kLPMinted = vault.deposit(wethAmount, address(this));

        // 3. Update position
        positions[msg.sender].collateralAmount += kLPMinted;

        if (kusdAmount > 0) {
            positions[msg.sender].debtAmount += kusdAmount;
            totalDebt += kusdAmount;
            require(isHealthy(msg.sender), "Insufficient collateral for leverage");
            kusd.mint(msg.sender, kusdAmount);
        }

        emit Leveraged(msg.sender, wethAmount, kLPMinted, kusdAmount);
    }

    /**
     * @notice Burns kUSD to unlock KerneVault shares.
     * @param kusdAmount The amount of kUSD to repay.
     * @param kLPAmount The amount of kLP shares to unlock.
     */
    function burn(uint256 kusdAmount, uint256 kLPAmount) external nonReentrant {
        require(kusdAmount > 0 || kLPAmount > 0, "Invalid amounts");

        if (kusdAmount > 0) {
            require(positions[msg.sender].debtAmount >= kusdAmount, "Exceeds debt");
            kusd.burnFrom(msg.sender, kusdAmount);
            positions[msg.sender].debtAmount -= kusdAmount;
            totalDebt -= kusdAmount;
        }

        if (kLPAmount > 0) {
            require(positions[msg.sender].collateralAmount >= kLPAmount, "Exceeds collateral");
            positions[msg.sender].collateralAmount -= kLPAmount;
            require(isHealthy(msg.sender), "Insufficient collateral remaining");
            IERC20(address(vault)).safeTransfer(msg.sender, kLPAmount);
        }

        emit Burned(msg.sender, kLPAmount, kusdAmount);
    }

    /**
     * @notice Liquidates an unhealthy position.
     * @param user The address of the user to liquidate.
     */
    function liquidate(
        address user
    ) external nonReentrant {
        require(!isHealthy(user, LIQUIDATION_THRESHOLD), "Position is healthy");

        Position storage pos = positions[user];
        uint256 debtToRepay = pos.debtAmount;

        // Calculate collateral to seize: debt + bonus
        uint256 collateralValueToSeize = (debtToRepay * (100 + LIQUIDATION_BONUS)) / 100;
        uint256 kLPToSeize = (collateralValueToSeize * PRECISION) / getKLPPrice();

        if (kLPToSeize > pos.collateralAmount) {
            kLPToSeize = pos.collateralAmount;
        }

        pos.debtAmount = 0;
        totalDebt -= debtToRepay;
        pos.collateralAmount -= kLPToSeize;

        kusd.burnFrom(msg.sender, debtToRepay);
        IERC20(address(vault)).safeTransfer(msg.sender, kLPToSeize);

        emit Liquidated(user, msg.sender, kLPToSeize, debtToRepay);
    }

    /**
     * @notice Checks if a position is healthy based on the default minting threshold.
     */
    function isHealthy(
        address user
    ) public view returns (bool) {
        return isHealthy(user, MINT_COLLATERAL_RATIO);
    }

    /**
     * @notice Checks if a position is healthy based on a specific threshold.
     */
    function isHealthy(address user, uint256 threshold) public view returns (bool) {
        Position memory pos = positions[user];
        if (pos.debtAmount == 0) return true;

        uint256 collateralValue = (pos.collateralAmount * getKLPPrice()) / PRECISION;
        return (collateralValue * 100) / pos.debtAmount >= threshold;
    }

    /**
     * @notice Returns the price of 1 kLP share in USD (18 decimals).
     * @dev Price = totalAssets / totalSupply.
     */
    function getKLPPrice() public view returns (uint256) {
        uint256 _totalAssets = vault.totalAssets();
        uint256 _totalSupply = vault.totalSupply();
        if (_totalSupply == 0) return PRECISION; // Initial price 1:1
        return (_totalAssets * PRECISION) / _totalSupply;
    }

    function pause() external onlyRole(MANAGER_ROLE) {
        _pause();
    }

    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Flash-mints kUSD via the kUSD contract.
     * @param receiver The address to receive the flash-minted kUSD.
     * @param amount The amount of kUSD to flash-mint.
     * @param data Arbitrary data to pass to the receiver's callback.
     */
    function flashMint(address receiver, uint256 amount, bytes calldata data) external nonReentrant whenNotPaused {
        kusd.flashMint(receiver, amount, data);
    }

    /**
     * @notice Returns the health factor of a user (18 decimals).
     * @dev Health Factor = (Collateral Value * 100) / (Debt * LIQUIDATION_THRESHOLD).
     * A health factor > 1e18 means the position is safe from liquidation.
     */
    function getHealthFactor(
        address user
    ) public view returns (uint256) {
        Position memory pos = positions[user];
        if (pos.debtAmount == 0) return 2e18; // Very healthy

        uint256 collateralValue = (pos.collateralAmount * getKLPPrice()) / PRECISION;
        return (collateralValue * 100 * PRECISION) / (pos.debtAmount * LIQUIDATION_THRESHOLD);
    }

    /**
     * @notice Callback for flash-minting. Used for recursive leverage.
     */
    function onFlashMint(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external returns (bytes32) {
        require(msg.sender == address(kusd), "Only kUSD");
        require(initiator == address(this), "Only self-initiated");

        // Decode data: user address, swap data, etc.
        (address user, uint256 minKLPOut) = abi.decode(data, (address, uint256));

        // 1. The kUSD is already in this contract (receiver)
        // 2. Swap kUSD for WETH (Vault Asset)
        // In production, this would call a DEX. For now, we simulate the swap
        // by assuming 1 kUSD = 1 USD and using the Vault's asset price.
        uint256 wethAmount = amount; // Simplified 1:1 for simulation

        // 3. Deposit into Vault
        IERC20 weth = IERC20(vault.asset());
        weth.approve(address(vault), wethAmount);
        uint256 kLPMinted = vault.deposit(wethAmount, address(this));
        require(kLPMinted >= minKLPOut, "Slippage too high");

        // 4. Update user position
        positions[user].collateralAmount += kLPMinted;
        positions[user].debtAmount += (amount + fee);
        totalDebt += (amount + fee);

        require(isHealthy(user), "Position unhealthy after folding");

        // 5. Approve kUSD for repayment
        kusd.approve(address(kusd), amount + fee);

        return keccak256("ERC3156FlashBorrower.onFlashMint");
    }

    /**
     * @notice Executes a recursive leverage (folding) strategy in a single transaction.
     * @param amountToBorrow The amount of kUSD to flash-mint for leverage.
     * @param minKLPOut Minimum kLP to receive from the fold (slippage).
     */
    function fold(uint256 amountToBorrow, uint256 minKLPOut) external nonReentrant whenNotPaused {
        require(amountToBorrow > 0, "Invalid borrow amount");

        bytes memory data = abi.encode(msg.sender, minKLPOut);
        kusd.flashMint(address(this), amountToBorrow, data);

        // Hardening: Ensure health factor is well above liquidation threshold after folding
        // 1.1e18 health factor means 10% buffer above the 120% liquidation threshold (i.e., 132% CR)
        require(getHealthFactor(msg.sender) >= 1.1e18, "Health factor too low after fold");

        emit Leveraged(msg.sender, 0, 0, amountToBorrow);
    }

    /**
     * @notice Allows the protocol to partially deleverage a position if it nears liquidation.
     * @dev Can be called by MANAGER_ROLE to protect the protocol and user from full liquidation.
     * @param user The address of the user to rebalance.
     * @param kLPToRedeem The amount of kLP to redeem and use to repay debt.
     */
    function rebalance(address user, uint256 kLPToRedeem) external onlyRole(MANAGER_ROLE) nonReentrant {
        require(getHealthFactor(user) < 1.3e18, "Position too healthy for rebalance");

        Position storage pos = positions[user];
        require(pos.collateralAmount >= kLPToRedeem, "Insufficient collateral");

        // 1. Redeem kLP for WETH
        uint256 wethReceived = vault.redeem(kLPToRedeem, address(this), address(this));

        // 2. Swap WETH for kUSD (Simulated 1:1)
        uint256 kusdToRepay = wethReceived;
        if (kusdToRepay > pos.debtAmount) kusdToRepay = pos.debtAmount;

        // 3. Repay debt
        pos.debtAmount -= kusdToRepay;
        totalDebt -= kusdToRepay;
        pos.collateralAmount -= kLPToRedeem;

        // In production, the swap would provide the kUSD. For now, we assume the contract has it or burns it.
        // kusd.burn(kusdToRepay);

        emit Burned(user, kLPToRedeem, kusdToRepay);
    }
}
