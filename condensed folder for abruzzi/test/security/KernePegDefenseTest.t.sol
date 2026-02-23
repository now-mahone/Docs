// Created: 2026-01-14
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KUSDPSM.sol";
import "src/KerneInsuranceFund.sol";
import "src/KerneToken.sol";
import "@openzeppelin/contracts/token/ERC20/ERC20.sol";

contract MockStable is ERC20 {
    constructor(string memory name, string memory symbol) ERC20(name, symbol) {
        _mint(msg.sender, 1000000 * 1e18);
    }
    function mint(address to, uint256 amount) public {
        _mint(to, amount);
    }
}

contract KernePegDefenseTest is Test {
    KUSDPSM psm;
    KerneInsuranceFund insurance;
    KerneToken kUSD;
    MockStable usdc;

    address admin = address(0x1);
    address user = address(0x2);

    function setUp() public {
        // Deploy contracts as this test contract to avoid Ownable issues during setup
        kUSD = new KerneToken(address(this));
        usdc = new MockStable("USD Coin", "USDC");
        psm = new KUSDPSM(address(kUSD), address(this));
        insurance = new KerneInsuranceFund(address(usdc), address(this));

        // Setup roles and config
        psm.addStable(address(usdc), 10, 1000000 * 1e18); // 10 bps fee
        psm.setInsuranceFund(address(insurance));
        insurance.setAuthorization(address(psm), true);

        kUSD.grantRole(kUSD.MINTER_ROLE(), address(this)); // Allow test to mint kUSD for simulation
        
        // Grant admin roles to the admin address for completeness
        psm.grantRole(psm.DEFAULT_ADMIN_ROLE(), admin);
        psm.grantRole(psm.MANAGER_ROLE(), admin);
        kUSD.grantRole(kUSD.DEFAULT_ADMIN_ROLE(), admin);
    }

    function testPegDefense_Success() public {
        // 1. Setup: PSM has 0 USDC, Insurance Fund has 1000 USDC
        usdc.mint(address(insurance), 1000 * 1e18);
        
        // 2. User has 100 kUSD and wants to swap for USDC
        kUSD.mint(user, 100 * 1e18);
        
        vm.startPrank(user);
        kUSD.approve(address(psm), 100 * 1e18);
        
        // 3. Swap: PSM should draw from Insurance Fund
        // Deficit is 100 USDC (minus fee)
        // We expect it to fail if the low-level call failed or if reserves are still insufficient
        vm.warp(block.timestamp + 2 hours); // Bypass cooldown
        psm.swapKUSDForStable(address(usdc), 100 * 1e18);
        vm.stopPrank();

        // 4. Verify: User got ~100 USDC (minus fee)
        uint256 fee = (100 * 1e18 * 10) / 10000;
        uint256 amountAfterFee = 100 * 1e18 - fee;
        assertEq(usdc.balanceOf(user), amountAfterFee);
        
        // Deficit was amountAfterFee. Insurance fund should have sent exactly that.
        assertEq(usdc.balanceOf(address(insurance)), 1000 * 1e18 - amountAfterFee);
    }

    function testPegDefense_ManualClaim() public {
        usdc.mint(address(insurance), 1000 * 1e18);
        vm.warp(block.timestamp + 2 hours); // Bypass cooldown
        insurance.claim(address(psm), 100 * 1e18);
        assertEq(usdc.balanceOf(address(psm)), 100 * 1e18);
    }

    function testPegDefense_DeficitExceedsLimit() public {
        // 1. Setup: Insurance Fund has 100 USDC, max claim is 50% (50 USDC)
        usdc.mint(address(insurance), 100 * 1e18);
        
        // 2. User wants to swap 60 kUSD
        kUSD.mint(user, 60 * 1e18);
        
        vm.startPrank(user);
        kUSD.approve(address(psm), 60 * 1e18);
        
        // 3. Swap should fail because deficit (60) > max claim (50)
        vm.expectRevert("Insufficient stable reserves (Peg Defense Failed)");
        psm.swapKUSDForStable(address(usdc), 60 * 1e18);
        vm.stopPrank();
    }

    function testPegDefense_Cooldown() public {
        usdc.mint(address(insurance), 1000 * 1e18);
        kUSD.mint(user, 200 * 1e18);
        
        vm.startPrank(user);
        kUSD.approve(address(psm), 200 * 1e18);
        
        // First swap succeeds
        vm.warp(block.timestamp + 2 hours);
        psm.swapKUSDForStable(address(usdc), 100 * 1e18);
        
        // Second swap fails due to 1 hour cooldown in InsuranceFund.claim
        vm.expectRevert("Insufficient stable reserves (Peg Defense Failed)");
        psm.swapKUSDForStable(address(usdc), 100 * 1e18);
        
        // Warp time
        vm.warp(block.timestamp + 1 hours + 1);
        
        // Now it succeeds
        psm.swapKUSDForStable(address(usdc), 100 * 1e18);
        vm.stopPrank();
    }
}
