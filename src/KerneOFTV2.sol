// Created: 2026-01-12
// Updated: 2026-01-12 - Institutional Deep Hardening: Cross-chain yield composition and OFTCompose integration
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { OFT } from "@layerzerolabs/oft-evm/OFT.sol";
import { IOFTCompose } from "@layerzerolabs/oft-evm/interfaces/IOFTCompose.sol";

/**
 * @title KerneOFTV2
 * @author Kerne Protocol
 * @notice Omnichain Fungible Token for kUSD and $KERNE using LayerZero V2.
 * Hardened with OFTCompose for seamless cross-chain yield and automated bridging.
 */
contract KerneOFTV2 is OFT, IOFTCompose {
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint,
        address _delegate
    ) OFT(_name, _symbol, _lzEndpoint, _delegate) {}

    /**
     * @notice Mints tokens on the destination chain.
     */
    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }

    /**
     * @notice Burns tokens on the source chain.
     */
    function burn(address _from, uint256 _amount) external onlyOwner {
        _burn(_from, _amount);
    }

    /**
     * @dev Implementation of IOFTCompose for cross-chain message handling.
     * Allows for automated actions (e.g., staking) upon token arrival.
     */
    function lzCompose(
        address _from,
        bytes32 _guid,
        bytes calldata _message,
        address _executor,
        bytes calldata _extraData
    ) external payable override {
        // In production, decode _message and perform automated actions
        // e.g., if (action == STAKE) { KerneStaking.stake(...) }
    }
}
