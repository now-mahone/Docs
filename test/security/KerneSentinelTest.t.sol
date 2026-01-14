// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneIntentExecutor.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockERC20 is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {
        _mint(msg.sender, 1000000 * 1e18);
    }

    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract MockLendingPool {
    function flashLoanSimple(
        address receiverAddress,
        address asset,
        uint256 amount,
        bytes calldata params,
        uint16 referralCode
    ) external {
        // Mock flash loan: just call executeOperation back
        KerneIntentExecutor(payable(receiverAddress)).executeOperation(asset, amount, 0, msg.sender, params);
    }
}

contract KerneSentinelTest is Test {
    KerneIntentExecutor executor;
    MockERC20 tokenIn;
    MockERC20 tokenOut;
    MockLendingPool lendingPool;

    address admin = address(0x1);
    address solver = address(0x2);
    address sentinel = address(0x3);
    address user = address(0x4);

    function setUp() public {
        tokenIn = new MockERC20("Token In", "TIN");
        tokenOut = new MockERC20("Token Out", "TOUT");
        lendingPool = new MockLendingPool();

        executor = new KerneIntentExecutor(admin, solver, address(lendingPool));

        vm.startPrank(admin);
        executor.grantRole(executor.SENTINEL_ROLE(), sentinel);
        vm.stopPrank();

        tokenOut.transfer(address(lendingPool), 1000 * 1e18);
    }

    function testFulfillIntent_SentinelLatency_Success() public {
        KerneIntentExecutor.IntentSafetyParams memory s = KerneIntentExecutor.IntentSafetyParams({
            timestamp: block.timestamp,
            expectedPrice: 1e18
        });
        bytes memory safetyParams = abi.encode(s);

        // Mint tokenIn to executor to satisfy flash loan repayment (mocked)
        tokenIn.mint(address(executor), 1000 * 1e18);
        // Mint tokenOut to lendingPool to satisfy flash loan
        tokenOut.mint(address(lendingPool), 1000 * 1e18);
        // Mint tokenOut to executor to satisfy transfer to user
        tokenOut.mint(address(executor), 1000 * 1e18);

        vm.startPrank(solver);
        executor.fulfillIntent(
            address(tokenIn),
            address(tokenOut),
            100 * 1e18,
            user,
            hex"00",
            safetyParams
        );
        vm.stopPrank();
    }

    function testFulfillIntent_SentinelLatency_Expired() public {
        // Set block timestamp to something large to avoid underflow
        vm.warp(1000);
        
        KerneIntentExecutor.IntentSafetyParams memory s = KerneIntentExecutor.IntentSafetyParams({
            timestamp: 500, // 500 seconds ago
            expectedPrice: 1e18
        });
        bytes memory safetyParams = abi.encode(s);

        vm.startPrank(solver);
        vm.expectRevert("Sentinel: Intent expired (Latency)");
        executor.fulfillIntent(
            address(tokenIn),
            address(tokenOut),
            100 * 1e18,
            user,
            hex"00",
            safetyParams
        );
        vm.stopPrank();
    }

    function testToggleSentinel() public {
        vm.warp(1000);
        vm.startPrank(sentinel);
        executor.toggleSentinel(false);
        vm.stopPrank();

        assertEq(executor.sentinelActive(), false);

        // Should now bypass latency check even if expired
        KerneIntentExecutor.IntentSafetyParams memory s = KerneIntentExecutor.IntentSafetyParams({
            timestamp: 500,
            expectedPrice: 1e18
        });
        bytes memory safetyParams = abi.encode(s);

        // Mint tokens to avoid balance errors
        tokenIn.mint(address(executor), 1000 * 1e18);
        tokenOut.mint(address(lendingPool), 1000 * 1e18);
        tokenOut.mint(address(executor), 1000 * 1e18);

        vm.startPrank(solver);
        executor.fulfillIntent(
            address(tokenIn),
            address(tokenOut),
            100 * 1e18,
            user,
            hex"00",
            safetyParams
        );
        vm.stopPrank();
    }

    function testUpdateSentinelParams() public {
        vm.startPrank(sentinel);
        executor.updateSentinelParams(1000, 200);
        vm.stopPrank();

        assertEq(executor.maxLatency(), 1000);
        assertEq(executor.maxPriceDeviationBps(), 200);
    }

    function testUnauthorizedSentinelUpdate() public {
        vm.startPrank(user);
        vm.expectRevert();
        executor.updateSentinelParams(1000, 200);
        vm.stopPrank();
    }
}
