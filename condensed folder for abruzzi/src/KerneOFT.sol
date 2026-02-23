// Created: 2026-01-12
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import { OFT } from "@layerzerolabs/oft-evm/v1/OFT.sol";

/**
 * @title KerneOFT
 * @author Kerne Protocol
 * @notice Omnichain Fungible Token for kUSD and $KERNE using LayerZero V1.
 * @dev Inherits from LayerZero V1 OFT which already includes Ownable via NonblockingLzApp.
 */
contract KerneOFT is OFT {
    constructor(
        string memory _name,
        string memory _symbol,
        address _lzEndpoint
    ) OFT(_name, _symbol, _lzEndpoint) {}

    /**
     * @notice Mints tokens on the destination chain.
     * @dev Only callable by the owner (inherited from LzApp -> Ownable).
     */
    function mint(address _to, uint256 _amount) external onlyOwner {
        _mint(_to, _amount);
    }

    /**
     * @notice Burns tokens on the source chain.
     * @dev Only callable by the owner.
     */
    function burn(address _from, uint256 _amount) external onlyOwner {
        _burn(_from, _amount);
    }
}
