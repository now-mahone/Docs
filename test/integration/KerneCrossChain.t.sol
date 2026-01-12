// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../../src/KerneOFTV2.sol";

contract KerneCrossChainTest is Test {
    KerneOFTV2 kusdBase;
    KerneOFTV2 kusdArb;
    
    address lzEndpointBase = address(0x1);
    address lzEndpointArb = address(0x2);
    address user = address(0x3);

    function setUp() public {
        kusdBase = new KerneOFTV2("kUSD", "kUSD", lzEndpointBase);
        kusdArb = new KerneOFTV2("kUSD", "kUSD", lzEndpointArb);
        
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
}
