// SPDX-License-Identifier: MIT
// Created: 2026-02-05
pragma solidity 0.8.24;

import "forge-std/Script.sol";

interface IKerneZINPool {
    function supportToken(address token) external;
    function supportedTokens(address token) external view returns (bool);
    function hasRole(bytes32 role, address account) external view returns (bool);
    function MANAGER_ROLE() external view returns (bytes32);
}

/**
 * @title EnableZINTokensArbitrum
 * @notice Enables USDC, WETH, and wstETH as supported tokens in the ZIN Pool on Arbitrum
 * @dev Run with: forge script script/EnableZINTokensArbitrum.s.sol --rpc-url https://arb1.arbitrum.io/rpc --broadcast
 */
contract EnableZINTokensArbitrum is Script {
    // Arbitrum One Addresses
    address constant ZIN_POOL = 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD;
    address constant USDC = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831;
    address constant USDC_E = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8;
    address constant WETH = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address constant WSTETH = 0x5979D7b546E38E414F7E9822514be443A4800529;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        IKerneZINPool pool = IKerneZINPool(ZIN_POOL);
        
        console.log("=== Enable ZIN Pool Tokens (Arbitrum) ===");
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

        // Enable USDC.e
        if (!pool.supportedTokens(USDC_E)) {
            console.log("Enabling USDC.e...");
            pool.supportToken(USDC_E);
            console.log("USDC.e enabled!");
        } else {
            console.log("USDC.e already supported");
        }
        
        // Enable WETH
        if (!pool.supportedTokens(WETH)) {
            console.log("Enabling WETH...");
            pool.supportToken(WETH);
            console.log("WETH enabled!");
        } else {
            console.log("WETH already supported");
        }
        
        // Enable wstETH
        if (!pool.supportedTokens(WSTETH)) {
            console.log("Enabling wstETH...");
            pool.supportToken(WSTETH);
            console.log("wstETH enabled!");
        } else {
            console.log("wstETH already supported");
        }
        
        vm.stopBroadcast();
        
        console.log("");
        console.log("=== Verification ===");
        console.log("USDC supported:", pool.supportedTokens(USDC));
        console.log("USDC.e supported:", pool.supportedTokens(USDC_E));
        console.log("WETH supported:", pool.supportedTokens(WETH));
        console.log("wstETH supported:", pool.supportedTokens(WSTETH));
        console.log("");
        console.log("Done! Arbitrum ZIN Pool can now flash loan these tokens.");
    }
}