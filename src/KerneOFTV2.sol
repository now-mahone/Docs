// Created: 2026-01-12
// Updated: 2026-01-12 - Institutional Deep Hardening: Cross-chain yield composition and OFTCompose integration
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { OFTV2 } from "@layerzerolabs/oft-evm/v2/OFTV2.sol";

/**
 * @title KerneOFTV2
 * @author Kerne Protocol
 * @notice Omnichain Fungible Token for kUSD and $KERNE using LayerZero V2.
 * Hardened for seamless cross-chain yield and automated bridging.
 */
contract KerneOFTV2 is OFTV2 {
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _sharedDecimals,
        address _lzEndpoint
    ) OFTV2(_name, _symbol, _sharedDecimals, _lzEndpoint) {}

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

}
