// SPDX-License-Identifier: MIT
// Created: 2026-01-20
pragma solidity 0.8.24;

import "forge-std/Script.sol";

interface IKerneZINPool {
    function supportToken(address token) external;
    function supportedTokens(address token) external view returns (bool);
    function hasRole(bytes32 role, address account) external view returns (bool);
    function MANAGER_ROLE() external view returns (bytes32);
}

/**
 * @title EnableZINTokens
 * @notice Enables USDC and WETH as supported tokens in the ZIN Pool
 * @dev Run with: forge script script/EnableZINTokens.s.sol --rpc-url $BASE_RPC_URL --broadcast
 */
contract EnableZINTokens is Script {
    // Base Mainnet Addresses
    address constant ZIN_POOL = 0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7;
    address constant USDC = 0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913;
    address constant WETH = 0x4200000000000000000000000000000000000006;
    address constant WSTETH = 0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452;
    address constant CBETH = 0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        IKerneZINPool pool = IKerneZINPool(ZIN_POOL);
        
        console.log("=== Enable ZIN Pool Tokens ===");
        console.log("ZIN Pool:", ZIN_POOL);
        console.log("Deployer:", deployer);
        
        // Check if deployer has MANAGER_ROLE
        bytes32 managerRole = pool.MANAGER_ROLE();
        bool hasManager = pool.hasRole(managerRole, deployer);
        console.log("Has MANAGER_ROLE:", hasManager);
        
        if (!hasManager) {
            console.log("ERROR: Deployer does not have MANAGER_ROLE");
            return;
        }
        
        vm.startBroadcast(deployerPrivateKey);
        
        // Enable USDC
        if (!pool.supportedTokens(USDC)) {
            console.log("Enabling USDC...");
            pool.supportToken(USDC);
            console.log("USDC enabled!");
        } else {
            console.log("USDC already supported");
        }
        
        // Enable WETH
        if (!pool.supportedTokens(WETH)) {
            console.log("Enabling WETH...");
            pool.supportToken(WETH);
            console.log("WETH enabled!");
        } else {
            console.log("WETH already supported");
        }
        
        // Enable wstETH (for LST intents)
        if (!pool.supportedTokens(WSTETH)) {
            console.log("Enabling wstETH...");
            pool.supportToken(WSTETH);
            console.log("wstETH enabled!");
        } else {
            console.log("wstETH already supported");
        }
        
        // Enable cbETH (for LST intents)
        if (!pool.supportedTokens(CBETH)) {
            console.log("Enabling cbETH...");
            pool.supportToken(CBETH);
            console.log("cbETH enabled!");
        } else {
            console.log("cbETH already supported");
        }
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Verification ===");
        console.log("USDC supported:", pool.supportedTokens(USDC));
        console.log("WETH supported:", pool.supportedTokens(WETH));
        console.log("wstETH supported:", pool.supportedTokens(WSTETH));
        console.log("cbETH supported:", pool.supportedTokens(CBETH));
        console.log("");
        console.log("Done! ZIN Pool can now flash loan these tokens.");
    }
}
