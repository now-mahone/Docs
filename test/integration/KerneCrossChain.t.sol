// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "src/KerneOFTV2.sol";
import "src/mocks/EndpointV2Mock.sol";

contract KerneCrossChainTest is Test {
    KerneOFTV2 kusdBase;
    KerneOFTV2 kusdArb;
    
    EndpointV2Mock endpointBase;
    EndpointV2Mock endpointArb;
    
    address user = address(0x3);

    function setUp() public {
        endpointBase = new EndpointV2Mock();
        endpointArb = new EndpointV2Mock();
        
        kusdBase = new KerneOFTV2("kUSD", "kUSD", address(endpointBase), address(this));
        kusdArb = new KerneOFTV2("kUSD", "kUSD", address(endpointArb), address(this));
        
        vm.label(address(kusdBase), "kUSD_Base");
        vm.label(address(kusdArb), "kUSD_Arb");
    }


    function testOFTDeployment() public {
        assertEq(kusdBase.name(), "kUSD");
        assertEq(kusdArb.symbol(), "kUSD");
    }

    function testMinting() public {
        kusdBase.mint(user, 1000e18);
        assertEq(kusdBase.balanceOf(user), 1000e18);
    }

    function testSetPeer() public {
        uint32 arbEid = 2;
        bytes32 arbPeer = bytes32(uint256(uint160(address(kusdArb))));
        
        kusdBase.setPeer(arbEid, arbPeer);
        assertEq(kusdBase.peers(arbEid), arbPeer);
    }
}

