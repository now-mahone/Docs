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
 * @dev Tests cover:
 *      - Basic arbitrage execution
 *      - Flash loan integration
 *      - Profit distribution (Treasury/Insurance)
 *      - Min profit thresholds
 *      - DEX routing (Aerodrome/Uniswap)
 *      - Access control
 *      - Emergency functions
 */
contract KerneFlashArbBotTest is Test {
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // TEST STATE
    // ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // SETUP
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function setUp() public {
        vm.startPrank(admin);
        
        // Deploy mock tokens
        kUSD = new ERC20Mock();
        usdc = new ERC20Mock();
        weth = new ERC20Mock();
        
        // Deploy mock DEX routers
        aeroRouter = new MockAerodromeRouter();
        uniRouter = new MockUniswapV3Router();
        
        // Deploy PSM (flash loan source)
        psm = new KUSDPSM(address(kUSD), admin);
        psm.addStable(address(usdc), 10, type(uint256).max); // 0.1% fee
        psm.setFlashFee(0); // 0% flash fee for arb bot
        
        // Deploy arb bot
        arbBot = new KerneFlashArbBot(
            admin,
            treasury,
            insuranceFund,
            vault,
            address(psm),
            address(aeroRouter),
            address(uniRouter)
        );
        
        // Grant ARBITRAGEUR_ROLE to arb bot in PSM
        psm.grantRole(psm.ARBITRAGEUR_ROLE(), address(arbBot));
        
        // Grant EXECUTOR_ROLE to executor
        arbBot.grantRole(arbBot.EXECUTOR_ROLE(), executor);
        
        // Approve tokens in arb bot
        arbBot.setTokenApproval(address(kUSD), true);
        arbBot.setTokenApproval(address(usdc), true);
        arbBot.setTokenApproval(address(weth), true);
        
        vm.stopPrank();
        
        // Mint initial balances
        kUSD.mint(address(psm), INITIAL_BALANCE);
        usdc.mint(address(psm), INITIAL_BALANCE);
        kUSD.mint(address(aeroRouter), INITIAL_BALANCE);
        usdc.mint(address(aeroRouter), INITIAL_BALANCE);
        weth.mint(address(aeroRouter), INITIAL_BALANCE);
        kUSD.mint(address(uniRouter), INITIAL_BALANCE);
        usdc.mint(address(uniRouter), INITIAL_BALANCE);
        weth.mint(address(uniRouter), INITIAL_BALANCE);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // INITIALIZATION TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_Initialization() public view {
        assertEq(arbBot.treasury(), treasury);
        assertEq(arbBot.insuranceFund(), insuranceFund);
        assertEq(arbBot.vault(), vault);
        assertEq(arbBot.psm(), address(psm));
        assertEq(arbBot.insuranceSplitBps(), 2000); // 20%
        assertEq(arbBot.minProfitBps(), 5); // 0.05%
        assertTrue(arbBot.sentinelActive());
    }
    
    function test_RolesGranted() public view {
        assertTrue(arbBot.hasRole(arbBot.DEFAULT_ADMIN_ROLE(), admin));
        assertTrue(arbBot.hasRole(arbBot.EXECUTOR_ROLE(), admin));
        assertTrue(arbBot.hasRole(arbBot.EXECUTOR_ROLE(), executor));
        assertTrue(arbBot.hasRole(arbBot.SENTINEL_ROLE(), admin));
    }
    
    function test_LendersApproved() public view {
        assertTrue(arbBot.approvedLenders(address(psm)));
        assertTrue(arbBot.approvedLenders(vault));
    }
    
    function test_TokensApproved() public view {
        assertTrue(arbBot.approvedTokens(address(kUSD)));
        assertTrue(arbBot.approvedTokens(address(usdc)));
        assertTrue(arbBot.approvedTokens(address(weth)));
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ARBITRAGE EXECUTION TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_ExecuteArbitrage_ProfitableAero() public {
        // Setup: Aerodrome has better rate (buy on Aero, get profit)
        // Rate: 1 kUSD = 1.01 USDC on Aerodrome
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1.01e18);
        aeroRouter.setMockRate(address(usdc), address(kUSD), 1e18);
        
        uint256 borrowAmount = 1000 ether;
        
        // Build swap params
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        
        // Swap 1: kUSD → USDC on Aerodrome
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            tokenIn: address(kUSD),
            tokenOut: address(usdc),
            amountIn: borrowAmount,
            minAmountOut: 1,
            stable: true,
            fee: 0,
            extraData: ""
        });
        
        // Swap 2: USDC → kUSD on Aerodrome (sell back)
        swaps[1] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
            tokenIn: address(usdc),
            tokenOut: address(kUSD),
            amountIn: 0, // Will be set from previous swap
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
        
        uint256 treasuryBefore = kUSD.balanceOf(treasury);
        uint256 insuranceBefore = kUSD.balanceOf(insuranceFund);
        
        vm.prank(executor);
        arbBot.executeArbitrage(params);
        
        // Check profits were distributed
        uint256 treasuryAfter = kUSD.balanceOf(treasury);
        uint256 insuranceAfter = kUSD.balanceOf(insuranceFund);
        
        assertGt(treasuryAfter, treasuryBefore, "Treasury should receive profit");
        assertGt(insuranceAfter, insuranceBefore, "Insurance should receive profit");
        
        // 80% to treasury, 20% to insurance
        uint256 totalProfit = (treasuryAfter - treasuryBefore) + (insuranceAfter - insuranceBefore);
        assertApproxEqRel(
            treasuryAfter - treasuryBefore,
            totalProfit * 80 / 100,
            0.01e18 // 1% tolerance
        );
    }
    
    function test_ExecuteArbitrage_UniswapPath() public {
        // Setup: Buy on Uniswap (cheaper), sell on Aerodrome (more expensive)
        uniRouter.setMockRate(address(weth), address(usdc), 3000e6); // 1 WETH = 3000 USDC
        uniRouter.setMockRate(address(usdc), address(weth), 0.00033e18); // Sell back
        
        aeroRouter.setMockRate(address(usdc), address(weth), 0.00034e18); // 1% better
        aeroRouter.setMockRate(address(weth), address(usdc), 2950e6);
        
        // Mint WETH to PSM for lending
        weth.mint(address(psm), 100 ether);
        
        vm.prank(admin);
        psm.addStable(address(weth), 0, type(uint256).max);
        
        uint256 borrowAmount = 1 ether;
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        
        // Buy USDC with WETH on Uniswap
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.UniswapV3,
            tokenIn: address(weth),
            tokenOut: address(usdc),
            amountIn: borrowAmount,
            minAmountOut: 1,
            stable: false,
            fee: 500,
            extraData: ""
        });
        
        // Sell USDC for WETH on Aerodrome
        swaps[1] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
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
        
        // Verify profit was distributed
        assertGt(weth.balanceOf(treasury), 0, "Treasury should receive WETH profit");
    }
    
    function test_ExecuteArbitrage_RevertUnprofitable() public {
        // Setup: No spread (same rates)
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1e18);
        aeroRouter.setMockRate(address(usdc), address(kUSD), 1e18);
        
        uint256 borrowAmount = 1000 ether;
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
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
        vm.expectRevert(); // ArbNotProfitable
        arbBot.executeArbitrage(params);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ACCESS CONTROL TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
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
    
    function test_OnlyAdminCanSetLenderApproval() public {
        vm.prank(attacker);
        vm.expectRevert();
        arbBot.setLenderApproval(address(0x999), true);
    }
    
    function test_OnlyAdminCanSetTokenApproval() public {
        vm.prank(attacker);
        vm.expectRevert();
        arbBot.setTokenApproval(address(0x999), true);
    }
    
    function test_UnauthorizedLenderReverts() public {
        address fakeLender = address(0x999);
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](1);
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: fakeLender,
            borrowToken: address(kUSD),
            borrowAmount: 1000 ether,
            swaps: swaps
        });
        
        vm.prank(executor);
        vm.expectRevert(KerneFlashArbBot.UnauthorizedLender.selector);
        arbBot.executeArbitrage(params);
    }
    
    function test_UnauthorizedTokenReverts() public {
        ERC20Mock fakeToken = new ERC20Mock();
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](1);
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(fakeToken),
            borrowAmount: 1000 ether,
            swaps: swaps
        });
        
        vm.prank(executor);
        vm.expectRevert(KerneFlashArbBot.UnauthorizedToken.selector);
        arbBot.executeArbitrage(params);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // PROFIT DISTRIBUTION TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_ProfitSplit_80_20() public {
        // Setup profitable arb
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1.10e18); // 10% profit
        aeroRouter.setMockRate(address(usdc), address(kUSD), 1e18);
        
        uint256 borrowAmount = 1000 ether;
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](2);
        swaps[0] = KerneFlashArbBot.SwapParams({
            dex: KerneFlashArbBot.DEX.Aerodrome,
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
        
        uint256 treasuryProfit = kUSD.balanceOf(treasury);
        uint256 insuranceProfit = kUSD.balanceOf(insuranceFund);
        
        // Verify 80/20 split
        uint256 total = treasuryProfit + insuranceProfit;
        assertApproxEqRel(treasuryProfit, total * 80 / 100, 0.01e18);
        assertApproxEqRel(insuranceProfit, total * 20 / 100, 0.01e18);
    }
    
    function test_UpdateInsuranceSplit() public {
        vm.prank(admin);
        arbBot.setInsuranceSplit(3000); // 30%
        assertEq(arbBot.insuranceSplitBps(), 3000);
    }
    
    function test_InsuranceSplitMaxLimit() public {
        vm.prank(admin);
        vm.expectRevert("Max 50%");
        arbBot.setInsuranceSplit(6000); // 60% - over limit
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // PRICE QUERY TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_GetAerodromeQuote() public {
        aeroRouter.setMockRate(address(kUSD), address(usdc), 1.05e18);
        
        uint256 quote = arbBot.getAerodromeQuote(
            address(kUSD),
            address(usdc),
            1 ether,
            true
        );
        
        assertEq(quote, 1.05e18);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // EMERGENCY FUNCTIONS TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_EmergencyWithdraw() public {
        // Send tokens to arb bot
        kUSD.mint(address(arbBot), 100 ether);
        
        uint256 adminBefore = kUSD.balanceOf(admin);
        
        vm.prank(admin);
        arbBot.emergencyWithdraw(address(kUSD));
        
        uint256 adminAfter = kUSD.balanceOf(admin);
        assertEq(adminAfter - adminBefore, 100 ether);
        assertEq(kUSD.balanceOf(address(arbBot)), 0);
    }
    
    function test_EmergencyWithdrawETH() public {
        // Send ETH to arb bot
        vm.deal(address(arbBot), 1 ether);
        
        uint256 adminBefore = admin.balance;
        
        vm.prank(admin);
        arbBot.emergencyWithdrawETH();
        
        uint256 adminAfter = admin.balance;
        assertEq(adminAfter - adminBefore, 1 ether);
        assertEq(address(arbBot).balance, 0);
    }
    
    function test_OnlyAdminCanEmergencyWithdraw() public {
        kUSD.mint(address(arbBot), 100 ether);
        
        vm.prank(attacker);
        vm.expectRevert();
        arbBot.emergencyWithdraw(address(kUSD));
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // PAUSE TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_PauseAndUnpause() public {
        vm.prank(admin);
        arbBot.pause();
        assertTrue(arbBot.paused());
        
        KerneFlashArbBot.SwapParams[] memory swaps = new KerneFlashArbBot.SwapParams[](1);
        KerneFlashArbBot.ArbParams memory params = KerneFlashArbBot.ArbParams({
            lender: address(psm),
            borrowToken: address(kUSD),
            borrowAmount: 1000 ether,
            swaps: swaps
        });
        
        vm.prank(executor);
        vm.expectRevert(); // Pausable: paused
        arbBot.executeArbitrage(params);
        
        vm.prank(admin);
        arbBot.unpause();
        assertFalse(arbBot.paused());
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // SENTINEL TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_ToggleSentinel() public {
        assertTrue(arbBot.sentinelActive());
        
        vm.prank(admin);
        arbBot.toggleSentinel(false);
        assertFalse(arbBot.sentinelActive());
        
        vm.prank(admin);
        arbBot.toggleSentinel(true);
        assertTrue(arbBot.sentinelActive());
    }
    
    function test_SetMinProfitBps() public {
        vm.prank(admin);
        arbBot.setMinProfitBps(10); // 0.1%
        assertEq(arbBot.minProfitBps(), 10);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ROUTER UPDATE TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_SetRouters() public {
        address newAero = address(0x111);
        address newUni = address(0x222);
        
        // Deploy mocks at these addresses for factory call
        MockAerodromeRouter newAeroRouter = new MockAerodromeRouter();
        
        vm.prank(admin);
        arbBot.setRouters(address(newAeroRouter), newUni);
        
        assertEq(address(arbBot.aerodromeRouter()), address(newAeroRouter));
        assertEq(address(arbBot.uniswapRouter()), newUni);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // FUZZ TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function testFuzz_InsuranceSplit(uint256 bps) public {
        bps = bound(bps, 0, 5000);
        
        vm.prank(admin);
        arbBot.setInsuranceSplit(bps);
        
        assertEq(arbBot.insuranceSplitBps(), bps);
    }
    
    function testFuzz_MinProfitBps(uint256 bps) public {
        bps = bound(bps, 1, 1000);
        
        vm.prank(admin);
        arbBot.setMinProfitBps(bps);
        
        assertEq(arbBot.minProfitBps(), bps);
    }
}
