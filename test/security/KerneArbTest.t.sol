// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneArbExecutor.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/interfaces/IERC3156FlashLender.sol";

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

contract MockVault {
    uint256 public ratio = 10500;
    function setSolvencyRatio(uint256 _ratio) external {
        ratio = _ratio;
    }
    function getSolvencyRatio() external view returns (uint256) {
        return ratio;
    }
}

contract MockLender is IERC3156FlashLender {
    IERC20 public token;
    constructor(address _token) {
        token = IERC20(_token);
    }
    function maxFlashLoan(address t) external view override returns (uint256) {
        return t == address(token) ? 1000000 * 1e18 : 0;
    }
    function flashFee(address, uint256) external pure override returns (uint256) {
        return 0;
    }
    function flashLoan(
        IERC3156FlashBorrower receiver,
        address t,
        uint256 amount,
        bytes calldata data
    ) external override returns (bool) {
        token.transfer(address(receiver), amount);
        require(receiver.onFlashLoan(msg.sender, t, amount, 0, data) == keccak256("ERC3156FlashBorrower.onFlashLoan"), "Callback failed");
        token.transferFrom(address(receiver), address(this), amount);
        return true;
    }
}

contract KerneArbTest is Test {
    KerneArbExecutor executor;
    MockToken weth;
    MockToken wsteth;
    MockDEX dexA;
    MockDEX dexB;
    MockVault vault;
    MockLender lender;

    address admin = address(0x1);
    address solver = address(0x2);
    address treasury = address(0x3);
    address insuranceFund = address(0x4);

    function setUp() public {
        weth = new MockToken("Wrapped Ether", "WETH");
        wsteth = new MockToken("Wrapped Staked Ether", "wstETH");
        vault = new MockVault();
        lender = new MockLender(address(weth));
        
        executor = new KerneArbExecutor(admin, solver, treasury, insuranceFund, address(vault));

        // Dex A: Buy wstETH with WETH (1 WETH = 1.1 wstETH)
        dexA = new MockDEX(address(weth), address(wsteth), 1100);
        wsteth.mint(address(dexA), 1000 * 1e18);

        // Dex B: Sell wstETH for WETH (1 wstETH = 1.0 WETH) -> Total 1.1 WETH
        dexB = new MockDEX(address(wsteth), address(weth), 1000);
        weth.mint(address(dexB), 1000 * 1e18);

        weth.mint(address(lender), 1000 * 1e18);
    }

    function testArbWithFlashLoan_Success() public {
        uint256 amountIn = 10 * 1e18;

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

        vm.startPrank(address(executor));
        weth.approve(address(dexA), type(uint256).max);
        wsteth.approve(address(dexB), type(uint256).max);
        weth.approve(address(lender), type(uint256).max);
        vm.stopPrank();

        vm.prank(solver, solver);
        executor.executeArbWithFlashLoan(address(lender), address(weth), amountIn, steps);

        // Profit = 11 - 10 = 1 WETH
        // Split: 80% Treasury (0.8), 20% Insurance (0.2)
        assertEq(weth.balanceOf(treasury), 0.8 * 1e18);
        assertEq(weth.balanceOf(insuranceFund), 0.2 * 1e18);
    }

    function testArb_SentinelInsolvencyRevert() public {
        vault.setSolvencyRatio(10000); // 100% (Below 101% threshold)
        
        uint256 amountIn = 10 * 1e18;
        KerneArbExecutor.ArbStep[] memory steps = new KerneArbExecutor.ArbStep[](0);

        vm.prank(solver, solver);
        vm.expectRevert("Sentinel: Protocol insolvency detected");
        executor.executeArb(address(weth), amountIn, steps);
    }

    function testArb_ProfitSplitUpdate() public {
        vm.prank(admin);
        executor.setProfitSplit(5000); // 50/50 split

        uint256 amountIn = 10 * 1e18;
        weth.mint(address(executor), amountIn);

        KerneArbExecutor.ArbStep[] memory steps = new KerneArbExecutor.ArbStep[](2);
        steps[0] = KerneArbExecutor.ArbStep({
            target: address(dexA),
            data: abi.encodeWithSignature("swap(uint256)", amountIn)
        });
        steps[1] = KerneArbExecutor.ArbStep({
            target: address(dexB),
            data: abi.encodeWithSignature("swap(uint256)", 11 * 1e18)
        });

        vm.startPrank(address(executor));
        weth.approve(address(dexA), type(uint256).max);
        wsteth.approve(address(dexB), type(uint256).max);
        vm.stopPrank();

        vm.prank(solver, solver);
        executor.executeArb(address(weth), 0, steps);

        assertEq(weth.balanceOf(treasury), 0.5 * 1e18);
        assertEq(weth.balanceOf(insuranceFund), 0.5 * 1e18);
    }

}
