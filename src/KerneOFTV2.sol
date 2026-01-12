// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { OFT } from "@layerzerolabs/oft-evm/OFT.sol";

/**
 * @title KerneOFTV2
 * @author Kerne Protocol
 * @notice Omnichain Fungible Token for kUSD and $KERNE using LayerZero V2.
 * @dev Implements OFTCompose for seamless cross-chain yield.
 */
contract KerneOFTV2 is OFT {
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint
    ) OFT(_name, _symbol, _lzEndpoint) {}

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
