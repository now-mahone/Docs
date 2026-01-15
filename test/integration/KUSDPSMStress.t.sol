// SPDX-License-Identifier: MIT
// Created: 2026-01-12
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import { KUSDPSM } from "src/KUSDPSM.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { IAggregatorV3 } from "src/interfaces/IAggregatorV3.sol";

contract MockERC20 is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract MockOracle is IAggregatorV3 {
    int256 public price;
    uint256 public updatedAt;

    function setPrice(int256 _price) external {
        price = _price;
        updatedAt = block.timestamp;
    }

    function latestRoundData() external view override returns (uint80, int256, uint256, uint256, uint80) {
        return (0, price, 0, updatedAt, 0);
    }
    
    function decimals() external pure override returns (uint8) { return 8; }
    function description() external pure override returns (string memory) { return "Mock Oracle"; }
    function version() external pure override returns (uint256) { return 1; }
    function getRoundData(uint80) external pure override returns (uint80, int256, uint256, uint256, uint80) { return (0,0,0,0,0); }
}

contract KUSDPSMStressTest is Test {
    KUSDPSM public psm;
    MockERC20 public kUSD;
    MockERC20 public usdc;
    MockOracle public oracle;
    
    address public admin = address(0xAD);
    address public user = address(0xDE);

    function setUp() public {
        kUSD = new MockERC20("Kerne USD", "kUSD");
        usdc = new MockERC20("USD Coin", "USDC");
        psm = new KUSDPSM(address(kUSD), admin);
        oracle = new MockOracle();
        oracle.setPrice(1e8); // $1.00

        vm.startPrank(admin);
        psm.addStable(address(usdc), 10, type(uint256).max); // 10 bps fee, unlimited cap
        psm.setOracle(address(usdc), address(oracle));
        vm.stopPrank();

        kUSD.mint(address(psm), 1_000_000 * 1e18);
        usdc.mint(user, 100_000 * 1e18);
    }


    /**
     * @notice Stress Test: Verify depeg circuit breaker.
     */
    function testDepegCircuitBreaker() public {
        // Drop price to $0.97 (3% depeg, default limit is 2%)
        oracle.setPrice(0.97e8);
        
        vm.startPrank(user);
        usdc.approve(address(psm), 1000 * 1e18);
        
        vm.expectRevert("Stable depegged: Circuit breaker triggered");
        psm.swapStableForKUSD(address(usdc), 1000 * 1e18);
        vm.stopPrank();
    }

    /**
     * @notice Stress Test: Verify solvency circuit breaker.
     */
    function testInsolvencyCircuitBreaker() public {
        address mockVault = address(0xCAFE);
        vm.startPrank(admin);
        psm.setVault(mockVault);
        vm.stopPrank();

        // Mock solvency ratio < 101%
        vm.mockCall(
            mockVault,
            abi.encodeWithSignature("getSolvencyRatio()"),
            abi.encode(10050) // 100.5%
        );

        vm.startPrank(user);
        usdc.approve(address(psm), 1000 * 1e18);
        vm.expectRevert("Protocol insolvency: PSM operations halted");
        psm.swapStableForKUSD(address(usdc), 1000 * 1e18);
        vm.stopPrank();
    }

    /**
     * @notice Test pausing functionality.
     */
    function testPauseCircuitBreaker() public {
        vm.startPrank(admin);
        psm.pause();
        vm.stopPrank();

        vm.startPrank(user);
        usdc.approve(address(psm), 1000 * 1e18);
        vm.expectRevert(abi.encodeWithSignature("EnforcedPause()"));
        psm.swapStableForKUSD(address(usdc), 1000 * 1e18);
        vm.stopPrank();
    }

    /**
     * @notice Test standard swap under normal conditions.

     */
    function testNormalSwap() public {
        vm.startPrank(user);
        usdc.approve(address(psm), 1000 * 1e18);
        psm.swapStableForKUSD(address(usdc), 1000 * 1e18);
        
        // 1000 - 10 bps (1) = 999
        assertEq(kUSD.balanceOf(user), 999 * 1e18);
        vm.stopPrank();
    }

    /**
     * @notice Stress Test: Simulate a depeg scenario where the PSM is drained.
     * If USDC depegs, users will rush to swap USDC for kUSD.
     */
    function testUSDCDepegDrain() public {
        uint256 psmInitialKUSD = kUSD.balanceOf(address(psm));
        
        // Large whale swaps USDC for kUSD during depeg
        address whale = address(0xBA);
        usdc.mint(whale, psmInitialKUSD);
        
        vm.startPrank(whale);
        usdc.approve(address(psm), psmInitialKUSD);
        
        // The PSM currently doesn't have a circuit breaker for price deviation
        // This test highlights the risk of being a "liquidity provider of last resort"
        psm.swapStableForKUSD(address(usdc), psmInitialKUSD);
        
        // The fee is 10 bps, so the whale gets psmInitialKUSD - fee
        // The PSM should have 0 kUSD left if the swap was for the full amount
        uint256 fee = (psmInitialKUSD * 10) / 10000;
        uint256 amountOut = psmInitialKUSD - fee;
        
        // If the whale wanted to drain EXACTLY what's in the PSM, they need to account for the fee
        // Let's adjust the test to swap enough to drain the PSM
        vm.stopPrank();
        
        // Reset and try again with exact amount to drain
        kUSD.mint(address(psm), 1_000_000 * 1e18); // Refill
        uint256 currentKUSD = kUSD.balanceOf(address(psm));
        
        // To get currentKUSD out, whale needs to swap X where X - (X * 10 / 10000) = currentKUSD
        // X * (9990 / 10000) = currentKUSD => X = currentKUSD * 10000 / 9990
        uint256 exactAmountIn = (currentKUSD * 10000) / 9990;
        usdc.mint(whale, exactAmountIn);
        
        vm.startPrank(whale);
        usdc.approve(address(psm), exactAmountIn);
        psm.swapStableForKUSD(address(usdc), exactAmountIn);
        
        assertEq(kUSD.balanceOf(address(psm)), 0);
        vm.stopPrank();
    }

    /**
     * @notice Stress Test: Tiered fees for institutional volume.
     */
    function testTieredFeesStress() public {
        vm.startPrank(admin);
        KUSDPSM.TieredFee[] memory tiers = new KUSDPSM.TieredFee[](1);
        tiers[0] = KUSDPSM.TieredFee({
            threshold: 50_000 * 1e18,
            feeBps: 5 // Lower fee for > 50k
        });
        psm.setTieredFees(address(usdc), tiers);
        vm.stopPrank();

        vm.startPrank(user);
        usdc.approve(address(psm), 60_000 * 1e18);
        psm.swapStableForKUSD(address(usdc), 60_000 * 1e18);
        
        // 60,000 - 5 bps (30) = 59,970
        assertEq(kUSD.balanceOf(user), 59_970 * 1e18);
        vm.stopPrank();
    }
}
