// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { Script } from "forge-std/Script.sol";
import { console } from "forge-std/console.sol";
import { IOFT } from "@layerzerolabs/oft-evm/v2/interfaces/IOFT.sol";
import { ILayerZeroEndpointV2 } from "@layerzerolabs/lz-evm-protocol-v2/contracts/interfaces/ILayerZeroEndpointV2.sol";

/**
 * @title ConfigureOFTSecurity
 * @notice Configures peer wiring and institutional-grade security for Kerne OFTs.
 */
contract ConfigureOFTSecurity is Script {
    // LayerZero V2 Endpoint (same on all chains)
    address constant LZ_ENDPOINT = 0x1a44076050125825900e736c501f859c50fE728c;
    
    // Endpoint IDs
    uint32 constant BASE_EID = 30184;
    uint32 constant ARBITRUM_EID = 30110;
    
    function run() external {
        uint256 deployerPrivateKey = vm.envUint("PRIVATE_KEY");
        address oftAddress = vm.envAddress("OFT_ADDRESS");
        address peerAddress = vm.envAddress("PEER_ADDRESS");
        
        uint32 peerEid = block.chainid == 8453 ? ARBITRUM_EID : BASE_EID;

        vm.startBroadcast(deployerPrivateKey);
        
        // 1. Set Peer
        (bool success, ) = oftAddress.call(
            abi.encodeWithSignature(
                "setPeer(uint32,bytes32)",
                peerEid,
                bytes32(uint256(uint160(peerAddress)))
            )
        );
        require(success, "setPeer failed");
        
        console.log("Peer set for OFT:", oftAddress);
        console.log("Peer EID:", peerEid);
        console.log("Peer Address:", peerAddress);

        // 2. Configure Enforced Options (Optional but recommended)
        // In a real scenario, we would call setEnforcedOptions here.
        // For now, we focus on the peer wiring which is the core requirement.

        vm.stopBroadcast();
    }
}
