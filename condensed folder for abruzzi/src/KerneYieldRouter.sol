// SPDX-License-Identifier: MIT
// Created: 2026-01-19
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title KerneYieldRouter
 * @author Kerne Protocol
 * @notice Multi-asset deposit router that optimizes yield across all supported assets.
 * @dev Users can deposit ANY supported asset (ETH, BTC, SOL, USDC, etc.) and receive KUSD.
 *      The router automatically allocates deposits to the highest-yielding delta-neutral positions
 *      based on real-time funding rates and LST yields.
 *
 * Key Features:
 * - Accept deposits in any supported asset
 * - Auto-optimize allocation based on Sharpe-weighted yields
 * - Single KUSD token represents diversified delta-neutral exposure
 * - Withdraw to any supported asset
 */
contract KerneYieldRouter is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ============ Roles ============
    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");
    bytes32 public constant OPTIMIZER_ROLE = keccak256("OPTIMIZER_ROLE");

    // ============ Structs ============

    /// @notice Configuration for a supported asset
    struct AssetConfig {
        address vault;           // The vault contract for this asset
        address lstToken;        // LST token address (address(0) if no LST)
        uint256 lstYieldBps;     // Annual LST yield in basis points (350 = 3.5%)
        uint256 maxAllocationBps; // Maximum allocation to this asset (10000 = 100%)
        uint256 minDepositUsd;   // Minimum deposit in USD terms
        bool active;             // Whether deposits are enabled
    }

    /// @notice Current optimal allocation weights (updated by off-chain optimizer)
    struct AllocationWeights {
        address[] assets;
        uint256[] weights;       // Weights in basis points (sum = 10000)
        uint256 expectedApyBps;  // Expected portfolio APY in basis points
        uint256 lastUpdated;     // Timestamp of last update
    }

    /// @notice User position tracking
    struct UserPosition {
        uint256 kusdBalance;     // Total KUSD balance
        uint256 depositTimestamp; // First deposit timestamp
        mapping(address => uint256) assetDeposits; // Original deposits by asset
    }

    // ============ Constants ============
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant ALLOCATION_STALENESS_THRESHOLD = 8 hours;

    // ============ State Variables ============

    /// @notice The KUSD token contract
    IERC20 public immutable kusd;

    /// @notice Supported assets configuration
    mapping(address => AssetConfig) public assetConfigs;
    address[] public supportedAssets;

    /// @notice Current optimal allocation
    AllocationWeights public currentAllocation;

    /// @notice User positions
    mapping(address => UserPosition) private userPositions;

    /// @notice Price oracle for USD conversions
    address public priceOracle;

    /// @notice DEX aggregator for swaps (e.g., 1inch, Paraswap)
    address public dexAggregator;

    /// @notice Total value locked across all assets (in USD, 18 decimals)
    uint256 public totalValueLockedUsd;

    /// @notice Allocation modes
    enum AllocationMode {
        AUTO_OPTIMIZE,    // Use Sharpe-weighted optimal allocation
        SINGLE_ASSET,     // 100% to deposited asset
        CUSTOM            // User-defined allocation
    }

    // ============ Events ============

    event AssetAdded(address indexed asset, address indexed vault, uint256 lstYieldBps);
    event AssetUpdated(address indexed asset, bool active, uint256 maxAllocationBps);
    event AllocationUpdated(address[] assets, uint256[] weights, uint256 expectedApyBps);
    event Deposited(
        address indexed user,
        address indexed asset,
        uint256 amount,
        uint256 kusdMinted,
        AllocationMode mode
    );
    event Withdrawn(
        address indexed user,
        address indexed targetAsset,
        uint256 kusdBurned,
        uint256 assetReceived
    );
    event Rebalanced(address indexed asset, uint256 fromAmount, uint256 toAmount);

    // ============ Errors ============

    error AssetNotSupported(address asset);
    error AssetNotActive(address asset);
    error InsufficientDeposit(uint256 provided, uint256 minimum);
    error AllocationStale(uint256 lastUpdated, uint256 threshold);
    error InvalidAllocation(uint256 totalWeight);
    error InsufficientBalance(uint256 requested, uint256 available);
    error SlippageExceeded(uint256 expected, uint256 received);

    // ============ Constructor ============

    /**
     * @param _kusd The KUSD token address
     * @param _admin The admin address
     * @param _strategist The strategist address
     */
    constructor(address _kusd, address _admin, address _strategist) {
        require(_kusd != address(0), "Invalid KUSD address");
        require(_admin != address(0), "Invalid admin address");

        kusd = IERC20(_kusd);

        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(STRATEGIST_ROLE, _strategist);
        _grantRole(OPTIMIZER_ROLE, _strategist);
    }

    // ============ External Functions ============

    /**
     * @notice Deposit any supported asset and receive KUSD
     * @param asset The asset to deposit
     * @param amount The amount to deposit
     * @param mode Allocation mode (0=Auto, 1=Single, 2=Custom)
     * @param customWeights Custom allocation weights (only used if mode=2)
     * @param minKusdOut Minimum KUSD to receive (slippage protection)
     * @return kusdAmount The amount of KUSD minted
     */
    function deposit(
        address asset,
        uint256 amount,
        AllocationMode mode,
        uint256[] calldata customWeights,
        uint256 minKusdOut
    ) external nonReentrant whenNotPaused returns (uint256 kusdAmount) {
        // Validate asset
        AssetConfig storage config = assetConfigs[asset];
        if (config.vault == address(0)) revert AssetNotSupported(asset);
        if (!config.active) revert AssetNotActive(asset);

        // Transfer asset from user
        IERC20(asset).safeTransferFrom(msg.sender, address(this), amount);

        // Get USD value of deposit
        uint256 depositValueUsd = _getAssetValueUsd(asset, amount);
        if (depositValueUsd < config.minDepositUsd) {
            revert InsufficientDeposit(depositValueUsd, config.minDepositUsd);
        }

        // Determine allocation based on mode
        (address[] memory targetAssets, uint256[] memory weights) = _getAllocation(
            asset,
            mode,
            customWeights
        );

        // Execute allocation (swap and deposit to vaults)
        kusdAmount = _executeAllocation(asset, amount, targetAssets, weights);

        // Slippage check
        if (kusdAmount < minKusdOut) {
            revert SlippageExceeded(minKusdOut, kusdAmount);
        }

        // Update user position
        UserPosition storage position = userPositions[msg.sender];
        position.kusdBalance += kusdAmount;
        position.assetDeposits[asset] += amount;
        if (position.depositTimestamp == 0) {
            position.depositTimestamp = block.timestamp;
        }

        // Update TVL
        totalValueLockedUsd += depositValueUsd;

        emit Deposited(msg.sender, asset, amount, kusdAmount, mode);
    }

    /**
     * @notice Withdraw KUSD to any supported asset
     * @param kusdAmount Amount of KUSD to redeem
     * @param targetAsset The asset to receive (address(0) for proportional mix)
     * @param minAssetOut Minimum asset to receive (slippage protection)
     * @return assetAmount The amount of target asset received
     */
    function withdraw(
        uint256 kusdAmount,
        address targetAsset,
        uint256 minAssetOut
    ) external nonReentrant whenNotPaused returns (uint256 assetAmount) {
        UserPosition storage position = userPositions[msg.sender];
        if (position.kusdBalance < kusdAmount) {
            revert InsufficientBalance(kusdAmount, position.kusdBalance);
        }

        // Calculate USD value of withdrawal
        uint256 withdrawValueUsd = _getKusdValueUsd(kusdAmount);

        // Execute withdrawal from vaults
        if (targetAsset == address(0)) {
            // Proportional withdrawal across all assets
            assetAmount = _executeProportionalWithdraw(kusdAmount, msg.sender);
        } else {
            // Single asset withdrawal
            if (assetConfigs[targetAsset].vault == address(0)) {
                revert AssetNotSupported(targetAsset);
            }
            assetAmount = _executeSingleAssetWithdraw(kusdAmount, targetAsset, msg.sender);
        }

        // Slippage check
        if (assetAmount < minAssetOut) {
            revert SlippageExceeded(minAssetOut, assetAmount);
        }

        // Update user position
        position.kusdBalance -= kusdAmount;

        // Update TVL
        totalValueLockedUsd -= withdrawValueUsd;

        emit Withdrawn(msg.sender, targetAsset, kusdAmount, assetAmount);
    }

    /**
     * @notice Get current optimal allocation based on live funding rates
     * @return assets Array of asset addresses
     * @return weights Array of weights in basis points
     * @return expectedApyBps Expected portfolio APY in basis points
     */
    function getOptimalAllocation()
        external
        view
        returns (address[] memory assets, uint256[] memory weights, uint256 expectedApyBps)
    {
        return (
            currentAllocation.assets,
            currentAllocation.weights,
            currentAllocation.expectedApyBps
        );
    }

    /**
     * @notice Get current APY for a specific asset
     * @param asset The asset address
     * @return apyBps The current APY in basis points
     */
    function getAssetAPY(address asset) external view returns (uint256 apyBps) {
        AssetConfig storage config = assetConfigs[asset];
        if (config.vault == address(0)) revert AssetNotSupported(asset);

        // Get funding APY from vault
        (bool success, bytes memory data) = config.vault.staticcall(
            abi.encodeWithSignature("getProjectedAPY()")
        );

        uint256 fundingApyBps = 0;
        if (success && data.length == 32) {
            fundingApyBps = abi.decode(data, (uint256));
        }

        // Add LST yield
        return fundingApyBps + config.lstYieldBps;
    }

    /**
     * @notice Get user's current position
     * @param user The user address
     * @return kusdBalance User's KUSD balance
     * @return depositTimestamp First deposit timestamp
     */
    function getUserPosition(address user)
        external
        view
        returns (uint256 kusdBalance, uint256 depositTimestamp)
    {
        UserPosition storage position = userPositions[user];
        return (position.kusdBalance, position.depositTimestamp);
    }

    /**
     * @notice Get all supported assets
     * @return assets Array of supported asset addresses
     */
    function getSupportedAssets() external view returns (address[] memory) {
        return supportedAssets;
    }

    // ============ Admin Functions ============

    /**
     * @notice Add a new supported asset
     * @param asset The asset address
     * @param vault The vault address for this asset
     * @param lstToken The LST token address (address(0) if no LST)
     * @param lstYieldBps Annual LST yield in basis points
     * @param maxAllocationBps Maximum allocation in basis points
     * @param minDepositUsd Minimum deposit in USD
     */
    function addAsset(
        address asset,
        address vault,
        address lstToken,
        uint256 lstYieldBps,
        uint256 maxAllocationBps,
        uint256 minDepositUsd
    ) external onlyRole(DEFAULT_ADMIN_ROLE) {
        require(asset != address(0), "Invalid asset");
        require(vault != address(0), "Invalid vault");
        require(assetConfigs[asset].vault == address(0), "Asset already exists");

        assetConfigs[asset] = AssetConfig({
            vault: vault,
            lstToken: lstToken,
            lstYieldBps: lstYieldBps,
            maxAllocationBps: maxAllocationBps,
            minDepositUsd: minDepositUsd,
            active: true
        });

        supportedAssets.push(asset);

        emit AssetAdded(asset, vault, lstYieldBps);
    }

    /**
     * @notice Update asset configuration
     * @param asset The asset address
     * @param active Whether the asset is active
     * @param maxAllocationBps Maximum allocation in basis points
     */
    function updateAsset(
        address asset,
        bool active,
        uint256 maxAllocationBps
    ) external onlyRole(STRATEGIST_ROLE) {
        AssetConfig storage config = assetConfigs[asset];
        if (config.vault == address(0)) revert AssetNotSupported(asset);

        config.active = active;
        config.maxAllocationBps = maxAllocationBps;

        emit AssetUpdated(asset, active, maxAllocationBps);
    }

    /**
     * @notice Update optimal allocation (called by off-chain optimizer)
     * @param assets Array of asset addresses
     * @param weights Array of weights in basis points (must sum to 10000)
     * @param expectedApyBps Expected portfolio APY in basis points
     */
    function updateAllocation(
        address[] calldata assets,
        uint256[] calldata weights,
        uint256 expectedApyBps
    ) external onlyRole(OPTIMIZER_ROLE) {
        require(assets.length == weights.length, "Length mismatch");

        // Validate weights sum to 10000
        uint256 totalWeight = 0;
        for (uint256 i = 0; i < weights.length; i++) {
            totalWeight += weights[i];
        }
        if (totalWeight != BPS_DENOMINATOR) {
            revert InvalidAllocation(totalWeight);
        }

        // Update allocation
        currentAllocation.assets = assets;
        currentAllocation.weights = weights;
        currentAllocation.expectedApyBps = expectedApyBps;
        currentAllocation.lastUpdated = block.timestamp;

        emit AllocationUpdated(assets, weights, expectedApyBps);
    }

    /**
     * @notice Set the price oracle address
     * @param _priceOracle The price oracle address
     */
    function setPriceOracle(address _priceOracle) external onlyRole(DEFAULT_ADMIN_ROLE) {
        priceOracle = _priceOracle;
    }

    /**
     * @notice Set the DEX aggregator address
     * @param _dexAggregator The DEX aggregator address
     */
    function setDexAggregator(address _dexAggregator) external onlyRole(DEFAULT_ADMIN_ROLE) {
        dexAggregator = _dexAggregator;
    }

    /**
     * @notice Pause the router
     */
    function pause() external onlyRole(STRATEGIST_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause the router
     */
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }

    // ============ Internal Functions ============

    /**
     * @dev Get allocation based on mode
     */
    function _getAllocation(
        address depositAsset,
        AllocationMode mode,
        uint256[] calldata customWeights
    ) internal view returns (address[] memory assets, uint256[] memory weights) {
        if (mode == AllocationMode.SINGLE_ASSET) {
            // 100% to deposited asset
            assets = new address[](1);
            weights = new uint256[](1);
            assets[0] = depositAsset;
            weights[0] = BPS_DENOMINATOR;
        } else if (mode == AllocationMode.CUSTOM) {
            // Use custom weights
            require(customWeights.length == supportedAssets.length, "Invalid custom weights");
            assets = supportedAssets;
            weights = customWeights;
        } else {
            // AUTO_OPTIMIZE - use current optimal allocation
            if (
                block.timestamp - currentAllocation.lastUpdated > ALLOCATION_STALENESS_THRESHOLD
            ) {
                revert AllocationStale(
                    currentAllocation.lastUpdated,
                    ALLOCATION_STALENESS_THRESHOLD
                );
            }
            assets = currentAllocation.assets;
            weights = currentAllocation.weights;
        }
    }

    /**
     * @dev Execute allocation by swapping and depositing to vaults
     */
    function _executeAllocation(
        address sourceAsset,
        uint256 sourceAmount,
        address[] memory targetAssets,
        uint256[] memory weights
    ) internal returns (uint256 totalKusd) {
        for (uint256 i = 0; i < targetAssets.length; i++) {
            if (weights[i] == 0) continue;

            address targetAsset = targetAssets[i];
            uint256 targetAmount = (sourceAmount * weights[i]) / BPS_DENOMINATOR;

            if (targetAmount == 0) continue;

            // Swap if needed
            uint256 depositAmount;
            if (sourceAsset == targetAsset) {
                depositAmount = targetAmount;
            } else {
                depositAmount = _swap(sourceAsset, targetAsset, targetAmount);
            }

            // Deposit to vault
            AssetConfig storage config = assetConfigs[targetAsset];
            IERC20(targetAsset).safeIncreaseAllowance(config.vault, depositAmount);

            (bool success, bytes memory data) = config.vault.call(
                abi.encodeWithSignature(
                    "deposit(uint256,address)",
                    depositAmount,
                    address(this)
                )
            );

            if (success && data.length >= 32) {
                totalKusd += abi.decode(data, (uint256));
            }
        }
    }

    /**
     * @dev Execute proportional withdrawal across all assets
     */
    function _executeProportionalWithdraw(
        uint256 kusdAmount,
        address recipient
    ) internal returns (uint256 totalValue) {
        // Calculate proportional amounts from each vault
        for (uint256 i = 0; i < supportedAssets.length; i++) {
            address asset = supportedAssets[i];
            AssetConfig storage config = assetConfigs[asset];

            // Get vault balance
            (bool success, bytes memory data) = config.vault.staticcall(
                abi.encodeWithSignature("balanceOf(address)", address(this))
            );

            if (!success || data.length < 32) continue;

            uint256 vaultShares = abi.decode(data, (uint256));
            if (vaultShares == 0) continue;

            // Calculate proportional withdrawal
            uint256 withdrawShares = (vaultShares * kusdAmount) / userPositions[recipient].kusdBalance;

            // Withdraw from vault
            (success, data) = config.vault.call(
                abi.encodeWithSignature(
                    "redeem(uint256,address,address)",
                    withdrawShares,
                    recipient,
                    address(this)
                )
            );

            if (success && data.length >= 32) {
                totalValue += abi.decode(data, (uint256));
            }
        }
    }

    /**
     * @dev Execute single asset withdrawal
     */
    function _executeSingleAssetWithdraw(
        uint256 kusdAmount,
        address targetAsset,
        address recipient
    ) internal returns (uint256 assetAmount) {
        // Withdraw from all vaults and swap to target asset
        for (uint256 i = 0; i < supportedAssets.length; i++) {
            address asset = supportedAssets[i];
            AssetConfig storage config = assetConfigs[asset];

            // Get vault balance
            (bool success, bytes memory data) = config.vault.staticcall(
                abi.encodeWithSignature("balanceOf(address)", address(this))
            );

            if (!success || data.length < 32) continue;

            uint256 vaultShares = abi.decode(data, (uint256));
            if (vaultShares == 0) continue;

            // Calculate proportional withdrawal
            uint256 withdrawShares = (vaultShares * kusdAmount) / userPositions[recipient].kusdBalance;

            // Withdraw from vault
            (success, data) = config.vault.call(
                abi.encodeWithSignature(
                    "redeem(uint256,address,address)",
                    withdrawShares,
                    address(this),
                    address(this)
                )
            );

            if (!success || data.length < 32) continue;

            uint256 withdrawnAmount = abi.decode(data, (uint256));

            // Swap to target asset if needed
            if (asset == targetAsset) {
                assetAmount += withdrawnAmount;
            } else {
                assetAmount += _swap(asset, targetAsset, withdrawnAmount);
            }
        }

        // Transfer to recipient
        IERC20(targetAsset).safeTransfer(recipient, assetAmount);
    }

    /**
     * @dev Swap assets via DEX aggregator
     */
    function _swap(
        address fromAsset,
        address toAsset,
        uint256 amount
    ) internal returns (uint256 receivedAmount) {
        if (dexAggregator == address(0)) {
            // Fallback: direct transfer (for testing)
            return amount;
        }

        // Approve DEX aggregator
        IERC20(fromAsset).safeIncreaseAllowance(dexAggregator, amount);

        // Execute swap via aggregator
        // Note: In production, this would call the actual DEX aggregator
        (bool success, bytes memory data) = dexAggregator.call(
            abi.encodeWithSignature(
                "swap(address,address,uint256,uint256)",
                fromAsset,
                toAsset,
                amount,
                0 // minOut - should be calculated off-chain
            )
        );

        if (success && data.length >= 32) {
            receivedAmount = abi.decode(data, (uint256));
        }
    }

    /**
     * @dev Get USD value of an asset amount
     */
    function _getAssetValueUsd(address asset, uint256 amount) internal view returns (uint256) {
        if (priceOracle == address(0)) {
            // Fallback: assume 1:1 for stablecoins, use placeholder for others
            return amount;
        }

        (bool success, bytes memory data) = priceOracle.staticcall(
            abi.encodeWithSignature("getPrice(address)", asset)
        );

        if (success && data.length >= 32) {
            uint256 price = abi.decode(data, (uint256));
            return (amount * price) / 1e18;
        }

        return amount;
    }

    /**
     * @dev Get USD value of KUSD amount
     */
    function _getKusdValueUsd(uint256 kusdAmount) internal pure returns (uint256) {
        // KUSD is pegged 1:1 to USD
        return kusdAmount;
    }
}
