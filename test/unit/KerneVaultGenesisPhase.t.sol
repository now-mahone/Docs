// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "../../src/KerneVault.sol";
import "../../src/mocks/MockERC20.sol";

contract KerneVaultGenesisPhaseTest is Test {
    KerneVault public vault;
    MockERC20 public asset;
    
    address public admin = address(0x1);
    address public strategist = address(0x2);
    address public user1 = address(0x3);
    address public user2 = address(0x4);
    address public founder = address(0x5);
    
    // $100,000 threshold
    uint256 public constant GENESIS_THRESHOLD = 100_000 * 1e18;
    
    function setUp() public {
        asset = new MockERC20("Wrapped ETH", "WETH", 18);
        vault = new KerneVault(
            IERC20(address(asset)),
            "Kerne Vault",
            "kLP",
            admin,
            strategist,
            address(0) // exchangeDepositAddress
        );
        
        // Mint assets to users
        asset.mint(user1, 1_000_000 * 1e18);
        asset.mint(user2, 1_000_000 * 1e18);
        
        // Approve vault
        vm.prank(user1);
        asset.approve(address(vault), type(uint256).max);
        vm.prank(user2);
        asset.approve(address(vault), type(uint256).max);
        
        // Set founder
        vm.prank(admin);
        vault.setFounder(founder);
        
        // Set deposit fee to 0 for testing
        vm.prank(admin);
        vault.setDepositFee(0);
    }
    
    function test_GenesisPhase_InitialState() public {
        assertEq(vault.genesisPhaseActive(), true, "Genesis Phase should be active initially");
        assertEq(vault.GENESIS_TVL_THRESHOLD(), GENESIS_THRESHOLD, "Threshold should be $100k");
        assertEq(vault.genesisPhaseDeposits(), 0, "Genesis deposits should be 0");
        assertEq(vault.genesisPhaseEndedAt(), 0, "Genesis ended at should be 0");
    }
    
    function test_GenesisPhase_EffectiveFeeIsZero() public {
        assertEq(vault.getEffectivePerformanceFee(), 0, "Effective fee should be 0% during Genesis");
    }
    
    function test_GenesisPhase_DepositTracking() public {
        uint256 depositAmount = 50_000 * 1e18; // $50k
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        assertEq(vault.genesisPhaseDeposits(), depositAmount, "Genesis deposits should track deposits");
        assertEq(vault.genesisPhaseActive(), true, "Genesis Phase should still be active");
    }
    
    function test_GenesisPhase_ProgressTracking() public {
        uint256 depositAmount = 50_000 * 1e18; // $50k = 50%
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        // Progress should be 50%
        uint256 progress = vault.getGenesisPhaseProgress();
        assertEq(progress, 5000, "Progress should be 50% (5000 bps)");
    }
    
    function test_GenesisPhase_RemainingTVL() public {
        uint256 depositAmount = 30_000 * 1e18; // $30k
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        uint256 remaining = vault.getRemainingGenesisTVL();
        assertEq(remaining, 70_000 * 1e18, "Remaining should be $70k");
    }
    
    function test_GenesisPhase_EndsAtThreshold() public {
        // Deposit $100k to trigger end of Genesis Phase
        uint256 depositAmount = 100_000 * 1e18;
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        assertEq(vault.genesisPhaseActive(), false, "Genesis Phase should end at $100k");
        assertGt(vault.genesisPhaseEndedAt(), 0, "Genesis ended timestamp should be set");
    }
    
    function test_GenesisPhase_EffectiveFeeAfterEnd() public {
        // End Genesis Phase
        uint256 depositAmount = 100_000 * 1e18;
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        // Effective fee should now be 10%
        assertEq(vault.getEffectivePerformanceFee(), 1000, "Effective fee should be 10% after Genesis");
    }
    
    function test_GenesisPhase_AdminCanEndManually() public {
        vm.prank(admin);
        vault.endGenesisPhase();
        
        assertEq(vault.genesisPhaseActive(), false, "Admin can end Genesis Phase");
    }
    
    function test_GenesisPhase_CannotEndTwice() public {
        vm.prank(admin);
        vault.endGenesisPhase();
        
        vm.prank(admin);
        vm.expectRevert("Genesis Phase already ended");
        vault.endGenesisPhase();
    }
    
    function test_GenesisPhase_EventsEmitted() public {
        uint256 depositAmount = 100_000 * 1e18;
        
        // Expect GenesisPhaseDeposit event
        vm.expectEmit(true, false, false, true);
        emit KerneVault.GenesisPhaseDeposit(user1, depositAmount, depositAmount);
        
        // Expect GenesisPhaseEnded event
        vm.expectEmit(false, false, false, true);
        emit KerneVault.GenesisPhaseEnded(depositAmount, block.timestamp);
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
    }
    
    function test_GenesisPhase_MultipleDeposits() public {
        // First deposit: $40k
        vm.prank(user1);
        vault.deposit(40_000 * 1e18, user1);
        
        assertEq(vault.genesisPhaseActive(), true, "Genesis should still be active");
        assertEq(vault.genesisPhaseDeposits(), 40_000 * 1e18);
        
        // Second deposit: $60k (total $100k)
        vm.prank(user2);
        vault.deposit(60_000 * 1e18, user2);
        
        assertEq(vault.genesisPhaseActive(), false, "Genesis should end after $100k");
        assertEq(vault.genesisPhaseDeposits(), 100_000 * 1e18);
    }
    
    function test_GenesisPhase_ExceedsThreshold() public {
        // Deposit $150k in one go
        uint256 depositAmount = 150_000 * 1e18;
        
        vm.prank(user1);
        vault.deposit(depositAmount, user1);
        
        assertEq(vault.genesisPhaseActive(), false, "Genesis should end when exceeding threshold");
        assertEq(vault.genesisPhaseDeposits(), depositAmount, "All deposits tracked");
    }
    
    function test_GenesisPhase_ViewFunctionsAfterEnd() public {
        // End Genesis Phase
        vm.prank(admin);
        vault.endGenesisPhase();
        
        assertEq(vault.isGenesisPhaseActive(), false);
        assertEq(vault.getRemainingGenesisTVL(), 0, "Remaining should be 0 after end");
        assertEq(vault.getGenesisPhaseProgress(), 10000, "Progress should be 100% after end");
    }
}