// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneArbExecutor.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockToken is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {
        _mint(msg.sender, 1000000 * 1e18);
    }
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract MockDEX {
    IERC20 public tokenIn;
    IERC20 public tokenOut;
    uint256 public rate; // amountOut = amountIn * rate / 1000

    constructor(address _tokenIn, address _tokenOut, uint256 _rate) {
        tokenIn = IERC20(_tokenIn);
        tokenOut = IERC20(_tokenOut);
        rate = _rate;
    }

    function swap(uint256 amount) external {
        tokenIn.transferFrom(msg.sender, address(this), amount);
        uint256 amountOut = (amount * rate) / 1000;
        tokenOut.transfer(msg.sender, amountOut);
    }
}

contract KerneArbTest is Test {
    KerneArbExecutor executor;
    MockToken weth;
    MockToken wsteth;
    MockDEX dexA;
    MockDEX dexB;

    address admin = address(0x1);
    address solver = address(0x2);
    address treasury = address(0x3);

    function setUp() public {
        weth = new MockToken("Wrapped Ether", "WETH");
        wsteth = new MockToken("Wrapped Staked Ether", "wstETH");
        
        executor = new KerneArbExecutor(admin, solver, treasury);

        // Dex A: Buy wstETH with WETH (1 WETH = 1.1 wstETH)
        dexA = new MockDEX(address(weth), address(wsteth), 1100);
        wsteth.mint(address(dexA), 1000 * 1e18);

        // Dex B: Sell wstETH for WETH (1 wstETH = 1.0 WETH) -> Total 1.1 WETH
        dexB = new MockDEX(address(wsteth), address(weth), 1000);
        weth.mint(address(dexB), 1000 * 1e18);
    }

    function testArbExecution_Success() public {
        uint256 amountIn = 10 * 1e18;
        weth.mint(address(executor), amountIn);

        KerneArbExecutor.ArbStep[] memory steps = new KerneArbExecutor.ArbStep[](2);
        
        // Step 1: WETH -> wstETH on Dex A
        steps[0] = KerneArbExecutor.ArbStep({
            target: address(dexA),
            data: abi.encodeWithSignature("swap(uint256)", amountIn)
        });

        // Step 2: wstETH -> WETH on Dex B
        // amountIn * 1.1 = 11 wstETH
        steps[1] = KerneArbExecutor.ArbStep({
            target: address(dexB),
            data: abi.encodeWithSignature("swap(uint256)", 11 * 1e18)
        });

        // Re-setup with approvals
        vm.prank(address(executor));
        weth.approve(address(dexA), type(uint256).max);
        vm.prank(address(executor));
        wsteth.approve(address(dexB), type(uint256).max);

        uint256 balanceBefore = weth.balanceOf(address(executor));
        emit log_named_uint("Balance Before", balanceBefore);

        vm.startPrank(solver);
        executor.executeArb(address(weth), 0, steps); // amountIn is already in contract, so we set amount to 0 for profit check
        vm.stopPrank();

        uint256 balanceAfter = weth.balanceOf(address(executor));
        emit log_named_uint("Balance After", balanceAfter);

        // Profit = 11 - 10 = 1 WETH
        assertEq(weth.balanceOf(treasury), 1 * 1e18);
    }

    function testArbExecution_NotProfitable() public {
        uint256 amountIn = 10 * 1e18;
        weth.mint(address(executor), amountIn);

        // Dex A: 1 WETH = 0.9 wstETH
        MockDEX dexC = new MockDEX(address(weth), address(wsteth), 900);
        wsteth.mint(address(dexC), 1000 * 1e18);

        KerneArbExecutor.ArbStep[] memory steps = new KerneArbExecutor.ArbStep[](2);
        steps[0] = KerneArbExecutor.ArbStep({
            target: address(dexC),
            data: abi.encodeWithSignature("swap(uint256)", amountIn)
        });
        steps[1] = KerneArbExecutor.ArbStep({
            target: address(dexB),
            data: abi.encodeWithSignature("swap(uint256)", 9 * 1e18)
        });

        vm.startPrank(address(executor));
        weth.approve(address(dexC), type(uint256).max);
        wsteth.approve(address(dexB), type(uint256).max);
        vm.stopPrank();

        vm.startPrank(solver);
        vm.expectRevert("Arb not profitable");
        executor.executeArb(address(weth), amountIn, steps);
        vm.stopPrank();
    }
}
