// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "forge-std/Test.sol";
import "src/KerneOFTV2.sol";
import "src/KerneArbSettler.sol";
import "src/mocks/EndpointV2Mock.sol";

contract ArbitrumExpansionTest is Test {
    KerneOFTV2 kusdBase;
    KerneOFTV2 kusdArb;
    KerneArbSettler settler;
    
    EndpointV2Mock endpointBase;
    EndpointV2Mock endpointArb;
    
    address admin = address(0x1);
    address baseTreasury = address(0x2);
    address user = address(0x3);
    
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;

    function setUp() public {
        endpointBase = new EndpointV2Mock();
        endpointArb = new EndpointV2Mock();
        
        kusdBase = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", address(endpointBase), admin);
        kusdArb = new KerneOFTV2("Kerne Synthetic Dollar", "kUSD", address(endpointArb), admin);
        
        settler = new KerneArbSettler(address(kusdArb), baseTreasury, admin);
        
        vm.label(address(kusdBase), "kUSD_Base");
        vm.label(address(kusdArb), "kUSD_Arb");
        vm.label(address(settler), "KerneArbSettler");
    }

    function testPeerWiring() public {
        vm.startPrank(admin);
        
        // Wire Base to Arb
        kusdBase.setPeer(ARBITRUM_EID, bytes32(uint256(uint160(address(kusdArb)))));
        
        // Wire Arb to Base
        kusdArb.setPeer(BASE_EID, bytes32(uint256(uint160(address(kusdBase)))));
        
        assertEq(kusdBase.peers(ARBITRUM_EID), bytes32(uint256(uint160(address(kusdArb)))));
        assertEq(kusdArb.peers(BASE_EID), bytes32(uint256(uint160(address(kusdBase)))));
        
        vm.stopPrank();
    }

    function testSettlementAccumulation() public {
        vm.startPrank(admin);
        settler.accumulateProfits(500e18);
        assertEq(settler.pendingProfits(), 500e18);
        vm.stopPrank();
    }

    function testSettlementExecution() public {
        // 1. Setup Peer Wiring
        testPeerWiring();
        
        // 2. Accumulate profits on Arbitrum
        vm.startPrank(admin);
        settler.accumulateProfits(1000e18);
        
        // 3. Mint kUSD to settler on Arbitrum (simulating arb profit)
        kusdArb.mint(address(settler), 1000e18);
        assertEq(kusdArb.balanceOf(address(settler)), 1000e18);
        
        // 4. Settle to Base
        // We need to mock the LayerZero fee and send call
        // Since we are using mocks, we just verify the call is made
        
        // In a real test with EndpointV2Mock, we would verify the message delivery
        // For now, we verify the state changes in the settler
        
        // Note: EndpointV2Mock might not implement quoteSend/send fully
        // Let's check EndpointV2Mock.sol if possible
        
        vm.deal(admin, 1 ether);
        settler.settle{value: 0.1 ether}("");
        
        assertEq(settler.pendingProfits(), 0);
        // Balance of settler should be 0 as it was burned/sent
        assertEq(kusdArb.balanceOf(address(settler)), 0);
        
        vm.stopPrank();
    }
}
