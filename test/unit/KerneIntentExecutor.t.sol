// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { Test, console } from "forge-std/Test.sol";
import { KerneIntentExecutor } from "src/KerneIntentExecutor.sol";
import { KerneVault } from "src/KerneVault.sol";
import { KUSDPSM } from "src/KUSDPSM.sol";
import { KerneToken } from "src/KerneToken.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract MockToken is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {}
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract MockAggregator {
    function settle(address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut, address recipient, address from) external {
        // Pull tokenIn from the 'from' address (the user who is swapping)
        IERC20(tokenIn).transferFrom(from, address(this), amountIn);
        // Send tokenOut to the recipient (executor, to repay flash loan)
        IERC20(tokenOut).transfer(recipient, amountOut);
    }
}

contract KerneIntentExecutorTest is Test {
    KerneIntentExecutor public executor;
    KerneVault public vault;
    KUSDPSM public psm;
    KerneToken public kUSD;
    MockToken public usdc;
    MockToken public weth;

    address public admin = address(0x1);
    address public solver = address(0x2);
    address public user = address(0x3);
    address public exchange = makeAddr("exchange");

    address public constant ONE_INCH_ROUTER = 0x111111125421cA6dc452d289314280a0f8842A65;

    function setUp() public {
        kUSD = new KerneToken(address(this));
        kUSD.grantRole(kUSD.MINTER_ROLE(), address(this));
        usdc = new MockToken("USDC", "USDC");
        weth = new MockToken("WETH", "WETH");

        // Deploy vault with this contract as admin
        vault = new KerneVault(IERC20(address(usdc)), "Kerne Vault USDC", "kUSDC", address(this), address(this), exchange);
        psm = new KUSDPSM(address(kUSD), address(this));

        executor = new KerneIntentExecutor(admin, solver);

        // Grant roles for zero-fee flash loans
        vault.grantRole(vault.STRATEGIST_ROLE(), address(executor));
        psm.grantRole(psm.ARBITRAGEUR_ROLE(), address(executor));
        psm.addStable(address(usdc), 0, 1000000 ether);
        psm.addStable(address(kUSD), 0, 1000000 ether);

        // Fund liquidity sources
        usdc.mint(address(vault), 1000000 ether);
        usdc.mint(address(psm), 1000000 ether);
        kUSD.mint(address(psm), 1000000 ether);
        
        // Label for clarity
        vm.label(admin, "Admin");
        vm.label(solver, "Solver");

        // Etch Mock Aggregator at 1inch address
        MockAggregator mockAggregator = new MockAggregator();
        vm.etch(ONE_INCH_ROUTER, address(mockAggregator).code);
        
        vm.label(ONE_INCH_ROUTER, "1inch");
        vm.label(address(executor), "Executor");
        vm.label(address(vault), "Vault");
        vm.label(address(psm), "PSM");
    }

    function testFulfillIntentWithVault() public {
        uint256 amount = 1000 ether;
        
        // Mock user having tokenIn (WETH)
        weth.mint(user, 10 ether);
        
        // Fund the mock aggregator with USDC to simulate swap output
        usdc.mint(ONE_INCH_ROUTER, 1000 ether);
        
        // Aggregator data: call settle(weth, usdc, 1 ether, 1000 ether, executor, user)
        // The aggregator pulls WETH from user, sends USDC to executor
        bytes memory aggregatorData = abi.encodeWithSignature(
            "settle(address,address,uint256,uint256,address,address)",
            address(weth),
            address(usdc),
            1 ether,
            1000 ether,
            address(executor),
            user
        );

        KerneIntentExecutor.IntentSafetyParams memory safety = KerneIntentExecutor.IntentSafetyParams({
            timestamp: block.timestamp,
            expectedPrice: 1000e18
        });
        bytes memory safetyParams = abi.encode(safety);

        // User approves the aggregator to pull their WETH
        vm.prank(user);
        weth.approve(ONE_INCH_ROUTER, 1 ether);
        
        vm.prank(solver);
        executor.fulfillIntent(
            address(vault),
            address(weth),
            address(usdc),
            1000 ether,
            user,
            aggregatorData,
            safetyParams
        );

        assertEq(usdc.balanceOf(user), 1000 ether);
        assertEq(weth.balanceOf(user), 9 ether);
        // Vault should have 1000000 USDC (no fee charged)
        assertEq(usdc.balanceOf(address(vault)), 1000000 ether);
    }

    function testFulfillIntentWithPSM() public {
        uint256 amount = 1000 ether;
        
        // Fund the mock aggregator with kUSD to simulate swap output
        kUSD.mint(ONE_INCH_ROUTER, 1000 ether);
        
        // Aggregator data: call settle(usdc, kUSD, 1000 ether, 1000 ether, executor, user)
        bytes memory aggregatorData = abi.encodeWithSignature(
            "settle(address,address,uint256,uint256,address,address)",
            address(usdc),
            address(kUSD),
            1000 ether,
            1000 ether,
            address(executor),
            user
        );

        KerneIntentExecutor.IntentSafetyParams memory safety = KerneIntentExecutor.IntentSafetyParams({
            timestamp: block.timestamp,
            expectedPrice: 1e18
        });
        bytes memory safetyParams = abi.encode(safety);

        usdc.mint(user, 1000 ether);
        // User approves the aggregator to pull their USDC
        vm.prank(user);
        usdc.approve(ONE_INCH_ROUTER, 1000 ether);

        vm.prank(solver);
        executor.fulfillIntent(
            address(psm),
            address(usdc),
            address(kUSD),
            1000 ether,
            user,
            aggregatorData,
            safetyParams
        );

        assertEq(kUSD.balanceOf(user), 1000 ether);
        assertEq(usdc.balanceOf(user), 0);
        // PSM should have 1000000 kUSD (no fee charged)
        assertEq(kUSD.balanceOf(address(psm)), 1000000 ether);
    }
}
