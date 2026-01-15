// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../../src/KerneTreasury.sol";
import "../../src/mocks/MockAerodromeRouter.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

/**
 * @title MockERC20
 * @notice Simple mock ERC20 for testing
 */
contract MockERC20 is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}
    
    function mint(address to, uint256 amount) external {
        _mint(to, amount);
    }
}

/**
 * @title KerneTreasuryTest
 * @notice Comprehensive tests for KerneTreasury buyback functionality
 */
contract KerneTreasuryTest is Test {
    KerneTreasury public treasury;
    MockAerodromeRouter public router;
    MockERC20 public weth;
    MockERC20 public kerne;
    MockERC20 public usdc;
    
    address public founder = address(0x1);
    address public stakingContract = address(0x2);
    address public owner = address(this);
    address public user = address(0x3);
    
    uint256 public constant INITIAL_BALANCE = 1000e18;
    
    event FeesDistributed(address indexed token, uint256 founderAmount, uint256 buybackAmount);
    event BuybackExecuted(
        address indexed inputToken,
        uint256 amountIn,
        uint256 kerneReceived,
        address indexed destination
    );
    event BuybackTokenApproved(address indexed token, bool approved);
    event SlippageUpdated(uint256 oldSlippage, uint256 newSlippage);
    
    function setUp() public {
        // Deploy mock tokens
        weth = new MockERC20("Wrapped ETH", "WETH");
        kerne = new MockERC20("Kerne Token", "KERNE");
        usdc = new MockERC20("USD Coin", "USDC");
        
        // Deploy mock router
        router = new MockAerodromeRouter(address(weth));
        
        // Fund router with KERNE for swaps
        kerne.mint(address(router), INITIAL_BALANCE * 10);
        
        // Deploy treasury
        treasury = new KerneTreasury(
            founder,
            address(kerne),
            stakingContract,
            address(router)
        );
        
        // Approve WETH for buybacks
        treasury.setApprovedBuybackToken(address(weth), true);
        
        // Fund treasury with WETH
        weth.mint(address(treasury), INITIAL_BALANCE);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTRUCTOR TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_Constructor_SetsCorrectParameters() public view {
        assertEq(treasury.founder(), founder);
        assertEq(treasury.kerneToken(), address(kerne));
        assertEq(treasury.stakingContract(), stakingContract);
        assertEq(address(treasury.aerodromeRouter()), address(router));
        assertEq(treasury.slippageBps(), 100); // Default 1%
        assertEq(treasury.useStablePool(), false);
    }
    
    function test_Constructor_RevertsOnZeroAddresses() public {
        vm.expectRevert(KerneTreasury.ZeroAddress.selector);
        new KerneTreasury(address(0), address(kerne), stakingContract, address(router));
        
        vm.expectRevert(KerneTreasury.ZeroAddress.selector);
        new KerneTreasury(founder, address(0), stakingContract, address(router));
        
        vm.expectRevert(KerneTreasury.ZeroAddress.selector);
        new KerneTreasury(founder, address(kerne), address(0), address(router));
        
        vm.expectRevert(KerneTreasury.ZeroAddress.selector);
        new KerneTreasury(founder, address(kerne), stakingContract, address(0));
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // DISTRIBUTE TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_Distribute_SplitsFundsCorrectly() public {
        uint256 balance = weth.balanceOf(address(treasury));
        uint256 expectedFounderShare = (balance * 8000) / 10000; // 80%
        uint256 expectedBuybackShare = balance - expectedFounderShare; // 20%
        
        vm.expectEmit(true, false, false, true);
        emit FeesDistributed(address(weth), expectedFounderShare, expectedBuybackShare);
        
        treasury.distribute(address(weth));
        
        // Founder receives 80%
        assertEq(weth.balanceOf(founder), expectedFounderShare);
        // Treasury keeps 20% for buyback
        assertEq(weth.balanceOf(address(treasury)), expectedBuybackShare);
    }
    
    function test_Distribute_RevertsOnZeroBalance() public {
        MockERC20 emptyToken = new MockERC20("Empty", "EMPTY");
        
        vm.expectRevert(KerneTreasury.InsufficientBalance.selector);
        treasury.distribute(address(emptyToken));
    }
    
    function test_Distribute_RevertsWhenPaused() public {
        treasury.pause();
        
        vm.expectRevert();
        treasury.distribute(address(weth));
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // BUYBACK TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_ExecuteBuyback_SwapsCorrectly() public {
        uint256 buybackAmount = 100e18;
        
        // Calculate expected output (1:1 rate in mock)
        (uint256 expectedKerne,) = treasury.previewBuyback(address(weth), buybackAmount);
        
        vm.expectEmit(true, false, false, true);
        emit BuybackExecuted(address(weth), buybackAmount, expectedKerne, stakingContract);
        
        treasury.executeBuyback(address(weth), buybackAmount, 0);
        
        // Verify staking contract received KERNE
        assertEq(kerne.balanceOf(stakingContract), expectedKerne);
        
        // Verify stats updated
        (uint256 totalBought, uint256 totalSpent) = treasury.getBuybackStats();
        assertEq(totalBought, expectedKerne);
        assertEq(totalSpent, buybackAmount);
    }
    
    function test_ExecuteBuyback_SlippageProtection() public {
        uint256 buybackAmount = 100e18;
        
        // Set exchange rate to 50% (bad rate)
        router.setExchangeRate(5000);
        
        // Request minimum that's higher than we'll get
        uint256 unreasonableMin = 100e18;
        
        vm.expectRevert("MockRouter: insufficient output");
        treasury.executeBuyback(address(weth), buybackAmount, unreasonableMin);
    }
    
    function test_ExecuteBuyback_OnlyOwner() public {
        vm.prank(user);
        vm.expectRevert();
        treasury.executeBuyback(address(weth), 100e18, 0);
    }
    
    function test_ExecuteBuyback_RevertsOnUnapprovedToken() public {
        vm.expectRevert(KerneTreasury.TokenNotApproved.selector);
        treasury.executeBuyback(address(usdc), 100e18, 0);
    }
    
    function test_ExecuteBuyback_RevertsOnInsufficientBalance() public {
        vm.expectRevert(KerneTreasury.InsufficientBalance.selector);
        treasury.executeBuyback(address(weth), INITIAL_BALANCE * 2, 0);
    }
    
    function test_ExecuteBuyback_RevertsOnSmallAmount() public {
        // Transfer most WETH out first via emergency withdraw
        treasury.emergencyWithdraw(address(weth));
        
        // Send small amount back (below MIN_BUYBACK_AMOUNT of 1e18)
        weth.mint(address(treasury), 0.5e18);
        
        vm.expectRevert(KerneTreasury.BuybackTooSmall.selector);
        treasury.executeBuyback(address(weth), 0.5e18, 0);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // DISTRIBUTE AND BUYBACK TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_DistributeAndBuyback_ExecutesInOneTransaction() public {
        uint256 balance = weth.balanceOf(address(treasury));
        uint256 buybackAmount = (balance * 2000) / 10000; // 20%
        
        treasury.distributeAndBuyback(address(weth), 0);
        
        // Founder received 80%
        assertEq(weth.balanceOf(founder), (balance * 8000) / 10000);
        
        // Staking contract received KERNE from buyback
        assertGt(kerne.balanceOf(stakingContract), 0);
        
        // Treasury should have no WETH left
        assertEq(weth.balanceOf(address(treasury)), 0);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // PREVIEW TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_PreviewBuyback_ReturnsCorrectAmounts() public view {
        uint256 inputAmount = 100e18;
        
        (uint256 expected, uint256 min) = treasury.previewBuyback(address(weth), inputAmount);
        
        // With 1:1 exchange rate
        assertEq(expected, inputAmount);
        // Min should be 99% (1% slippage)
        assertEq(min, (inputAmount * 9900) / 10000);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ROUTING TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_RoutingHop_UsesIntermediateToken() public {
        // Approve USDC and set WETH as hop
        treasury.setApprovedBuybackToken(address(usdc), true);
        treasury.setRoutingHop(address(usdc), address(weth));
        
        // Fund treasury with USDC
        usdc.mint(address(treasury), 100e18);
        // Fund router with enough KERNE
        kerne.mint(address(router), 1000e18);
        
        // Execute buyback via USDC -> WETH -> KERNE
        treasury.executeBuyback(address(usdc), 100e18, 0);
        
        // Should have gone through 2 hops
        assertEq(router.swapCallCount(), 1);
        assertGt(kerne.balanceOf(stakingContract), 0);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // ADMIN TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_SetSlippage_UpdatesCorrectly() public {
        vm.expectEmit(false, false, false, true);
        emit SlippageUpdated(100, 200);
        
        treasury.setSlippage(200);
        assertEq(treasury.slippageBps(), 200);
    }
    
    function test_SetSlippage_RevertsOnTooHigh() public {
        vm.expectRevert(KerneTreasury.SlippageTooHigh.selector);
        treasury.setSlippage(600); // 6% > 5% max
    }
    
    function test_SetApprovedBuybackToken_Works() public {
        assertEq(treasury.isApprovedToken(address(usdc)), false);
        
        vm.expectEmit(true, false, false, true);
        emit BuybackTokenApproved(address(usdc), true);
        
        treasury.setApprovedBuybackToken(address(usdc), true);
        
        assertEq(treasury.isApprovedToken(address(usdc)), true);
    }
    
    function test_UpdateFounder_ByFounder() public {
        address newFounder = address(0x999);
        
        vm.prank(founder);
        treasury.updateFounder(newFounder);
        
        assertEq(treasury.founder(), newFounder);
    }
    
    function test_UpdateFounder_ByOwner() public {
        address newFounder = address(0x999);
        
        treasury.updateFounder(newFounder);
        
        assertEq(treasury.founder(), newFounder);
    }
    
    function test_UpdateFounder_RevertsForUnauthorized() public {
        vm.prank(user);
        vm.expectRevert(KerneTreasury.Unauthorized.selector);
        treasury.updateFounder(user);
    }
    
    function test_EmergencyWithdraw_Works() public {
        uint256 balance = weth.balanceOf(address(treasury));
        
        treasury.emergencyWithdraw(address(weth));
        
        assertEq(weth.balanceOf(owner), balance);
        assertEq(weth.balanceOf(address(treasury)), 0);
    }
    
    function test_PauseUnpause_Works() public {
        treasury.pause();
        
        vm.expectRevert();
        treasury.distribute(address(weth));
        
        treasury.unpause();
        
        // Should work now
        treasury.distribute(address(weth));
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // VIEW FUNCTION TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function test_GetPendingBuyback_ReturnsBalance() public view {
        uint256 pending = treasury.getPendingBuyback(address(weth));
        assertEq(pending, INITIAL_BALANCE);
    }
    
    function test_GetBuybackStats_InitiallyZero() public view {
        (uint256 bought, uint256 spent) = treasury.getBuybackStats();
        assertEq(bought, 0);
        assertEq(spent, 0);
    }
    
    // ═══════════════════════════════════════════════════════════════════════════════
    // FUZZ TESTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    function testFuzz_Distribute_AlwaysSplitsCorrectly(uint256 amount) public {
        // Bound to reasonable amounts
        amount = bound(amount, 1e18, 1000000e18);
        
        // Reset treasury balance
        treasury.emergencyWithdraw(address(weth));
        weth.mint(address(treasury), amount);
        
        uint256 expectedFounder = (amount * 8000) / 10000;
        uint256 expectedBuyback = amount - expectedFounder;
        
        treasury.distribute(address(weth));
        
        assertEq(weth.balanceOf(founder), expectedFounder);
        assertEq(weth.balanceOf(address(treasury)), expectedBuyback);
    }
    
    function testFuzz_Slippage_AlwaysWithinBounds(uint256 slippage) public {
        slippage = bound(slippage, 0, 500);
        
        treasury.setSlippage(slippage);
        assertEq(treasury.slippageBps(), slippage);
    }
}
