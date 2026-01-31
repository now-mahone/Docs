// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Script.sol";
import "../src/KerneZINPool.sol";

/**
 * @title EnableZINTokensArbitrum
 * @notice Whitelists tokens in the KerneZINPool on Arbitrum One
 * @dev Run with: forge script script/EnableZINTokensArbitrum.s.sol --rpc-url $ARB_RPC_URL --broadcast
 */
contract EnableZINTokensArbitrum is Script {
    address constant ZIN_POOL = 0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD;
    
    // Arbitrum One Addresses
    address constant USDC_NATIVE = 0xaf88d065e77c8cC2239327C5EDb3A432268e5831;
    address constant USDC_E = 0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8;
    address constant WETH = 0x82aF49447D8a07e3bd95BD0d56f35241523fBab1;
    address constant WSTETH = 0x5979D7b546E38E414F7E9822514be443A4800529;

    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address deployer = vm.addr(deployerPrivateKey);
        
        vm.startBroadcast(deployerPrivateKey);
        
        KerneZINPool pool = KerneZINPool(payable(ZIN_POOL));
        
        console.log("=== Enabling ZIN Tokens on Arbitrum ===");
        console.log("Pool:", ZIN_POOL);
        console.log("Deployer:", deployer);
        
        // Whitelist tokens
        _supportToken(pool, USDC_NATIVE, "USDC (Native)");
        _supportToken(pool, USDC_E, "USDC.e (Bridged)");
        _supportToken(pool, WETH, "WETH");
        _supportToken(pool, WSTETH, "wstETH");
        
        vm.stopBroadcast();
        
        console.log("=== Token Whitelisting Complete ===");
    }
    
    function _supportToken(KerneZINPool pool, address token, string memory name) internal {
        if (pool.supportedTokens(token)) {
            console.log(string.concat(name, " is already supported"));
        } else {
            console.log(string.concat("Enabling ", name, "..."));
            pool.supportToken(token);
            console.log(string.concat(name, " enabled!"));
        }
    }
}
