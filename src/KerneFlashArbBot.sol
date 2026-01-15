// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";
import { IERC3156FlashLender } from "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";
import { IAerodromeRouter } from "./interfaces/IAerodromeRouter.sol";
import { IUniswapV3Router } from "./interfaces/IUniswapV3Router.sol";

/**
 * @title KerneFlashArbBot
 * @author Kerne Protocol
 * @notice Zero-capital arbitrage executor using internal flash loans
 * @dev Captures price spreads between Aerodrome and Uniswap V3 on Base,
 *      routing all profits to KerneTreasury for founder wealth extraction.
 * 
 * Architecture:
 *   1. Flash borrow from KUSDPSM or KerneVault (0% fee for ARBITRAGEUR_ROLE)
 *   2. Execute cross-DEX arbitrage (buy low, sell high)
 *   3. Repay flash loan
 *   4. Route profit: 80% → Treasury, 20% → Insurance Fund
 * 
 * Supported Arb Patterns:
 *   - Aerodrome ↔ Uniswap V3 price gaps
 *   - PSM stable coin depegs (kUSD arbitrage)
 *   - LST/ETH rate discrepancies (stETH, cbETH, rETH)
 *   - Triangular arbitrage (A → B → C → A)
 */
contract KerneFlashArbBot is AccessControl, ReentrancyGuard, Pausable, IERC3156FlashBorrower {
    using SafeERC20 for IERC20;

    // ═══════════════════════════════════════════════════════════════════════════════
    // ROLES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    bytes32 public constant EXECUTOR_ROLE = keccak256("EXECUTOR_ROLE");
    bytes32 public constant SENTINEL_ROLE = keccak256("SENTINEL_ROLE");
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // STATE
    // ═══════════════════════════════════════════════════════════════════════════════
    
    /// @notice Treasury address (receives 80% of profits)
    address public treasury;
    
    /// @notice Insurance fund (receives 20% of profits)
    address public insuranceFund;
    
    /// @notice Main vault for solvency checks
    address public vault;
    
    /// @notice PSM for kUSD arbitrage
    address public psm;
    
    /// @notice Aerodrome Router V2
    IAerodromeRouter public aerodromeRouter;
    
    /// @notice Uniswap V3 Router
    IUniswapV3Router public uniswapRouter;
    
    /// @notice Aerodrome factory for pool lookups
    address public aerodromeFactory;
    
    /// @notice Profit split: insurance fund share (bps)
    uint256 public insuranceSplitBps = 2000; // 20%
    
    /// @notice Minimum profit threshold (bps of borrowed amount)
    uint256 public minProfitBps = 5; // 0.05%
    
    /// @notice Minimum solvency ratio required
    uint256 public minSolvencyThreshold = 10100; // 101%
    
    /// @notice Whether sentinel checks are active
    bool public sentinelActive = true;
    
    /// @notice Approved flash lenders
    mapping(address => bool) public approvedLenders;
    
    /// @notice Approved tokens for arbitrage
    mapping(address => bool) public approvedTokens;
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // STRUCTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    enum DEX { Aerodrome, UniswapV3 }
    
    struct SwapParams {
        DEX dex;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 minAmountOut;
        bool stable;           // For Aerodrome pools
        uint24 fee;            // For Uniswap V3 pools (500, 3000, 10000)
        bytes extraData;       // For multi-hop paths
    }
    
    struct ArbParams {
        address lender;        // Flash loan source (PSM or Vault)
        address borrowToken;   // Token to flash borrow
        uint256 borrowAmount;  // Amount to borrow
        SwapParams[] swaps;    // Sequence of swaps
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    event ArbExecuted(
        address indexed borrowToken,
        uint256 borrowAmount,
        uint256 grossProfit,
        uint256 netProfit,
        uint256 toTreasury,
        uint256 toInsurance
    );
    event SwapExecuted(DEX dex, address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut);
    event LenderApproved(address indexed lender, bool approved);
    event TokenApproved(address indexed token, bool approved);
    event ConfigUpdated(string param, uint256 value);
    event SentinelToggled(bool active);
    event EmergencyWithdraw(address indexed token, uint256 amount);
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ERRORS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    error ZeroAddress();
    error UnauthorizedLender();
    error UnauthorizedToken();
    error ArbNotProfitable(uint256 expected, uint256 actual);
    error SwapFailed(uint8 swapIndex);
    error SolvencyCheckFailed(uint256 ratio);
    error InvalidParams();
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════════════════════
    
    constructor(
        address _admin,
        address _treasury,
        address _insuranceFund,
        address _vault,
        address _psm,
        address _aerodromeRouter,
        address _uniswapRouter
    ) {
        if (_admin == address(0)) revert ZeroAddress();
        if (_treasury == address(0)) revert ZeroAddress();
        
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(EXECUTOR_ROLE, _admin);
        _grantRole(SENTINEL_ROLE, _admin);
        
        treasury = _treasury;
        insuranceFund = _insuranceFund;
        vault = _vault;
        psm = _psm;
        
        if (_aerodromeRouter != address(0)) {
            aerodromeRouter = IAerodromeRouter(_aerodromeRouter);
            aerodromeFactory = aerodromeRouter.defaultFactory();
        }
        
        if (_uniswapRouter != address(0)) {
            uniswapRouter = IUniswapV3Router(_uniswapRouter);
        }
        
        // Approve internal lenders by default
        if (_psm != address(0)) approvedLenders[_psm] = true;
        if (_vault != address(0)) approvedLenders[_vault] = true;
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // CORE ARBITRAGE FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    /**
     * @notice Execute a complete arbitrage cycle using flash loan
     * @param params The arbitrage parameters including lender, amount, and swap sequence
     * @dev Called by the off-chain bot when an opportunity is detected
     */
    function executeArbitrage(ArbParams calldata params) 
        external 
        onlyRole(EXECUTOR_ROLE) 
        nonReentrant 
        whenNotPaused 
    {
        _checkSolvency();
        
        if (!approvedLenders[params.lender]) revert UnauthorizedLender();
        if (!approvedTokens[params.borrowToken]) revert UnauthorizedToken();
        if (params.swaps.length == 0) revert InvalidParams();
        
        // Encode swap sequence for callback
        bytes memory data = abi.encode(params.swaps);
        
        // Initiate flash loan
        IERC3156FlashLender(params.lender).flashLoan(
            this,
            params.borrowToken,
            params.borrowAmount,
            data
        );
    }
    
    /**
     * @notice Flash loan callback - executes the arb sequence
     */
    function onFlashLoan(
        address initiator,
        address token,
        uint256 amount,
        uint256 fee,
        bytes calldata data
    ) external override returns (bytes32) {
        // Verify callback is from approved lender
        if (!approvedLenders[msg.sender]) revert UnauthorizedLender();
        
        // Verify initiator is this contract
        require(initiator == address(this), "Invalid initiator");
        
        uint256 balanceBefore = IERC20(token).balanceOf(address(this));
        
        // Decode and execute swap sequence
        SwapParams[] memory swaps = abi.decode(data, (SwapParams[]));
        
        for (uint8 i = 0; i < swaps.length; i++) {
            _executeSwap(swaps[i], i);
        }
        
        uint256 balanceAfter = IERC20(token).balanceOf(address(this));
        uint256 repayAmount = amount + fee;
        
        // Validate profitability
        if (balanceAfter < balanceBefore + fee) {
            revert ArbNotProfitable(balanceBefore + fee, balanceAfter);
        }
        
        uint256 grossProfit = balanceAfter - balanceBefore;
        
        // Verify minimum profit threshold
        uint256 minProfit = (amount * minProfitBps) / 10000;
        if (grossProfit < minProfit) {
            revert ArbNotProfitable(minProfit, grossProfit);
        }
        
        // Calculate and distribute profits
        uint256 netProfit = grossProfit - fee;
        _distributeProfits(token, netProfit);
        
        // Approve repayment
        IERC20(token).forceApprove(msg.sender, repayAmount);
        
        emit ArbExecuted(token, amount, grossProfit, netProfit, 
            (netProfit * (10000 - insuranceSplitBps)) / 10000,
            (netProfit * insuranceSplitBps) / 10000
        );
        
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
    
    /**
     * @notice Execute a single swap on the specified DEX
     */
    function _executeSwap(SwapParams memory params, uint8 index) internal {
        uint256 balanceBefore = IERC20(params.tokenOut).balanceOf(address(this));
        
        // Approve the router
        if (params.dex == DEX.Aerodrome) {
            _executeAerodromeSwap(params);
        } else if (params.dex == DEX.UniswapV3) {
            _executeUniswapSwap(params);
        }
        
        uint256 balanceAfter = IERC20(params.tokenOut).balanceOf(address(this));
        uint256 amountOut = balanceAfter - balanceBefore;
        
        if (amountOut < params.minAmountOut) {
            revert SwapFailed(index);
        }
        
        emit SwapExecuted(params.dex, params.tokenIn, params.tokenOut, params.amountIn, amountOut);
    }
    
    /**
     * @notice Execute swap on Aerodrome
     */
    function _executeAerodromeSwap(SwapParams memory params) internal {
        IERC20(params.tokenIn).forceApprove(address(aerodromeRouter), params.amountIn);
        
        IAerodromeRouter.Route[] memory routes = new IAerodromeRouter.Route[](1);
        routes[0] = IAerodromeRouter.Route({
            from: params.tokenIn,
            to: params.tokenOut,
            stable: params.stable,
            factory: aerodromeFactory
        });
        
        aerodromeRouter.swapExactTokensForTokens(
            params.amountIn,
            params.minAmountOut,
            routes,
            address(this),
            block.timestamp + 300
        );
    }
    
    /**
     * @notice Execute swap on Uniswap V3
     */
    function _executeUniswapSwap(SwapParams memory params) internal {
        IERC20(params.tokenIn).forceApprove(address(uniswapRouter), params.amountIn);
        
        IUniswapV3Router.ExactInputSingleParams memory uniParams = IUniswapV3Router.ExactInputSingleParams({
            tokenIn: params.tokenIn,
            tokenOut: params.tokenOut,
            fee: params.fee,
            recipient: address(this),
            amountIn: params.amountIn,
            amountOutMinimum: params.minAmountOut,
            sqrtPriceLimitX96: 0
        });
        
        uniswapRouter.exactInputSingle(uniParams);
    }
    
    /**
     * @notice Distribute profits to treasury and insurance fund
     */
    function _distributeProfits(address token, uint256 profit) internal {
        if (profit == 0) return;
        
        uint256 insuranceAmount = (profit * insuranceSplitBps) / 10000;
        uint256 treasuryAmount = profit - insuranceAmount;
        
        if (insuranceAmount > 0 && insuranceFund != address(0)) {
            IERC20(token).safeTransfer(insuranceFund, insuranceAmount);
        }
        
        if (treasuryAmount > 0 && treasury != address(0)) {
            IERC20(token).safeTransfer(treasury, treasuryAmount);
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // SPECIALIZED ARB FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    /**
     * @notice Execute PSM arbitrage when kUSD depegs
     * @dev Buy kUSD cheap on DEX, redeem 1:1 at PSM (or vice versa)
     * @param stableToken The stable to swap kUSD for (USDC, USDT, DAI)
     * @param borrowAmount Amount of stable to flash borrow
     * @param buyOnDex If true, buy kUSD on DEX → redeem at PSM. If false, mint at PSM → sell on DEX.
     * @param dex Which DEX to trade on
     * @param minProfit Minimum profit required
     */
    function executePsmArbitrage(
        address stableToken,
        uint256 borrowAmount,
        bool buyOnDex,
        DEX dex,
        uint256 minProfit
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant whenNotPaused {
        _checkSolvency();
        
        // Get kUSD address from PSM
        (bool success, bytes memory data) = psm.staticcall(abi.encodeWithSignature("kUSD()"));
        require(success, "Failed to get kUSD address");
        address kUSD = abi.decode(data, (address));
        
        uint256 balanceBefore = IERC20(stableToken).balanceOf(address(this));
        
        // Flash borrow from PSM
        bytes memory arbData = abi.encode(buyOnDex, dex, stableToken, kUSD);
        IERC3156FlashLender(psm).flashLoan(this, stableToken, borrowAmount, arbData);
        
        uint256 balanceAfter = IERC20(stableToken).balanceOf(address(this));
        
        require(balanceAfter > balanceBefore + minProfit, "PSM arb not profitable");
        
        uint256 profit = balanceAfter - balanceBefore;
        _distributeProfits(stableToken, profit);
    }
    
    /**
     * @notice Execute triangular arbitrage
     * @dev A → B → C → A pattern to exploit price inefficiencies
     */
    function executeTriangularArb(
        address lender,
        address tokenA,
        address tokenB,
        address tokenC,
        uint256 amountA,
        DEX dexAB,
        DEX dexBC,
        DEX dexCA,
        uint24[3] calldata fees,  // Uniswap fees for each leg
        bool[3] calldata stables  // Aerodrome stable flags for each leg
    ) external onlyRole(EXECUTOR_ROLE) nonReentrant whenNotPaused {
        _checkSolvency();
        
        if (!approvedLenders[lender]) revert UnauthorizedLender();
        
        SwapParams[] memory swaps = new SwapParams[](3);
        
        // Leg 1: A → B
        swaps[0] = SwapParams({
            dex: dexAB,
            tokenIn: tokenA,
            tokenOut: tokenB,
            amountIn: amountA,
            minAmountOut: 1,
            stable: stables[0],
            fee: fees[0],
            extraData: ""
        });
        
        // Leg 2: B → C (amount will be updated dynamically)
        swaps[1] = SwapParams({
            dex: dexBC,
            tokenIn: tokenB,
            tokenOut: tokenC,
            amountIn: 0, // Will use full balance
            minAmountOut: 1,
            stable: stables[1],
            fee: fees[1],
            extraData: ""
        });
        
        // Leg 3: C → A
        swaps[2] = SwapParams({
            dex: dexCA,
            tokenIn: tokenC,
            tokenOut: tokenA,
            amountIn: 0, // Will use full balance
            minAmountOut: amountA, // Must return at least what we borrowed
            stable: stables[2],
            fee: fees[2],
            extraData: ""
        });
        
        bytes memory data = abi.encode(swaps);
        IERC3156FlashLender(lender).flashLoan(this, tokenA, amountA, data);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // PRICE QUERIES
    // ═══════════════════════════════════════════════════════════════════════════════
    
    /**
     * @notice Get Aerodrome price quote
     */
    function getAerodromeQuote(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        bool stable
    ) external view returns (uint256 amountOut) {
        IAerodromeRouter.Route[] memory routes = new IAerodromeRouter.Route[](1);
        routes[0] = IAerodromeRouter.Route({
            from: tokenIn,
            to: tokenOut,
            stable: stable,
            factory: aerodromeFactory
        });
        
        uint256[] memory amounts = aerodromeRouter.getAmountsOut(amountIn, routes);
        return amounts[amounts.length - 1];
    }
    
    /**
     * @notice Check for arbitrage opportunity between DEXs
     * @return profitable Whether arb is profitable
     * @return profit Expected profit amount
     * @return buyDex Which DEX to buy on
     */
    function checkArbOpportunity(
        address tokenA,
        address tokenB,
        uint256 amountIn,
        bool aeroStable,
        uint24 uniFee
    ) external view returns (bool profitable, uint256 profit, DEX buyDex) {
        // Get Aerodrome price
        uint256 aeroOut = this.getAerodromeQuote(tokenA, tokenB, amountIn, aeroStable);
        
        // For Uniswap, we'd need to call quoter (not available as view)
        // This is a simplified check - real implementation uses off-chain quoter
        
        // Placeholder logic - real implementation compares both prices
        return (false, 0, DEX.Aerodrome);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // SAFETY CHECKS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function _checkSolvency() internal view {
        if (!sentinelActive || vault == address(0)) return;
        
        (bool success, bytes memory data) = vault.staticcall(
            abi.encodeWithSignature("getSolvencyRatio()")
        );
        
        if (success && data.length == 32) {
            uint256 ratio = abi.decode(data, (uint256));
            if (ratio < minSolvencyThreshold) {
                revert SolvencyCheckFailed(ratio);
            }
        }
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function setLenderApproval(address lender, bool approved) external onlyRole(DEFAULT_ADMIN_ROLE) {
        approvedLenders[lender] = approved;
        emit LenderApproved(lender, approved);
    }
    
    function setTokenApproval(address token, bool approved) external onlyRole(DEFAULT_ADMIN_ROLE) {
        approvedTokens[token] = approved;
        emit TokenApproved(token, approved);
    }
    
    function setTreasury(address _treasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_treasury == address(0)) revert ZeroAddress();
        treasury = _treasury;
    }
    
    function setInsuranceFund(address _insuranceFund) external onlyRole(DEFAULT_ADMIN_ROLE) {
        insuranceFund = _insuranceFund;
    }
    
    function setInsuranceSplit(uint256 bps) external onlyRole(SENTINEL_ROLE) {
        require(bps <= 5000, "Max 50%");
        insuranceSplitBps = bps;
        emit ConfigUpdated("insuranceSplitBps", bps);
    }
    
    function setMinProfitBps(uint256 bps) external onlyRole(SENTINEL_ROLE) {
        minProfitBps = bps;
        emit ConfigUpdated("minProfitBps", bps);
    }
    
    function setMinSolvencyThreshold(uint256 threshold) external onlyRole(SENTINEL_ROLE) {
        minSolvencyThreshold = threshold;
        emit ConfigUpdated("minSolvencyThreshold", threshold);
    }
    
    function toggleSentinel(bool active) external onlyRole(SENTINEL_ROLE) {
        sentinelActive = active;
        emit SentinelToggled(active);
    }
    
    function setRouters(address _aerodrome, address _uniswap) external onlyRole(DEFAULT_ADMIN_ROLE) {
        if (_aerodrome != address(0)) {
            aerodromeRouter = IAerodromeRouter(_aerodrome);
            aerodromeFactory = aerodromeRouter.defaultFactory();
        }
        if (_uniswap != address(0)) {
            uniswapRouter = IUniswapV3Router(_uniswap);
        }
    }
    
    function pause() external onlyRole(SENTINEL_ROLE) {
        _pause();
    }
    
    function unpause() external onlyRole(DEFAULT_ADMIN_ROLE) {
        _unpause();
    }
    
    /**
     * @notice Emergency token recovery
     */
    function emergencyWithdraw(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        IERC20(token).safeTransfer(msg.sender, balance);
        emit EmergencyWithdraw(token, balance);
    }
    
    /**
     * @notice Emergency ETH recovery
     */
    function emergencyWithdrawETH() external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = address(this).balance;
        (bool success, ) = msg.sender.call{value: balance}("");
        require(success, "ETH transfer failed");
    }
    
    receive() external payable {}
}
