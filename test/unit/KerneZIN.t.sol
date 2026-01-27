// SPDX-License-Identifier: MIT
// Created: 2026-01-17
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { IERC3156FlashBorrower } from "@openzeppelin/contracts/interfaces/IERC3156FlashBorrower.sol";
import { KerneZINPool } from "../../src/KerneZINPool.sol";
import { KerneZINRouter } from "../../src/KerneZINRouter.sol";
import { KerneIntentExecutorV2 } from "../../src/KerneIntentExecutorV2.sol";
import { KerneVault } from "../../src/KerneVault.sol";
import { MockERC20 } from "../../src/mocks/MockERC20.sol";

contract MockAggregator {
    function swap(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 amountOut,
        address payer,
        address recipient
    ) external {
        IERC20(tokenIn).transferFrom(payer, address(this), amountIn);
        IERC20(tokenOut).transfer(recipient, amountOut);
    }
}

contract MockFlashBorrower is IERC3156FlashBorrower {
    IERC20 public immutable token;

    constructor(IERC20 token_) {
        token = token_;
    }

    function onFlashLoan(
        address,
        address,
        uint256 amount,
        uint256 fee,
        bytes calldata
    ) external override returns (bytes32) {
        token.approve(msg.sender, amount + fee);
        return keccak256("ERC3156FlashBorrower.onFlashLoan");
    }
}

/**
 * @title KerneZINTest
 * @notice Comprehensive test suite for the Zero-Fee Intent Network (ZIN)
 */
