// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "forge-std/Test.sol";
import "../../src/KerneTreasury.sol";

contract KerneTreasuryFixTest is Test {
    KerneTreasury treasury = KerneTreasury(payable(0xB656440287f8A1112558D3df915b23326e9b89ec));
    address constant OWNER = 0x57D400cED462a01Ed51a5De038F204Df49690A99;
    address constant KERNE_TOKEN = 0xfEA3D217F5f2304C8551dc9F5B5169F2c2d87340;
    address constant KERNE_STAKING = 0x032Af1631671126A689614c0c957De774b45D582;

    function setUp() public {
        vm.createSelectFork("https://mainnet.base.org");
    }

    function testTreasuryFix() public {
        console.log("Current KerneToken:", treasury.kerneToken());
        console.log("Current Staking:", treasury.stakingContract());
        console.log("Contract Owner:", treasury.owner());

        vm.startPrank(OWNER);
        console.log("Pranking as:", OWNER);
        
        console.log("Attempting setRouter...");
        treasury.setRouter(0xcF77a3Ba9A5CA399B7c97c74d54e5b1Beb874E43);
        console.log("setRouter success!");

        console.log("Forcing KerneToken to address(0)...");
        vm.store(address(treasury), bytes32(uint256(2)), bytes32(0));
        console.log("New current value:", treasury.kerneToken());

        (bool success, ) = address(treasury).call(abi.encodeWithSelector(0xe85bfb4d, KERNE_TOKEN));
        if (success) {
            console.log("Selector 0xe85bfb4d success after store!");
            console.log("New KerneToken value:", treasury.kerneToken());
        } else {
            console.log("Selector 0xe85bfb4d failed even after store!");
        }
        try treasury.setStakingContract(KERNE_STAKING) {
            console.log("setStakingContract success!");
        } catch (bytes memory reason) {
            console.log("setStakingContract failed with reason:");
            console.logBytes(reason);
        }
        
        vm.stopPrank();

        assertEq(treasury.kerneToken(), KERNE_TOKEN);
        assertEq(treasury.stakingContract(), KERNE_STAKING);
        
        console.log("Fixed KerneToken:", treasury.kerneToken());
        console.log("Fixed Staking:", treasury.stakingContract());
    }
}
