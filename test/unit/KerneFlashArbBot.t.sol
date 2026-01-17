// Created: 2026-01-15
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import { KerneFlashArbBot } from "../../src/KerneFlashArbBot.sol";
import { KUSDPSM } from "../../src/KUSDPSM.sol";
import { MockAerodromeRouter } from "../../src/mocks/MockAerodromeRouter.sol";
import { MockUniswapV3Router } from "../../src/mocks/MockUniswapV3Router.sol";
import { ERC20Mock } from "@openzeppelin/contracts/mocks/token/ERC20Mock.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

/**
 * @title KerneFlashArbBotTest
 * @notice Comprehensive tests for the Flash Arbitrage Bot
 */
contract KerneFlashArbBotTest is Test {
    
    KerneFlashArbBot public arbBot;
    KUSDPSM public psm;
    MockAerodromeRouter public aeroRouter;
    MockUniswapV3Router public uniRouter;
    
    ERC20Mock public kUSD;
    ERC20Mock public usdc;
    ERC20Mock public weth;
    
    address public admin = address(0x1);
    address public executor = address(0x2);
    address public treasury = address(0x3);
    address public insuranceFund = address(0x4);
    address public vault = address(0x5);
    address public attacker = address(0x666);
    
    uint256 constant INITIAL_BALANCE = 1_000_000 ether;
    
    function setUp() public {
        vm.startPrank(admin);
        
        kUSD = new ERC20Mock();
        usdc = new ERC20Mock();
        weth = new ERC20Mock();
        
        aeroRouter = new MockAerodromeRouter();
        uniRouter = new MockUniswapV3Router();
        
        psm = new KUSDPSM(address(kUSD), admin);
        psm.addStable(address(usdc), 10, type(uint256).max);
        psm.setFlashFee(0);
        
        arbBot = new KerneFlashArbBot(
            admin,
            treasury,
            insuranceFund,
            vault,
            address(psm),
            address(aeroRouter),
            address(uniRouter),
            address(0) // Maverick Router
        );
        
        psm.grantRole(psm.ARBITRAGEUR_ROLE(), address(arbBot));
        arbBot.grantRole(arbBot.EXECUTOR_ROLE(), executor);
        arbBot.setTokenApproval(address(kUSD), true);
        arbBot.setTokenApproval(address(usdc), true);
        arbBot.setTokenApproval(address(weth), true);
        arbBot.toggleSentinel(false);
        
        vm.stopPrank();
        
        kUSD.mint(address(psm), INITIAL_BALANCE);
        usdc.mint(address(psm), INITIAL_BALANCE);
        kUSD.mint(address(aeroRouter), INITIAL_BALANCE);
        usdc.mint(address(aeroRouter), INITIAL_BALANCE);
        weth.mint(address(aeroRouter), INITIAL_BALANCE);
        kUSD.mint(address(uniRouter), INITIAL_BALANCE);
        usdc.mint(address(uniRouter), INITIAL_BALANCE);
        weth.mint(address(uniRouter), INITIAL_BALANCE);
    }
    
    function test_Initialization() public view {
        assertEq(arbBot.treasury(), treasury);
        assertEq(arbBot.insuranceFund(), insuranceFund);
        assertEq(arbBot.vault(), vault);
        assertEq(arbBot.psm(), address(psm));
    }
    
    function test_ExecuteArbitrage_ProfitableAero() public {
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1.01e18);
        aeroRouter.setMockRate(address(usdc), address(kUSD), 1e18);
        uint256 borrowAmount = 1000 ether;
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            router: address(0),
            tokenIn: address(kUSD),
            tokenOut: address(usdc),
            amountIn: borrowAmount,
            minAmountOut: 1,
            stable: true,
            fee: 0,
            extraData: ""
        });
        swaps[1] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            router: address(0),
            tokenIn: address(usdc),
            tokenOut: address(kUSD),
            amountIn: 0,
            minAmountOut: borrowAmount,
            stable: true,
            fee: 0,
            extraData: ""
        });
        
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(kUSD),
            borrowAmount: borrowAmount,
            swaps: swaps
        });
        
        vm.prank(executor);
        arbBot.executeArbitrage(params);
        
        assertGt(kUSD.balanceOf(treasury), 0);
        assertGt(kUSD.balanceOf(insuranceFund), 0);
    }
    
    function test_ExecuteArbitrage_UniswapPath() public {
        uniRouter.setMockRate(address(weth), address(usdc), 3000e18); // 1 WETH = 3000 USDC
        uniRouter.setMockRate(address(usdc), address(weth), 0.00033e18); 
        aeroRouter.setMockRate(address(usdc), address(weth), 0.00034e18); 
        
        weth.mint(address(psm), 100 ether);
        vm.prank(admin);
        psm.addStable(address(weth), 0, type(uint256).max);
        
        uint256 borrowAmount = 1 ether;
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.UniswapV3,
            router: address(0),
            tokenIn: address(weth),
            tokenOut: address(usdc),
            amountIn: borrowAmount,
            minAmountOut: 1,
            stable: false,
            fee: 500,
            extraData: ""
        });
        swaps[1] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            router: address(0),
            tokenIn: address(usdc),
            tokenOut: address(weth),
            amountIn: 0,
            minAmountOut: borrowAmount,
            stable: false,
            fee: 0,
            extraData: ""
        });
        
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(weth),
            borrowAmount: borrowAmount,
            swaps: swaps
        });
        
        vm.prank(executor);
        arbBot.executeArbitrage(params);
        assertGt(weth.balanceOf(treasury), 0);
    }
    
    function test_ExecuteArbitrage_RevertUnprofitable() public {
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1e18);
        aeroRouter.setMockRate(address(usdc), address(kUSD), 1e18);
        uint256 borrowAmount = 1000 ether;
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            router: address(0),
            tokenIn: address(kUSD),
            tokenOut: address(usdc),
            amountIn: borrowAmount,
            minAmountOut: 1,
            stable: true,
            fee: 0,
            extraData: ""
        });
        swaps[1] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            router: address(0),
            tokenIn: address(usdc),
            tokenOut: address(kUSD),
            amountIn: 0,
            minAmountOut: borrowAmount,
            stable: true,
            fee: 0,
            extraData: ""
        });
        
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(kUSD),
            borrowAmount: borrowAmount,
            swaps: swaps
        });
        
        vm.prank(executor);
        vm.expectRevert();
        arbBot.executeArbitrage(params);
    }
    
    function test_OnlyExecutorCanExecute() public {
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](1);
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(kUSD),
            borrowAmount: 1000 ether,
            swaps: swaps
        });
        vm.prank(attacker);
        vm.expectRevert();
        arbBot.executeArbitrage(params);
    }

    function test_EmergencyWithdraw() public {
        kUSD.mint(address(arbBot), 100 ether);
        uint256 adminBefore = kUSD.balanceOf(admin);
        vm.prank(admin);
        arbBot.emergencyWithdraw(address(kUSD));
        assertEq(kUSD.balanceOf(admin) - adminBefore, 100 ether);
    }
}
