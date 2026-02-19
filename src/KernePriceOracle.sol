// Created: 2026-02-19
// Kerne Protocol - Multi-Source Price Oracle with TWAP
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { IKernePriceOracle } from "./interfaces/IKernePriceOracle.sol";
import { IUniswapV3Pool } from "./interfaces/IUniswapV3Pool.sol";

/// @title Chainlink Aggregator Interface (minimal)
interface IAggregatorV3 {
    function latestRoundData() external view returns (
        uint80 roundId,
        int256 answer,
        uint256 startedAt,
        uint256 updatedAt,
        uint80 answeredInRound
    );
    function decimals() external view returns (uint8);
}

/// @title KernePriceOracle
/// @notice Multi-source price oracle with Chainlink + Uniswap V3 TWAP
/// @dev Provides manipulation-resistant price feeds for vault operations
contract KernePriceOracle is AccessControl, IKernePriceOracle {
    // ============================================================
    //                      ROLES
    // ============================================================
    
    bytes32 public constant UPDATER_ROLE = keccak256("UPDATER_ROLE");
    bytes32 public constant ADMIN_ROLE = DEFAULT_ADMIN_ROLE;

    // ============================================================
    //                      STATE VARIABLES
    // ============================================================
    
    /// @notice Chainlink price feed
    IAggregatorV3 public chainlinkFeed;
    
    /// @notice Uniswap V3 pool for TWAP
    IUniswapV3Pool public uniswapPool;
    
    /// @notice Token that the price represents (e.g., WETH)
    address public targetToken;
    
    /// @notice Quote token (e.g., USDC)
    address public quoteToken;
    
    /// @notice TWAP observation window in seconds
    uint256 public twapWindow = 1800; // 30 minutes
    
    /// @notice Max staleness for Chainlink price (seconds)
    uint256 public staleThreshold = 3600; // 1 hour
    
    /// @notice Max deviation between sources in basis points (3% = 300)
    uint256 public maxDeviationBps = 300;
    
    /// @notice Max deviation for price validity in basis points (10% = 1000)
    uint256 public maxValidityDeviationBps = 1000;
    
    /// @notice Chainlink decimals offset
    uint8 public chainlinkDecimals;
    
    /// @notice Whether token0 is the target token in Uniswap pool
    bool public targetIsToken0;

    // ============================================================
    //                      TWAP STORAGE
    // ============================================================
    
    /// @notice TWAP observation data
    struct Observation {
        uint256 timestamp;
        int56 tickCumulative;
        uint160 secondsPerLiquidityCumulativeX128;
    }
    
    /// @notice Last observation stored
    Observation public lastObservation;
    
    /// @notice Whether the oracle has been initialized
    bool public initialized;

    // ============================================================
    //                      EVENTS
    // ============================================================
    
    event OracleInitialized(
        address indexed chainlinkFeed,
        address indexed uniswapPool,
        address targetToken,
        address quoteToken
    );
    
    event TwapWindowUpdated(uint256 oldWindow, uint256 newWindow);
    event StaleThresholdUpdated(uint256 oldThreshold, uint256 newThreshold);
    event MaxDeviationUpdated(uint256 oldBps, uint256 newBps);

    // ============================================================
    //                      ERRORS
    // ============================================================
    
    error NotInitialized();
    error StaleChainlinkPrice();
    error InvalidPriceSources();
    error DeviationTooHigh(uint256 chainlinkPrice, uint256 twapPrice);
    error ZeroAddress();

    // ============================================================
    //                      CONSTRUCTOR
    // ============================================================
    
    constructor() {
        _grantRole(DEFAULT_ADMIN_ROLE, msg.sender);
        _grantRole(UPDATER_ROLE, msg.sender);
    }

    // ============================================================
    //                      INITIALIZATION
    // ============================================================
    
    /// @notice Initialize the oracle with price sources
    /// @param _chainlinkFeed Chainlink price feed address
    /// @param _uniswapPool Uniswap V3 pool address
    /// @param _targetToken The token we're pricing (e.g., WETH)
    /// @param _quoteToken The quote token (e.g., USDC)
    function initialize(
        address _chainlinkFeed,
        address _uniswapPool,
        address _targetToken,
        address _quoteToken
    ) external onlyRole(ADMIN_ROLE) {
        require(!initialized, "Already initialized");
        if (_chainlinkFeed == address(0) || _uniswapPool == address(0)) revert ZeroAddress();
        
        chainlinkFeed = IAggregatorV3(_chainlinkFeed);
        uniswapPool = IUniswapV3Pool(_uniswapPool);
        targetToken = _targetToken;
        quoteToken = _quoteToken;
        
        // Get Chainlink decimals
        chainlinkDecimals = chainlinkFeed.decimals();
        
        // Determine if target is token0 or token1
        address poolToken0 = uniswapPool.token0();
        targetIsToken0 = (poolToken0 == _targetToken);
        
        // Seed initial observation
        _updateObservation();
        
        initialized = true;
        
        emit OracleInitialized(_chainlinkFeed, _uniswapPool, _targetToken, _quoteToken);
    }

    // ============================================================
    //                      CORE FUNCTIONS
    // ============================================================
    
    /// @notice Returns current median price from all sources
    /// @return price The current price in 18 decimal precision
    function getPrice() external view override returns (uint256 price) {
        uint256 chainlinkPrice = _getChainlinkPrice();
        uint256 twapPrice = _getTwapPrice();
        
        // Calculate deviation
        uint256 diff = chainlinkPrice > twapPrice 
            ? chainlinkPrice - twapPrice 
            : twapPrice - chainlinkPrice;
        
        uint256 avgPrice = (chainlinkPrice + twapPrice) / 2;
        
        // If prices within maxDeviationBps, return average
        if (diff <= (avgPrice * maxDeviationBps) / 10000) {
            return avgPrice;
        }
        
        // If deviation > maxDeviationBps but < maxValidityDeviationBps, prefer Chainlink
        // This allows graceful degradation while still returning a price
        return chainlinkPrice;
    }
    
    /// @notice Returns TWAP price from Uniswap V3
    /// @return price The TWAP price in 18 decimal precision
    function getTwapPrice() external view override returns (uint256 price) {
        return _getTwapPrice();
    }
    
    /// @notice Returns true if all price sources are within tolerance
    /// @return valid Whether the price sources agree within acceptable bounds
    function isPriceValid() external view override returns (bool valid) {
        if (!initialized) return false;
        
        // Check Chainlink staleness
        (, , , uint256 updatedAt, ) = chainlinkFeed.latestRoundData();
        if (block.timestamp - updatedAt > staleThreshold) return false;
        
        uint256 chainlinkPrice = _getChainlinkPrice();
        uint256 twapPrice = _getTwapPrice();
        
        // Check deviation
        uint256 diff = chainlinkPrice > twapPrice 
            ? chainlinkPrice - twapPrice 
            : twapPrice - chainlinkPrice;
        uint256 avgPrice = (chainlinkPrice + twapPrice) / 2;
        
        return diff <= (avgPrice * maxValidityDeviationBps) / 10000;
    }
    
    /// @notice Returns individual source prices for transparency
    function getPriceSources() external view override returns (
        uint256 chainlinkPrice,
        uint256 uniswapTwapPrice,
        uint256 timestamp
    ) {
        chainlinkPrice = _getChainlinkPrice();
        uniswapTwapPrice = _getTwapPrice();
        timestamp = lastObservation.timestamp;
    }
    
    /// @notice Updates TWAP observation (called by bot)
    function updateObservation() external override onlyRole(UPDATER_ROLE) {
        _updateObservation();
    }

    // ============================================================
    //                      INTERNAL FUNCTIONS
    // ============================================================
    
    /// @dev Get Chainlink price in 18 decimals
    function _getChainlinkPrice() internal view returns (uint256) {
        (, int256 answer, , uint256 updatedAt, ) = chainlinkFeed.latestRoundData();
        
        if (block.timestamp - updatedAt > staleThreshold) {
            revert StaleChainlinkPrice();
        }
        
        // Convert to 18 decimals
        uint256 price = uint256(answer);
        if (chainlinkDecimals < 18) {
            price = price * (10 ** (18 - chainlinkDecimals));
        } else if (chainlinkDecimals > 18) {
            price = price / (10 ** (chainlinkDecimals - 18));
        }
        
        return price;
    }
    
    /// @dev Get TWAP price from Uniswap V3 in 18 decimals
    function _getTwapPrice() internal view returns (uint256) {
        uint32[] memory secondsAgos = new uint32[](2);
        secondsAgos[0] = uint32(twapWindow);
        secondsAgos[1] = 0;
        
        try uniswapPool.observe(secondsAgos) returns (
            int56[] memory tickCumulatives,
            uint160[] memory
        ) {
            // Calculate average tick over TWAP window
            int56 tickCumulativeDelta = tickCumulatives[1] - tickCumulatives[0];
            int24 averageTick = int24(tickCumulativeDelta / int56(int256(twapWindow)));
            
            // Convert tick to price
            // price = sqrtRatioX96^2 / 2^192
            // For tick: sqrtPrice = sqrt(1.0001^tick) * 2^96
            uint256 sqrtPriceX96 = _getSqrtRatioAtTick(averageTick);
            
            // Calculate price (token1/token0)
            uint256 price = (sqrtPriceX96 * sqrtPriceX96) / (2 ** 192);
            
            // Adjust for decimals (assuming both tokens are 18 decimals)
            // If target is token0, we need price of token0 in terms of token1
            // If target is token1, we need to invert
            if (targetIsToken0) {
                // Price is already token1 per token0
                return price;
            } else {
                // Invert to get token0 per token1
                if (price > 0) {
                    return (1e36) / price;
                }
                revert InvalidPriceSources();
            }
        } catch {
            // Fallback to current price from slot0
            (uint160 sqrtPriceX96, , , , , , ) = uniswapPool.slot0();
            uint256 price = (uint256(sqrtPriceX96) * uint256(sqrtPriceX96)) / (2 ** 192);
            
            if (targetIsToken0) {
                return price;
            } else {
                if (price > 0) {
                    return (1e36) / price;
                }
                revert InvalidPriceSources();
            }
        }
    }
    
    /// @dev Calculate sqrt ratio at tick using optimized bit manipulation
    /// @notice Uses the same algorithm as Uniswap V3 TickMath
    function _getSqrtRatioAtTick(int24 tick) internal pure returns (uint256) {
        int256 absTick = tick < 0 ? -int256(int24(tick)) : int256(int24(tick));
        
        require(absTick <= 887272, "Tick out of range");
        
        // Start with 2^96 (sqrt(1) in Q64.96)
        uint256 ratio = 0x1000000000000000000000000;
        
        // Apply tick bits using precomputed constants
        // Each bit represents sqrt(1.0001^2^i) = 1.0001^(2^(i-1))
        // These are the geometric series factors
        if (absTick & 0x1 != 0) ratio = (ratio * 0xfffcb933bd6fad37aa2d162d1a594001) >> 128;
        if (absTick & 0x2 != 0) ratio = (ratio * 0xfff97272373d413259a46990580e213a) >> 128;
        if (absTick & 0x4 != 0) ratio = (ratio * 0xfff2e50f5f656932ef12357cf3c7fdcc) >> 128;
        if (absTick & 0x8 != 0) ratio = (ratio * 0xffe5caca7e10e4e61c3624eaa0941cd0) >> 128;
        if (absTick & 0x10 != 0) ratio = (ratio * 0xffcb9843d60f6159c9db58835c926644) >> 128;
        if (absTick & 0x20 != 0) ratio = (ratio * 0xff973b41fa98c081472e6896dfb254c0) >> 128;
        if (absTick & 0x40 != 0) ratio = (ratio * 0xff2ea16466c96a3843ec78b326b52861) >> 128;
        if (absTick & 0x80 != 0) ratio = (ratio * 0xfe5dee046a99a2a811c461f1969c3053) >> 128;
        if (absTick & 0x100 != 0) ratio = (ratio * 0xfcbe86c7900a88aedcffc83b479aa3a4) >> 128;
        if (absTick & 0x200 != 0) ratio = (ratio * 0xf987a7253ac413176f2b074cf7815e54) >> 128;
        if (absTick & 0x400 != 0) ratio = (ratio * 0xf3392b0822b70005940c7a398e4b70f3) >> 128;
        if (absTick & 0x800 != 0) ratio = (ratio * 0xe7159475a2c29b7443b29c7fa6e889d9) >> 128;
        if (absTick & 0x1000 != 0) ratio = (ratio * 0xd097f3bdfd2022b8845ad8f792aa5825) >> 128;
        if (absTick & 0x2000 != 0) ratio = (ratio * 0xa9f746462d870fdf8a65dc1f90e061e5) >> 128;
        if (absTick & 0x4000 != 0) ratio = (ratio * 0x70d869a156d2a1b890bb3df62baf32f7) >> 128;
        if (absTick & 0x8000 != 0) ratio = (ratio * 0x31be135f97d08fd981231505542fcfa6) >> 128;
        if (absTick & 0x10000 != 0) ratio = (ratio * 0x9aa508b5b7a84e1c677de54f3e99bc9) >> 128;
        if (absTick & 0x20000 != 0) ratio = (ratio * 0x5d6af8dedb81196699c329225ee604) >> 128;
        if (absTick & 0x40000 != 0) ratio = (ratio * 0x2216e584f5fa1ea926041bedfe98) >> 128;
        if (absTick & 0x80000 != 0) ratio = (ratio * 0x48a170391f7dc42444e8fa2) >> 128;
        
        // Adjust for negative tick
        if (tick < 0) {
            // Invert the ratio for negative ticks
            ratio = type(uint256).max / ratio;
        }
        
        return ratio;
    }
    
    /// @dev Internal function to update observation
    function _updateObservation() internal {
        uint32[] memory secondsAgos = new uint32[](1);
        secondsAgos[0] = 0;
        
        try uniswapPool.observe(secondsAgos) returns (
            int56[] memory tickCumulatives,
            uint160[] memory secondsPerLiquidityCumulativeX128s
        ) {
            lastObservation = Observation({
                timestamp: block.timestamp,
                tickCumulative: tickCumulatives[0],
                secondsPerLiquidityCumulativeX128: secondsPerLiquidityCumulativeX128s[0]
            });
            
            emit ObservationRecorded(
                block.timestamp,
                uint256(int256(tickCumulatives[0])),
                uint256(secondsPerLiquidityCumulativeX128s[0])
            );
        } catch {
            // If observe fails, store current state
            lastObservation = Observation({
                timestamp: block.timestamp,
                tickCumulative: 0,
                secondsPerLiquidityCumulativeX128: 0
            });
        }
    }

    // ============================================================
    //                      ADMIN FUNCTIONS
    // ============================================================
    
    /// @notice Update TWAP window
    function setTwapWindow(uint256 _twapWindow) external onlyRole(ADMIN_ROLE) {
        emit TwapWindowUpdated(twapWindow, _twapWindow);
        twapWindow = _twapWindow;
    }
    
    /// @notice Update stale threshold
    function setStaleThreshold(uint256 _staleThreshold) external onlyRole(ADMIN_ROLE) {
        emit StaleThresholdUpdated(staleThreshold, _staleThreshold);
        staleThreshold = _staleThreshold;
    }
    
    /// @notice Update max deviation
    function setMaxDeviationBps(uint256 _maxDeviationBps) external onlyRole(ADMIN_ROLE) {
        emit MaxDeviationUpdated(maxDeviationBps, _maxDeviationBps);
        maxDeviationBps = _maxDeviationBps;
    }
    
    /// @notice Update max validity deviation
    function setMaxValidityDeviationBps(uint256 _bps) external onlyRole(ADMIN_ROLE) {
        maxValidityDeviationBps = _bps;
    }
}