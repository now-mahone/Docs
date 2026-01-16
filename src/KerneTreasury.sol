// Created: 2026-01-04
// Updated: 2026-01-14 - Implemented Aerodrome buyback swap logic
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/utils/Pausable.sol";
import "./interfaces/IAerodromeRouter.sol";

/**
 * @title KerneTreasury
 * @notice Handles automated wealth extraction, founder payouts, and $KERNE buybacks via Aerodrome.
 * @dev Routes 80% of performance fees to the founder and 20% to $KERNE buyback/staking.
 *      Buybacks create constant buy pressure on KERNE, driving token appreciation.
 * 
 * Fee Flow:
 *   Vault Fees → Treasury → 80% Founder | 20% Buyback → KERNE purchased → Staking Rewards
 * 
 * The buyback flywheel:
 *   Higher TVL → More Fees → More Buybacks → Token Appreciation → More TVL
 */
contract KerneTreasury is Ownable, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTANTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    uint256 public constant FOUNDER_SHARE = 8000;      // 80%
    uint256 public constant BUYBACK_SHARE = 2000;      // 20%
    uint256 public constant BPS_DENOMINATOR = 10000;
    uint256 public constant MAX_SLIPPAGE = 500;         // 5% max slippage
    uint256 public constant MIN_BUYBACK_AMOUNT = 1e18;  // Minimum 1 token worth for buyback
    uint256 public constant SWAP_DEADLINE_BUFFER = 300; // 5 minute deadline buffer

    // ═══════════════════════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════════════════════

    /// @notice Founder address receiving 80% of fees
    address public founder;
    
    /// @notice KERNE token address - target of buybacks
    address public kerneToken;
    
    /// @notice Staking contract where bought KERNE is sent
    address public stakingContract;
    
    /// @notice Aerodrome Router V2 on Base
    /// @dev Mainnet: 0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43
    IAerodromeRouter public aerodromeRouter;
    
    /// @notice Default factory for pool lookups
    address public aerodromeFactory;
    
    /// @notice Whether KERNE pool is stable (usually false for governance tokens)
    bool public useStablePool;
    
    /// @notice Slippage tolerance in basis points (default 100 = 1%)
    uint256 public slippageBps;
    
    /// @notice Total KERNE bought back via this contract
    uint256 public totalKerneBought;
    
    /// @notice Total value spent on buybacks (in input token terms)
    uint256 public totalBuybackSpent;
    
    /// @notice Mapping of approved buyback tokens (WETH, kUSD, USDC, etc.)
    mapping(address => bool) public approvedBuybackTokens;
    
    /// @notice Mapping of token to intermediate hop (for routing through deeper liquidity)
    /// @dev e.g., USDC → WETH → KERNE if USDC/KERNE pool is thin
    mapping(address => address) public routingHops;

    // ═══════════════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════════════

    event FeesDistributed(address indexed token, uint256 founderAmount, uint256 buybackAmount);
    event FounderUpdated(address indexed oldFounder, address indexed newFounder);
    event BuybackExecuted(
        address indexed inputToken,
        uint256 amountIn,
        uint256 kerneReceived,
        address indexed destination
    );
    event BuybackTokenApproved(address indexed token, bool approved);
    event RouterUpdated(address indexed oldRouter, address indexed newRouter);
    event SlippageUpdated(uint256 oldSlippage, uint256 newSlippage);
    event RoutingHopSet(address indexed token, address indexed hop);
    event StakingContractUpdated(address indexed oldStaking, address indexed newStaking);
    event EmergencyWithdraw(address indexed token, uint256 amount, address indexed to);

    // ═══════════════════════════════════════════════════════════════════════════════
    // ERRORS
    // ═══════════════════════════════════════════════════════════════════════════════

    error ZeroAddress();
    error ZeroAmount();
    error InsufficientBalance();
    error TokenNotApproved();
    error SlippageTooHigh();
    error BuybackTooSmall();
    error SwapFailed();
    error Unauthorized();

    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Initializes the Treasury with core addresses
     * @param _founder Address receiving founder share of fees
     * @param _kerneToken KERNE token address (buyback target)
     * @param _stakingContract Address where bought KERNE is sent
     * @param _aerodromeRouter Aerodrome Router V2 address
     */
    constructor(
        address _founder,
        address _kerneToken,
        address _stakingContract,
        address _aerodromeRouter
    ) Ownable(msg.sender) {
        if (_founder == address(0)) revert ZeroAddress();
        if (_kerneToken == address(0)) revert ZeroAddress();
        if (_stakingContract == address(0)) revert ZeroAddress();
        if (_aerodromeRouter == address(0)) revert ZeroAddress();

        founder = _founder;
        kerneToken = _kerneToken;
        stakingContract = _stakingContract;
        aerodromeRouter = IAerodromeRouter(_aerodromeRouter);
        aerodromeFactory = aerodromeRouter.defaultFactory();
        
        slippageBps = 100; // Default 1% slippage
        useStablePool = false; // KERNE is volatile, not stable
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // CORE FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Distributes accumulated tokens between founder and buyback pool
     * @param token The token to distribute (usually WETH or kUSD)
     * @dev 80% goes to founder, 20% held for buyback execution
     */
    function distribute(address token) external nonReentrant whenNotPaused {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance == 0) revert InsufficientBalance();

        uint256 founderAmount = (balance * FOUNDER_SHARE) / BPS_DENOMINATOR;
        uint256 buybackAmount = balance - founderAmount;

        // Transfer to founder
        IERC20(token).safeTransfer(founder, founderAmount);

        // Buyback amount stays in treasury for executeBuyback()
        // This allows batching buybacks for better gas efficiency

        emit FeesDistributed(token, founderAmount, buybackAmount);
    }

    /**
     * @notice Distributes and immediately executes buyback in one transaction
     * @param token The token to distribute and swap
     * @param minKerneOut Minimum KERNE to receive (slippage protection)
     * @dev More gas efficient when fees are ready to be processed immediately
     */
    function distributeAndBuyback(
        address token,
        uint256 minKerneOut
    ) external nonReentrant whenNotPaused {
        uint256 balance = IERC20(token).balanceOf(address(this));
        if (balance == 0) revert InsufficientBalance();

        uint256 founderAmount = (balance * FOUNDER_SHARE) / BPS_DENOMINATOR;
        uint256 buybackAmount = balance - founderAmount;

        // Transfer to founder
        IERC20(token).safeTransfer(founder, founderAmount);

        // Execute buyback with remaining funds
        if (buybackAmount >= MIN_BUYBACK_AMOUNT) {
            _executeBuybackInternal(token, buybackAmount, minKerneOut);
        }

        emit FeesDistributed(token, founderAmount, buybackAmount);
    }

    /**
     * @notice Executes a buyback of $KERNE using accumulated fees via Aerodrome
     * @param token Input token to swap for KERNE
     * @param amount Amount of input token to swap
     * @param minKerneOut Minimum KERNE to receive (slippage protection)
     * @dev Only callable by owner to prevent MEV exploitation
     *      The bought KERNE is sent to the staking contract for distribution
     */
    function executeBuyback(
        address token,
        uint256 amount,
        uint256 minKerneOut
    ) external onlyOwner nonReentrant whenNotPaused {
        _executeBuybackInternal(token, amount, minKerneOut);
    }

    /**
     * @notice Internal buyback execution logic
     * @param token Input token
     * @param amount Amount to swap
     * @param minKerneOut Minimum output (0 = use calculated slippage)
     */
    function _executeBuybackInternal(
        address token,
        uint256 amount,
        uint256 minKerneOut
    ) internal {
        if (token == address(0)) revert ZeroAddress();
        if (amount == 0) revert ZeroAmount();
        if (!approvedBuybackTokens[token]) revert TokenNotApproved();
        
        uint256 tokenBalance = IERC20(token).balanceOf(address(this));
        if (tokenBalance < amount) revert InsufficientBalance();
        if (amount < MIN_BUYBACK_AMOUNT) revert BuybackTooSmall();

        // Build route - check if we need intermediate hop
        IAerodromeRouter.Route[] memory routes;
        address hop = routingHops[token];
        
        if (hop != address(0)) {
            // Two-hop route: token → hop → KERNE
            routes = new IAerodromeRouter.Route[](2);
            routes[0] = IAerodromeRouter.Route({
                from: token,
                to: hop,
                stable: _isStablePair(token, hop),
                factory: aerodromeFactory
            });
            routes[1] = IAerodromeRouter.Route({
                from: hop,
                to: kerneToken,
                stable: useStablePool,
                factory: aerodromeFactory
            });
        } else {
            // Direct route: token → KERNE
            routes = new IAerodromeRouter.Route[](1);
            routes[0] = IAerodromeRouter.Route({
                from: token,
                to: kerneToken,
                stable: useStablePool,
                factory: aerodromeFactory
            });
        }

        // Calculate minimum output if not provided
        if (minKerneOut == 0) {
            uint256[] memory expectedAmounts = aerodromeRouter.getAmountsOut(amount, routes);
            uint256 expectedOut = expectedAmounts[expectedAmounts.length - 1];
            minKerneOut = (expectedOut * (BPS_DENOMINATOR - slippageBps)) / BPS_DENOMINATOR;
        }

        // Approve router to spend tokens
        IERC20(token).safeIncreaseAllowance(address(aerodromeRouter), amount);

        // Execute swap
        uint256 kerneBefore = IERC20(kerneToken).balanceOf(address(this));
        
        uint256[] memory amounts = aerodromeRouter.swapExactTokensForTokens(
            amount,
            minKerneOut,
            routes,
            address(this),
            block.timestamp + SWAP_DEADLINE_BUFFER
        );

        uint256 kerneReceived = IERC20(kerneToken).balanceOf(address(this)) - kerneBefore;
        
        if (kerneReceived == 0) revert SwapFailed();

        // Update tracking
        totalKerneBought += kerneReceived;
        totalBuybackSpent += amount;

        // Transfer bought KERNE to staking contract for distribution
        IERC20(kerneToken).safeTransfer(stakingContract, kerneReceived);

        emit BuybackExecuted(token, amount, kerneReceived, stakingContract);
    }

    /**
     * @notice Preview expected KERNE output for a given input
     * @param token Input token
     * @param amount Amount of input token
     * @return expectedKerne Expected KERNE output
     * @return minKerne Minimum KERNE with slippage applied
     */
    function previewBuyback(
        address token,
        uint256 amount
    ) external view returns (uint256 expectedKerne, uint256 minKerne) {
        if (!approvedBuybackTokens[token]) revert TokenNotApproved();

        IAerodromeRouter.Route[] memory routes;
        address hop = routingHops[token];
        
        if (hop != address(0)) {
            routes = new IAerodromeRouter.Route[](2);
            routes[0] = IAerodromeRouter.Route({
                from: token,
                to: hop,
                stable: _isStablePair(token, hop),
                factory: aerodromeFactory
            });
            routes[1] = IAerodromeRouter.Route({
                from: hop,
                to: kerneToken,
                stable: useStablePool,
                factory: aerodromeFactory
            });
        } else {
            routes = new IAerodromeRouter.Route[](1);
            routes[0] = IAerodromeRouter.Route({
                from: token,
                to: kerneToken,
                stable: useStablePool,
                factory: aerodromeFactory
            });
        }

        uint256[] memory amounts = aerodromeRouter.getAmountsOut(amount, routes);
        expectedKerne = amounts[amounts.length - 1];
        minKerne = (expectedKerne * (BPS_DENOMINATOR - slippageBps)) / BPS_DENOMINATOR;
    }

    /**
     * @notice Check if a pair should use stable pool
     * @dev Helper for stablecoin pairs (USDC/USDT, etc.)
     */
    function _isStablePair(address tokenA, address tokenB) internal view returns (bool) {
        // For simplicity, we assume WETH routing is always volatile
        // In production, this could check against a list of stablecoins
        return false;
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Approve a token for buyback swaps
     * @param token Token address to approve/revoke
     * @param approved Whether the token is approved
     */
    function setApprovedBuybackToken(address token, bool approved) external onlyOwner {
        if (token == address(0)) revert ZeroAddress();
        approvedBuybackTokens[token] = approved;
        emit BuybackTokenApproved(token, approved);
    }

    /**
     * @notice Set routing hop for a token (for deeper liquidity)
     * @param token Input token
     * @param hop Intermediate token (address(0) for direct route)
     */
    function setRoutingHop(address token, address hop) external onlyOwner {
        routingHops[token] = hop;
        emit RoutingHopSet(token, hop);
    }

    /**
     * @notice Update slippage tolerance
     * @param newSlippageBps New slippage in basis points
     */
    function setSlippage(uint256 newSlippageBps) external onlyOwner {
        if (newSlippageBps > MAX_SLIPPAGE) revert SlippageTooHigh();
        uint256 oldSlippage = slippageBps;
        slippageBps = newSlippageBps;
        emit SlippageUpdated(oldSlippage, newSlippageBps);
    }

    /**
     * @notice Update KERNE token address
     * @param _kerneToken New KERNE token address
     */
    function setKerneToken(address _kerneToken) external onlyOwner {
        if (_kerneToken == address(0)) revert ZeroAddress();
        address oldToken = kerneToken;
        kerneToken = _kerneToken;
        // No event for this yet, but we could add one
    }

    /**
     * @notice Update Aerodrome router address
     * @param newRouter New router address
     */
    function setRouter(address newRouter) external onlyOwner {
        if (newRouter == address(0)) revert ZeroAddress();
        address oldRouter = address(aerodromeRouter);
        aerodromeRouter = IAerodromeRouter(newRouter);
        aerodromeFactory = aerodromeRouter.defaultFactory();
        emit RouterUpdated(oldRouter, newRouter);
    }

    /**
     * @notice Update staking contract address
     * @param newStaking New staking contract address
     */
    function setStakingContract(address newStaking) external onlyOwner {
        if (newStaking == address(0)) revert ZeroAddress();
        address oldStaking = stakingContract;
        stakingContract = newStaking;
        emit StakingContractUpdated(oldStaking, newStaking);
    }

    /**
     * @notice Update founder address
     * @param newFounder New founder address
     */
    function updateFounder(address newFounder) external {
        if (msg.sender != founder && msg.sender != owner()) revert Unauthorized();
        if (newFounder == address(0)) revert ZeroAddress();
        address oldFounder = founder;
        founder = newFounder;
        emit FounderUpdated(oldFounder, newFounder);
    }

    /**
     * @notice Set pool type for KERNE swaps
     * @param _useStable Whether to use stable pool (usually false)
     */
    function setPoolType(bool _useStable) external onlyOwner {
        useStablePool = _useStable;
    }

    /**
     * @notice Pause contract in emergency
     */
    function pause() external onlyOwner {
        _pause();
    }

    /**
     * @notice Unpause contract
     */
    function unpause() external onlyOwner {
        _unpause();
    }

    /**
     * @notice Emergency withdraw for any stuck tokens
     * @param token Token to withdraw
     */
    function emergencyWithdraw(address token) external onlyOwner {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(owner(), balance);
        emit EmergencyWithdraw(token, balance, owner());
    }

    /**
     * @notice Withdraw ETH if any is stuck
     */
    function emergencyWithdrawETH() external onlyOwner {
        uint256 balance = address(this).balance;
        (bool success, ) = owner().call{value: balance}("");
        require(success, "ETH transfer failed");
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Get current buyback stats
     * @return _totalKerneBought Total KERNE acquired via buybacks
     * @return _totalBuybackSpent Total value spent on buybacks
     */
    function getBuybackStats() external view returns (
        uint256 _totalKerneBought,
        uint256 _totalBuybackSpent
    ) {
        return (totalKerneBought, totalBuybackSpent);
    }

    /**
     * @notice Check if a token is approved for buybacks
     * @param token Token address to check
     */
    function isApprovedToken(address token) external view returns (bool) {
        return approvedBuybackTokens[token];
    }

    /**
     * @notice Get pending buyback amount for a token
     * @param token Token to check
     */
    function getPendingBuyback(address token) external view returns (uint256) {
        return IERC20(token).balanceOf(address(this));
    }

    // Allow receiving ETH
    receive() external payable {}
}
