// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import { Test } from "forge-std/Test.sol";
import { KernePriceOracle } from "../src/KernePriceOracle.sol";

/// @title KernePriceOracleForkTest
/// @notice Tests oracle with real Base mainnet contracts
contract KernePriceOracleForkTest is Test {
    // Base Mainnet Addresses
    address constant ETH_USD_CHAINLINK = 0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70;
    address constant USDC_USD_CHAINLINK = 0x833D8Eb16D306ed1FbB5D7A2E019e106B960965A;
    address constant WETH_USDC_POOL = 0xD0B53D94776b2FfABBF66993B687Fe9F0a2b7F22;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    
    KernePriceOracle public oracle;
    
    address public admin = address(0x1);
    
    function setUp() public {
        // Fork Base mainnet
        vm.createSelectFork("https://mainnet.base.org");
        
        // Mark external contracts as persistent
        vm.makePersistent(ETH_USD_CHAINLINK);
        vm.makePersistent(USDC_USD_CHAINLINK);
        vm.makePersistent(WETH_USDC_POOL);
        vm.makePersistent(WETH);
        vm.makePersistent(USDC);
        
        vm.startPrank(admin);
        
        // Deploy oracle
        oracle = new KernePriceOracle();
        
        // Initialize with real addresses
        oracle.initialize(
            ETH_USD_CHAINLINK,
            WETH_USDC_POOL,
            WETH,
            USDC
        );
        
        vm.stopPrank();
    }
    
    function test_GetPriceFromRealSources() public {
        uint256 price = oracle.getPrice();
        
        // ETH should be between $1000 and $10000
        assertGt(price, 1000 * 1e18, "Price too low");
        assertLt(price, 10000 * 1e18, "Price too high");
        
        emit log_named_uint("ETH Price (18 decimals)", price / 1e18);
    }
    
    function test_GetPriceSources() public {
        (uint256 chainlinkPrice, uint256 twapPrice, uint256 timestamp) = oracle.getPriceSources();
        
        assertGt(chainlinkPrice, 0, "Chainlink price should be > 0");
        assertGt(twapPrice, 0, "TWAP price should be > 0");
        assertGt(timestamp, 0, "Timestamp should be > 0");
        
        emit log_named_uint("Chainlink Price", chainlinkPrice / 1e18);
        emit log_named_uint("TWAP Price", twapPrice / 1e18);
        
        // Prices should be within 10% of each other
        uint256 diff = chainlinkPrice > twapPrice 
            ? chainlinkPrice - twapPrice 
            : twapPrice - chainlinkPrice;
        uint256 avgPrice = (chainlinkPrice + twapPrice) / 2;
        uint256 deviationBps = (diff * 10000) / avgPrice;
        
        emit log_named_uint("Deviation (bps)", deviationBps);
        
        assertLt(deviationBps, 1000, "Deviation should be < 10%");
    }
    
    function test_IsPriceValid() public {
        bool isValid = oracle.isPriceValid();
        assertTrue(isValid, "Price should be valid on mainnet");
    }
    
    function test_GetTwapPrice() public {
        uint256 twapPrice = oracle.getTwapPrice();
        
        assertGt(twapPrice, 0, "TWAP price should be > 0");
        
        emit log_named_uint("TWAP Price", twapPrice / 1e18);
    }
}