contract KerneZINTest is Test {
    // Contracts
    KerneZINPool public zinPool;
    KerneZINRouter public zinRouter;
    KerneIntentExecutorV2 public zinExecutor;
    KerneVault public vault;
    
    // Mock tokens
    MockERC20 public weth;
    MockERC20 public usdc;
    MockERC20 public kusd;
    
    // Users
    address public admin = address(0x1);
    address public solver = address(0x2);
    address public user = address(0x3);
    address public profitVault = address(0x4);
    address public treasury = address(0x5);
    address public exchangeDeposit = address(0x6);
    
    // Constants
    uint256 constant INITIAL_LIQUIDITY = 1_000_000e18;
    uint256 constant USER_BALANCE = 100e18;
    
    function setUp() public {
        vm.startPrank(admin);
        
        // Deploy mock tokens
        weth = new MockERC20("Wrapped ETH", "WETH", 18);
        usdc = new MockERC20("USD Coin", "USDC", 6);
        kusd = new MockERC20("Kerne USD", "kUSD", 18);
        
        // Deploy vault
        vault = new KerneVault(
            IERC20(address(weth)),
            "Kerne WETH Vault",
            "kvWETH",
            admin,
            admin,
            exchangeDeposit
        );
        vault.setFlashFee(0);
        
        // Deploy ZIN Pool
        zinPool = new KerneZINPool(admin, treasury);
        
        // Deploy ZIN Router
        zinRouter = new KerneZINRouter(admin, address(vault), address(0), treasury);
        
        // Deploy ZIN Executor
        zinExecutor = new KerneIntentExecutorV2(admin, solver, profitVault);

        vm.etch(zinExecutor.ONE_INCH_ROUTER(), address(new MockAggregator()).code);
        
        // Setup roles
        zinPool.grantRole(zinPool.SOLVER_ROLE(), solver);
        zinPool.grantRole(zinPool.SOLVER_ROLE(), address(zinRouter));
        zinRouter.grantRole(zinRouter.SOLVER_ROLE(), solver);
        
        // Support tokens
        zinPool.supportToken(address(weth));
        zinPool.supportToken(address(usdc));
        zinPool.supportToken(address(kusd));
        
        // Seed liquidity
        weth.mint(address(vault), INITIAL_LIQUIDITY);
        weth.mint(address(zinPool), INITIAL_LIQUIDITY);
        usdc.mint(address(zinPool), INITIAL_LIQUIDITY / 1e12); // 6 decimals
        kusd.mint(address(zinPool), INITIAL_LIQUIDITY);

        // Seed aggregator with output liquidity
        address oneInch = zinExecutor.ONE_INCH_ROUTER();
        usdc.mint(oneInch, INITIAL_LIQUIDITY / 1e12); // 6 decimals
        weth.mint(oneInch, INITIAL_LIQUIDITY);
        
        // Give user some tokens
        weth.mint(user, USER_BALANCE);
        usdc.mint(user, USER_BALANCE / 1e12);
        
        vm.stopPrank();
    }
    
    // ============ ZIN Pool Tests ============
    
    function test_ZINPool_SupportToken() public {
        vm.prank(admin);
        zinPool.supportToken(address(0x123));
        assertTrue(zinPool.supportedTokens(address(0x123)));
    }
    
    function test_ZINPool_GetAvailableLiquidity() public view {
        uint256 liquidity = zinPool.getAvailableLiquidity(address(weth));
        assertEq(liquidity, INITIAL_LIQUIDITY);
    }
    
    function test_ZINPool_AddLiquiditySource() public {
        vm.startPrank(admin);
        zinPool.addLiquiditySource(address(weth), address(vault), 1);
        
        uint256 liquidity = zinPool.getAvailableLiquidity(address(weth));
        assertEq(liquidity, INITIAL_LIQUIDITY * 2); // Pool + Vault
        vm.stopPrank();
    }
    
    function test_ZINPool_FlashLoan_ZeroFeeForSolver() public {
        vm.startPrank(solver);
        uint256 fee = zinPool.flashFee(address(weth), 1000e18);
        assertEq(fee, 0); // Solver gets zero fee
        vm.stopPrank();
    }
    
    function test_ZINPool_FlashLoan_FeeForPublic() public {
        vm.startPrank(user);
        uint256 fee = zinPool.flashFee(address(weth), 10000e18);
        assertEq(fee, 30e18); // 0.30% of 10000 = 30
        vm.stopPrank();
    }
    
    function test_ZINPool_SetZinFee() public {
        vm.startPrank(admin);
        zinPool.setZinFee(50); // 0.50%
        
        vm.stopPrank();
        vm.prank(user);
        uint256 fee = zinPool.flashFee(address(weth), 10000e18);
        assertEq(fee, 50e18);
    }
    
    function test_ZINPool_ToggleLiquiditySource() public {
        vm.startPrank(admin);
        zinPool.addLiquiditySource(address(weth), address(vault), 1);
        
        uint256 liquidityBefore = zinPool.getAvailableLiquidity(address(weth));
        
        zinPool.toggleLiquiditySource(address(weth), address(vault), false);
        uint256 liquidityAfter = zinPool.getAvailableLiquidity(address(weth));
        
        assertEq(liquidityAfter, liquidityBefore - INITIAL_LIQUIDITY);
        vm.stopPrank();
    }

    function test_ZINPool_FillIntentInternal_TracksProfitAndVolume() public {
        uint256 amountOut = 10e18;
        uint256 tokenInBalanceBefore = usdc.balanceOf(address(zinPool));
        uint256 expectedProfit = (tokenInBalanceBefore * zinPool.zinFeeBps()) / 10000;
        uint256 userBalanceBefore = weth.balanceOf(user);
        uint256 profitRecipientBefore = usdc.balanceOf(treasury);
        uint256 volumeBefore = zinPool.totalVolumeFilled(address(weth));
        uint256 ordersBefore = zinPool.totalOrdersFilled();
        uint256 profitBefore = zinPool.totalProfitCaptured(address(usdc));

        vm.prank(solver);
        uint256 profit = zinPool.fillIntentInternal(address(usdc), address(weth), amountOut, user);

        assertEq(profit, expectedProfit);
        assertEq(weth.balanceOf(user), userBalanceBefore + amountOut);
        assertEq(usdc.balanceOf(treasury), profitRecipientBefore + expectedProfit);
        assertEq(zinPool.totalVolumeFilled(address(weth)), volumeBefore + amountOut);
        assertEq(zinPool.totalOrdersFilled(), ordersBefore + 1);
        assertEq(zinPool.totalProfitCaptured(address(usdc)), profitBefore + expectedProfit);
    }

    function test_ZINPool_FillIntentInternal_NoProfitOnSameToken() public {
        uint256 amountOut = 5e18;
        uint256 profitRecipientBefore = weth.balanceOf(treasury);
        uint256 profitBefore = zinPool.totalProfitCaptured(address(weth));

        vm.prank(solver);
        uint256 profit = zinPool.fillIntentInternal(address(weth), address(weth), amountOut, user);

        assertEq(profit, 0);
        assertEq(weth.balanceOf(treasury), profitRecipientBefore);
        assertEq(zinPool.totalProfitCaptured(address(weth)), profitBefore);
    }

    function test_ZINPool_FlashLoan_CapturesFee() public {
        MockFlashBorrower borrower = new MockFlashBorrower(IERC20(address(weth)));
        uint256 amount = 100e18;
        uint256 fee = zinPool.flashFee(address(weth), amount);

        weth.mint(address(borrower), fee);

        uint256 profitRecipientBefore = weth.balanceOf(treasury);
        uint256 profitBefore = zinPool.totalProfitCaptured(address(weth));

        bool success = zinPool.flashLoan(borrower, address(weth), amount, "");

        assertTrue(success);
        assertEq(weth.balanceOf(treasury), profitRecipientBefore + fee);
        assertEq(zinPool.totalProfitCaptured(address(weth)), profitBefore + fee);
    }
    
    // ============ ZIN Router Tests ============
    
    function test_ZINRouter_AnalyzeRoute_InternalVault() public view {
        (KerneZINRouter.RouteType route, uint256 estimated, uint256 internal_liq) = 
            zinRouter.analyzeRoute(address(weth), address(weth), 100e18);
        
        assertEq(uint256(route), uint256(KerneZINRouter.RouteType.INTERNAL_VAULT));
        assertEq(estimated, 100e18);
        assertGt(internal_liq, 0);
    }
    
    function test_ZINRouter_AnalyzeRoute_External() public view {
        // Request more than available in vault
        (KerneZINRouter.RouteType route, , ) = 
            zinRouter.analyzeRoute(address(weth), address(weth), INITIAL_LIQUIDITY * 10);
        
        assertEq(uint256(route), uint256(KerneZINRouter.RouteType.EXTERNAL_1INCH));
    }
    
    function test_ZINRouter_GetInternalLiquidity() public view {
        uint256 liquidity = zinRouter.getInternalLiquidity(address(weth));
        assertEq(liquidity, INITIAL_LIQUIDITY);
    }
    
    function test_ZINRouter_SetLiquiditySources() public {
        vm.startPrank(admin);
        zinRouter.setLiquiditySources(
            address(vault),
            address(0x123),
            address(zinPool)
        );
        
        assertEq(zinRouter.kusdPSM(), address(0x123));
        assertEq(zinRouter.zinPool(), address(zinPool));
        vm.stopPrank();
    }
    
    function test_ZINRouter_SetRoutingConfig() public {
        vm.startPrank(admin);
        zinRouter.setRoutingConfig(90, 10, 50);
        
        assertEq(zinRouter.internalLiquidityThreshold(), 90);
        assertEq(zinRouter.minProfitBps(), 10);
        assertEq(zinRouter.maxSlippageBps(), 50);
        vm.stopPrank();
    }
    
    function test_ZINRouter_GetMetrics() public view {
        (uint256 volume, uint256 profit, uint256 orders, address currentTreasury) = 
            zinRouter.getMetrics();
        
        assertEq(volume, 0);
        assertEq(profit, 0);
        assertEq(orders, 0);
        assertEq(currentTreasury, treasury);
    }

    function test_ZINRouter_ExecuteIntent_TracksProfitAndMetrics() public {
        KerneZINRouter.Intent memory intent = KerneZINRouter.Intent({
            user: user,
            tokenIn: address(weth),
            tokenOut: address(weth),
            amountIn: 1e18,
            minAmountOut: 1e18,
            deadline: block.timestamp + 1 hours,
            intentHash: keccak256("intent-1")
        });

        KerneZINRouter.Route[] memory routes = new KerneZINRouter.Route[](1);
        routes[0] = KerneZINRouter.Route({
            routeType: KerneZINRouter.RouteType.EXTERNAL_1INCH,
            source: address(0),
            percentage: 10000,
            callData: ""
        });

        uint256 userBalanceBefore = weth.balanceOf(user);
        uint256 treasuryBalanceBefore = weth.balanceOf(treasury);
        uint256 volumeBefore = zinRouter.totalVolume();
        uint256 profitBefore = zinRouter.totalProfit();
        uint256 ordersBefore = zinRouter.totalOrdersFilled();
        uint256 tokenVolumeBefore = zinRouter.tokenVolume(address(weth));
        uint256 tokenProfitBefore = zinRouter.tokenProfit(address(weth));

        bytes memory aggregatorData = abi.encodeWithSelector(
            MockAggregator.swap.selector,
            address(weth),
            address(weth),
            1e18,
            2e18,
            user,
            address(zinRouter)
        );

        vm.startPrank(user);
        weth.approve(zinExecutor.ONE_INCH_ROUTER(), 1e18);
        vm.stopPrank();

        vm.prank(solver);
        KerneZINRouter.ExecutionResult memory result = zinRouter.executeIntent(intent, routes, aggregatorData);

        assertTrue(result.success);
        assertEq(result.amountOut, 2e18);
        assertEq(result.profit, 1e18);
        assertEq(weth.balanceOf(user), userBalanceBefore);
        assertEq(weth.balanceOf(treasury), treasuryBalanceBefore + 1e18);
        assertEq(zinRouter.totalVolume(), volumeBefore + 1e18);
        assertEq(zinRouter.totalProfit(), profitBefore + 1e18);
        assertEq(zinRouter.totalOrdersFilled(), ordersBefore + 1);
        assertEq(zinRouter.tokenVolume(address(weth)), tokenVolumeBefore + 1e18);
        assertEq(zinRouter.tokenProfit(address(weth)), tokenProfitBefore + 1e18);
    }
    
    // ============ ZIN Executor V2 Tests ============
    
    function test_ZINExecutor_GetZINMetrics() public view {
        (uint256 totalSpread, uint256 totalIntents, address currentVault) = 
            zinExecutor.getZINMetrics();
        
        assertEq(totalSpread, 0);
        assertEq(totalIntents, 0);
        assertEq(currentVault, profitVault);
    }
    
    function test_ZINExecutor_SetProfitVault() public {
        address newVault = address(0x999);
        
        vm.prank(admin);
        zinExecutor.setProfitVault(newVault);
        
        assertEq(zinExecutor.profitVault(), newVault);
    }
    
    function test_ZINExecutor_UpdateSentinelParams() public {
        vm.prank(admin);
        zinExecutor.updateSentinelParams(1000, 200);
        
        assertEq(zinExecutor.maxLatency(), 1000);
        assertEq(zinExecutor.maxPriceDeviationBps(), 200);
    }
    
    function test_ZINExecutor_ToggleSentinel() public {
        vm.prank(admin);
        zinExecutor.toggleSentinel(false);
        
        assertFalse(zinExecutor.sentinelActive());
    }
    
    function test_ZINExecutor_GetTokenSpread() public view {
        uint256 spread = zinExecutor.getTokenSpread(address(weth));
        assertEq(spread, 0);
    }
    
    // ============ Access Control Tests ============
    
    function test_RevertWhen_ZINPool_NonAdminCannotSupportToken() public {
        vm.prank(user);
        vm.expectRevert();
        zinPool.supportToken(address(0x123));
    }
    
    function test_RevertWhen_ZINRouter_NonSolverCannotExecute() public {
        KerneZINRouter.Intent memory intent = KerneZINRouter.Intent({
            user: user,
            tokenIn: address(weth),
            tokenOut: address(weth),
            amountIn: 100e18,
            minAmountOut: 99e18,
            deadline: block.timestamp + 1 hours,
            intentHash: bytes32(0)
        });
        
        KerneZINRouter.Route[] memory routes = new KerneZINRouter.Route[](1);
        routes[0] = KerneZINRouter.Route({
            routeType: KerneZINRouter.RouteType.INTERNAL_VAULT,
            source: address(vault),
            percentage: 10000,
            callData: ""
        });
        
        vm.prank(user);
        vm.expectRevert();
        zinRouter.executeIntent(intent, routes, "");
    }
    
    function test_RevertWhen_ZINExecutor_NonSolverCannotFulfill() public {
        bytes memory safetyParams = abi.encode(block.timestamp, 1e18, 10);
        
        vm.prank(user);
        vm.expectRevert();
        zinExecutor.fulfillIntent(
            address(vault),
            address(weth),
            address(usdc),
            100e18,
            user,
            zinExecutor.ONE_INCH_ROUTER(),
            "",
            safetyParams
        );
    }

    
    function test_RevertWhen_ZINExecutor_NonAdminCannotSetProfitVault() public {
        vm.prank(user);
        vm.expectRevert();
        zinExecutor.setProfitVault(address(0x999));
    }
    
    // ============ Edge Case Tests ============
    
    function test_ZINPool_MaxFlashLoan() public view {
        uint256 maxLoan = zinPool.maxFlashLoan(address(weth));
        assertEq(maxLoan, INITIAL_LIQUIDITY);
    }
    
    function test_ZINPool_MaxFlashLoan_UnsupportedToken() public view {
        uint256 maxLoan = zinPool.maxFlashLoan(address(0x999));
        assertEq(maxLoan, 0);
    }
    
    function test_ZINPool_RemoveLiquiditySource() public {
        vm.startPrank(admin);
        zinPool.addLiquiditySource(address(weth), address(vault), 1);
        
        zinPool.removeLiquiditySource(address(weth), address(vault));
        
        // Should only have pool liquidity now
        uint256 liquidity = zinPool.getAvailableLiquidity(address(weth));
        assertEq(liquidity, INITIAL_LIQUIDITY);
        vm.stopPrank();
    }
    
    function test_RevertWhen_ZINPool_RemoveNonexistentSource() public {
        vm.prank(admin);
        vm.expectRevert("Source not found");
        zinPool.removeLiquiditySource(address(weth), address(0x999));
    }
    
    // ============ Integration Test ============
    
    function test_Integration_LiquidityAggregation() public {
        vm.startPrank(admin);
        
        // Add vault as liquidity source
        zinPool.addLiquiditySource(address(weth), address(vault), 1);
        
        // Set ZIN Pool in router
        zinRouter.setLiquiditySources(address(vault), address(0), address(zinPool));
        
        // Check total internal liquidity through router
        uint256 totalLiquidity = zinRouter.getInternalLiquidity(address(weth));
        
        // Should be vault + pool liquidity
        assertEq(totalLiquidity, INITIAL_LIQUIDITY * 2);
        
        vm.stopPrank();
    }
    
    // ============ Gas Optimization Tests ============
    
    function test_Gas_AnalyzeRoute() public {
        uint256 gasBefore = gasleft();
        zinRouter.analyzeRoute(address(weth), address(weth), 100e18);
        uint256 gasUsed = gasBefore - gasleft();
        
        // Should be under 50k gas for route analysis
        assertLt(gasUsed, 50000);
    }
    
    function test_Gas_GetAvailableLiquidity() public {
        uint256 gasBefore = gasleft();
        zinPool.getAvailableLiquidity(address(weth));
        uint256 gasUsed = gasBefore - gasleft();
        
        // Should be under 30k gas
        assertLt(gasUsed, 30000);
    }

    // ============ ZIN Invariant Tests ============

    function test_ZINExecutor_RevertWhenIntentExpired() public {
        vm.warp(100);
        bytes memory safetyParams = abi.encode(block.timestamp - 10, 1e18, 10);
        bytes memory aggregatorData = "";

        vm.prank(solver);
        vm.expectRevert("Sentinel: Intent expired (Latency)");
        zinExecutor.fulfillIntent(
            address(vault),
            address(weth),
            address(usdc),
            10e18,
            user,
            zinExecutor.ONE_INCH_ROUTER(),
            aggregatorData,
            safetyParams
        );
    }

    function test_ZINExecutor_ProfitCapturedToVault() public {
        uint256 amountOut = 10e18;
        uint256 aggregatorOut = 12e18;
        bytes memory aggregatorData = abi.encodeWithSelector(
            MockAggregator.swap.selector,
            address(weth),
            address(weth),
            amountOut,
            aggregatorOut,
            user,
            address(zinExecutor)
        );
        bytes memory safetyParams = abi.encode(block.timestamp, 1e18, 10);

        vm.startPrank(user);
        weth.approve(zinExecutor.ONE_INCH_ROUTER(), amountOut);
        vm.stopPrank();

        uint256 profitBefore = weth.balanceOf(profitVault);
        uint256 totalSpreadBefore = zinExecutor.totalSpreadCaptured();
        uint256 tokenSpreadBefore = zinExecutor.getTokenSpread(address(weth));

        vm.prank(solver);
        zinExecutor.fulfillIntent(
            address(vault),
            address(weth),
            address(weth),
            amountOut,
            user,
            zinExecutor.ONE_INCH_ROUTER(),
            aggregatorData,
            safetyParams
        );

        uint256 expectedProfit = aggregatorOut - amountOut;
        assertEq(weth.balanceOf(profitVault), profitBefore + expectedProfit);
        assertEq(zinExecutor.totalSpreadCaptured(), totalSpreadBefore + expectedProfit);
        assertEq(zinExecutor.getTokenSpread(address(weth)), tokenSpreadBefore + expectedProfit);
        assertEq(zinExecutor.totalIntentsFulfilled(), 1);
    }

    function test_ZINExecutor_NoProfitDoesNotUpdateTotals() public {
        uint256 amountOut = 10e18;
        uint256 aggregatorOut = 10e18;
        bytes memory aggregatorData = abi.encodeWithSelector(
            MockAggregator.swap.selector,
            address(weth),
            address(weth),
            amountOut,
            aggregatorOut,
            user,
            address(zinExecutor)
        );
        bytes memory safetyParams = abi.encode(block.timestamp, 1e18, 10);

        vm.startPrank(user);
        weth.approve(zinExecutor.ONE_INCH_ROUTER(), amountOut);
        vm.stopPrank();

        vm.prank(solver);
        zinExecutor.fulfillIntent(
            address(vault),
            address(weth),
            address(weth),
            amountOut,
            user,
            zinExecutor.ONE_INCH_ROUTER(),
            aggregatorData,
            safetyParams
        );

        assertEq(zinExecutor.totalSpreadCaptured(), 0);
        assertEq(zinExecutor.totalIntentsFulfilled(), 0);
        assertEq(zinExecutor.getTokenSpread(address(weth)), 0);
    }

    function test_ZINExecutor_FulfillFusionIntent() public {
        uint256 amountOut = 10e18;
        uint256 aggregatorOut = 11e18;
        address fusionSettler = address(0x123);
        vm.etch(fusionSettler, address(new MockAggregator()).code);
        
        bytes memory aggregatorData = abi.encodeWithSelector(
            MockAggregator.swap.selector,
            address(weth),
            address(weth),
            amountOut,
            aggregatorOut,
            user,
            address(zinExecutor)
        );
        bytes memory safetyParams = abi.encode(block.timestamp, 1e18, 10);

        vm.startPrank(user);
        weth.approve(fusionSettler, amountOut);
        vm.stopPrank();

        vm.prank(solver);
        zinExecutor.fulfillIntent(
            address(vault),
            address(weth),
            address(weth),
            amountOut,
            user,
            fusionSettler,
            aggregatorData,
            safetyParams
        );

        assertEq(zinExecutor.totalIntentsFulfilled(), 1);
        assertEq(zinExecutor.totalSpreadCaptured(), 1e18);
    }


    function test_ZINRouter_RevertOnExpiredIntent() public {
        KerneZINRouter.Intent memory intent = KerneZINRouter.Intent({
            user: user,
            tokenIn: address(weth),
            tokenOut: address(weth),
            amountIn: 100e18,
            minAmountOut: 99e18,
            deadline: block.timestamp - 1,
            intentHash: bytes32("expired")
        });

        KerneZINRouter.Route[] memory routes = new KerneZINRouter.Route[](1);
        routes[0] = KerneZINRouter.Route({
            routeType: KerneZINRouter.RouteType.INTERNAL_VAULT,
            source: address(vault),
            percentage: 10000,
            callData: ""
        });

        vm.prank(solver);
        vm.expectRevert("Intent expired");
        zinRouter.executeIntent(intent, routes, "");
    }

    function test_ZINRouter_RevertOnSlippageExceeded() public {
        KerneZINRouter.Intent memory intent = KerneZINRouter.Intent({
            user: user,
            tokenIn: address(weth),
            tokenOut: address(weth),
            amountIn: 100e18,
            minAmountOut: 99e18,
            deadline: block.timestamp + 1 hours,
            intentHash: bytes32("slippage")
        });

        KerneZINRouter.Route[] memory routes = new KerneZINRouter.Route[](1);
        routes[0] = KerneZINRouter.Route({
            routeType: KerneZINRouter.RouteType.EXTERNAL_1INCH,
            source: address(0),
            percentage: 10000,
            callData: ""
        });

        bytes memory aggregatorData = abi.encodeWithSelector(
            MockAggregator.swap.selector,
            address(weth),
            address(weth),
            1e18,
            0,
            user,
            address(zinRouter)
        );

        vm.startPrank(user);
        weth.approve(zinExecutor.ONE_INCH_ROUTER(), 1e18);
        vm.stopPrank();

        vm.prank(solver);
        vm.expectRevert("Slippage exceeded");
        zinRouter.executeIntent(intent, routes, aggregatorData);
    }
}
