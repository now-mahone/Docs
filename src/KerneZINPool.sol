// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";

/**
 * @title KerneZINPool
 * @notice Zero-Fee Intent Network Pool - Aggregates liquidity from multiple sources for intent fulfillment.
 * @dev This is the core liquidity pool for ZIN, aggregating vaults, PSM, and external liquidity.
 */
contract KerneZINPool is AccessControl, ReentrancyGuard, IERC3156FlashLender {
    using SafeERC20 for IERC20;

    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");
    bytes32 public constant SOLVER_ROLE = keccak256("SOLVER_ROLE");

    // Supported tokens
    mapping(address => bool) public supportedTokens;

    // Liquidity sources
    struct LiquiditySource {
        address source;
        uint256 priority; // Lower = higher priority
        bool enabled;
    }
    mapping(address => LiquiditySource[]) public liquiditySources; // token -> sources

    // Fee capture
    uint256 public zinFeeBps = 30; // 0.30% spread capture
    address public profitRecipient;

    // Statistics
    mapping(address => uint256) public totalVolumeFilled; // token -> volume
    mapping(address => uint256) public totalProfitCaptured; // token -> profit
    uint256 public totalOrdersFilled;

    // Events
    event LiquiditySourceAdded(address indexed token, address indexed source, uint256 priority);
    event LiquiditySourceRemoved(address indexed token, address indexed source);
    event LiquiditySourceToggled(address indexed token, address indexed source, bool enabled);
    event IntentFilled(address indexed user, address tokenIn, address tokenOut, uint256 amount, uint256 profit);
    event ProfitCaptured(address indexed token, uint256 amount);
    event ZinFeeUpdated(uint256 oldFee, uint256 newFee);
    event ProfitRecipientUpdated(address indexed oldRecipient, address indexed newRecipient);

    constructor(address admin, address _profitRecipient) {
        _grantRole(DEFAULT_ADMIN_ROLE, admin);
        _grantRole(MANAGER_ROLE, admin);
        _grantRole(SOLVER_ROLE, admin);
        profitRecipient = _profitRecipient;
    }

    /**
     * @notice Adds a liquidity source for a specific token.
     * @param token The token address.
     * @param source The liquidity source address (vault, PSM, etc.).
     * @param priority Priority for this source (lower = higher priority).
     */
    function addLiquiditySource(
        address token,
        address source,
        uint256 priority
    ) external onlyRole(MANAGER_ROLE) {
        require(supportedTokens[token], "Token not supported");
        require(source != address(0), "Invalid source");

        liquiditySources[token].push(LiquiditySource({
            source: source,
            priority: priority,
            enabled: true
        }));

        emit LiquiditySourceAdded(token, source, priority);
    }

    /**
     * @notice Removes a liquidity source.
     */
    function removeLiquiditySource(address token, address source) external onlyRole(MANAGER_ROLE) {
        LiquiditySource[] storage sources = liquiditySources[token];
        for (uint256 i = 0; i < sources.length; i++) {
            if (sources[i].source == source) {
                sources[i] = sources[sources.length - 1];
                sources.pop();
                emit LiquiditySourceRemoved(token, source);
                return;
            }
        }
        revert("Source not found");
    }

    /**
     * @notice Toggles a liquidity source on/off.
     */
    function toggleLiquiditySource(
        address token,
        address source,
        bool enabled
    ) external onlyRole(MANAGER_ROLE) {
        LiquiditySource[] storage sources = liquiditySources[token];
        for (uint256 i = 0; i < sources.length; i++) {
            if (sources[i].source == source) {
                sources[i].enabled = enabled;
                emit LiquiditySourceToggled(token, source, enabled);
                return;
            }
        }
        revert("Source not found");
    }

    /**
     * @notice Gets the available liquidity for a token from all enabled sources.
     */
    function getAvailableLiquidity(address token) external view returns (uint256) {
        if (!supportedTokens[token]) return 0;

        uint256 totalLiquidity = IERC20(token).balanceOf(address(this));

        LiquiditySource[] storage sources = liquiditySources[token];
        for (uint256 i = 0; i < sources.length; i++) {
            if (sources[i].enabled) {
                totalLiquidity += IERC20(token).balanceOf(sources[i].source);
            }
        }

        return totalLiquidity;
    }

    /**
     * @notice Supports a token for ZIN operations.
     */
    function supportToken(address token) external onlyRole(MANAGER_ROLE) {
        require(token != address(0), "Invalid token");
        supportedTokens[token] = true;
    }

    /**
     * @notice Internal function to fill an intent using pool liquidity.
     * @param tokenIn The input token.
     * @param tokenOut The output token.
     * @param amount The amount of tokenOut to provide.
     * @param user The user receiving the tokens.
     * @return profit The profit captured (if any).
     */
    function fillIntentInternal(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        address user
    ) external onlyRole(SOLVER_ROLE) nonReentrant returns (uint256) {
        require(supportedTokens[tokenIn] && supportedTokens[tokenOut], "Tokens not supported");

        // 1. Send tokenOut to user
        IERC20(tokenOut).safeTransfer(user, amount);

        // 2. Capture profit if tokenIn != tokenOut (arbitrage opportunity)
        uint256 profit = 0;
        if (tokenIn != tokenOut) {
            uint256 tokenInBalance = IERC20(tokenIn).balanceOf(address(this));
            if (tokenInBalance > 0) {
                // Calculate profit based on spread
                profit = (tokenInBalance * zinFeeBps) / 10000;
                if (profit > 0) {
                    uint256 remaining = tokenInBalance - profit;
                    IERC20(tokenIn).safeTransfer(profitRecipient, profit);
                    totalProfitCaptured[tokenIn] += profit;
                    emit ProfitCaptured(tokenIn, profit);
                }
            }
        }

        // 3. Update statistics
        totalVolumeFilled[tokenOut] += amount;
        totalOrdersFilled++;

        emit IntentFilled(user, tokenIn, tokenOut, amount, profit);

        return profit;
    }

    /**
     * @notice Withdraws profit to the recipient.
     */
    function withdrawProfit(address token) external onlyRole(MANAGER_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance > 0) {
            IERC20(token).safeTransfer(profitRecipient, balance);
        }
    }

    /**
     * @notice Sets the ZIN fee basis points.
     */
    function setZinFee(uint256 bps) external onlyRole(MANAGER_ROLE) {
        require(bps <= 100, "Fee too high");
        uint256 oldFee = zinFeeBps;
        zinFeeBps = bps;
        emit ZinFeeUpdated(oldFee, zinFeeBps);
    }

    /**
     * @notice Sets the profit recipient.
     */
    function setProfitRecipient(address recipient) external onlyRole(DEFAULT_ADMIN_ROLE) {
        address oldRecipient = profitRecipient;
        profitRecipient = recipient;
        emit ProfitRecipientUpdated(oldRecipient, recipient);
    }

    // --- IERC3156FlashLender Implementation ---

    function maxFlashLoan(address token) external view override returns (uint256) {
        if (!supportedTokens[token]) return 0;
        uint256 poolBalance = IERC20(token).balanceOf(address(this));
        
        // Add liquidity from enabled sources
        LiquiditySource[] storage sources = liquiditySources[token];
        for (uint256 i = 0; i < sources.length; i++) {
            if (sources[i].enabled) {
                poolBalance += IERC20(token).balanceOf(sources[i].source);
            }
        }
        
        return poolBalance;
    }

    function flashFee(address token, uint256 amount) public view override returns (uint256) {
        require(supportedTokens[token], "Unsupported token");
        // Zero fee for ZIN solvers
        if (hasRole(SOLVER_ROLE, msg.sender)) return 0;
        return (amount * zinFeeBps) / 10000;
    }

    function flashLoan(
        IERC3156FlashBorrower receiver,
        address token,
        uint256 amount,
        bytes calldata data
    ) external override nonReentrant returns (bool) {
        require(supportedTokens[token], "Unsupported token");
        uint256 fee = flashFee(token, amount);

        IERC20(token).safeTransfer(address(receiver), amount);

        require(
            receiver.onFlashLoan(msg.sender, token, amount, fee, data) == keccak256("ERC3156FlashBorrower.onFlashLoan"),
            "Flash loan callback failed"
        );

        IERC20(token).safeTransferFrom(address(receiver), address(this), amount + fee);

        // Capture fee as profit
        if (fee > 0 && profitRecipient != address(0)) {
            IERC20(token).safeTransfer(profitRecipient, fee);
            totalProfitCaptured[token] += fee;
            emit ProfitCaptured(token, fee);
        }

        return true;
    }

    /**
     * @notice Recovers tokens from the pool.
     */
    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(profitRecipient, balance);
    }

    receive() external payable {}
}
