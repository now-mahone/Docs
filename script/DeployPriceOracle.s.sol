// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { KernePriceOracle } from "../src/KernePriceOracle.sol";

/// @title DeployPriceOracle
/// @notice Deploys KernePriceOracle to Base mainnet with Chainlink feeds
contract DeployPriceOracle is Script {
    // Base Mainnet Addresses
    address constant ETH_USD_CHAINLINK = 0x71041dddad3595F9CEd3DcCFBe3D1F4b0a16Bb70;
    address constant USDC_USD_CHAINLINK = 0x833D8Eb16D306ed1FbB5D7A2E019e106B960965A;
    
    // Uniswap V3 WETH/USDC Pool on Base (0.05% fee)
    address constant WETH_USDC_POOL = 0xd0b53D9277642d899DF5C87A3966A349A798F224;
    
    // Token addresses on Base
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;

    function run() external returns (KernePriceOracle oracle) {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Deploy oracle
        oracle = new KernePriceOracle();
        
        // Initialize with ETH/USD feed
        oracle.initialize(
            ETH_USD_CHAINLINK,  // Chainlink ETH/USD feed
            WETH_USDC_POOL,     // Uniswap V3 WETH/USDC pool
            WETH,               // Target token (WETH)
            USDC                // Quote token (USDC)
        );
        
        vm.stopBroadcast();
        
        console.log("KernePriceOracle deployed at:", address(oracle));
    }
}