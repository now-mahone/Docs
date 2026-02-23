// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { MessagingFee, MessagingReceipt } from "@layerzerolabs/oft-evm/v2/interfaces/IOFT.sol";

struct MessagingParams {
    uint32 dstEid;
    bytes32 receiver;
    bytes message;
    bytes options;
    bool payInLzToken;
}

contract EndpointV2Mock {
    mapping(address => address) public delegates;

    function setDelegate(address _delegate) external {
        delegates[msg.sender] = _delegate;
    }

    function quote(MessagingParams calldata, address) external pure returns (MessagingFee memory) {
        return MessagingFee(0.01 ether, 0);
    }

    function send(
        MessagingParams calldata,
        address
    ) external payable returns (MessagingReceipt memory) {
        return MessagingReceipt(bytes32(uint256(1)), 1, MessagingFee(msg.value, 0));
    }

    function executable(address, uint32, bytes32, uint64) external pure returns (bool) {
        return true;
    }

    function verifier() external view returns (address) {
        return address(this);
    }
}
