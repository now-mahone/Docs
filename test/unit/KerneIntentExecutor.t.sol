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
    function settle(address tokenIn, address tokenOut, uint256 amountIn, uint256 amountOut, address executor) external {
        IERC20(tokenIn).transferFrom(executor, address(this), amountIn);
        IERC20(tokenOut).transfer(executor, amountOut);
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
        kUSD = new KerneToken(admin);
        usdc = new MockToken("USDC", "USDC");
        weth = new MockToken("WETH", "WETH");

        vault = new KerneVault(IERC20(address(usdc)), "Kerne Vault USDC", "kUSDC", admin, admin, exchange);
        psm = new KUSDPSM(address(kUSD), admin);

        executor = new KerneIntentExecutor(admin, solver);

        // Grant roles for zero-fee flash loans
        vm.startPrank(admin);
        vault.grantRole(vault.STRATEGIST_ROLE(), address(executor));
        psm.grantRole(psm.ARBITRAGEUR_ROLE(), address(executor));
        psm.addStable(address(usdc), 0, 1000000 ether);

        // Fund liquidity sources
        usdc.mint(address(vault), 1000000 ether);
        usdc.mint(address(psm), 1000000 ether);
        kUSD.mint(address(psm), 1000000 ether);
        vm.stopPrank();

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
        uint256 amountIn = 1010 ether; // User gives 1010 USDC for 1000 USDC flash loan (to cover hypothetical fees or just profit)
        
        // In this test, we flash loan USDC from Vault to give to user.
        // Aggregator will take USDC from user (simulated) and give back to executor.
        
        // Mock user having tokenIn (WETH)
        weth.mint(user, 10 ether);
        
        // Aggregator data: call settle(weth, usdc, 1 ether, 1000 ether, executor)
        // Wait, the executor sends tokenOut to user.
        // Then executor needs to get tokenOut back to repay flash loan.
        // So aggregator should swap tokenIn (from user) to tokenOut.
        
        bytes memory aggregatorData = abi.encodeWithSignature(
            "settle(address,address,uint256,uint256,address)",
            address(weth),
            address(usdc),
            1 ether,
            1000 ether,
            address(executor)
        );

        KerneIntentExecutor.IntentSafetyParams memory safety = KerneIntentExecutor.IntentSafetyParams({
            timestamp: block.timestamp,
            expectedPrice: 1000e18
        });
        bytes memory safetyParams = abi.encode(safety);

        // Solver fulfills intent
        vm.startPrank(solver);
        
        // We need to make sure the mock aggregator can pull WETH from user
        // In a real intent, the user would have signed a permit or approved the aggregator.
        // Here we simulate user approving executor or aggregator.
        vm.stopPrank();
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
        
        bytes memory aggregatorData = abi.encodeWithSignature(
            "settle(address,address,uint256,uint256,address)",
            address(usdc),
            address(kUSD),
            1000 ether,
            1000 ether,
            address(executor)
        );

        KerneIntentExecutor.IntentSafetyParams memory safety = KerneIntentExecutor.IntentSafetyParams({
            timestamp: block.timestamp,
            expectedPrice: 1e18
        });
        bytes memory safetyParams = abi.encode(safety);

        usdc.mint(user, 1000 ether);
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
