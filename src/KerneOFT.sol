// Created: 2026-01-06
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "lib/solidity-examples/contracts/token/oft/v2/OFTV2.sol";

/**
 * @title KerneOFT
 * @author Kerne Protocol
 * @notice Omnichain Fungible Token for kUSD and $KERNE.
 */
contract KerneOFT is OFTV2 {
    constructor(
        string memory _name,
        string memory _symbol,
        uint8 _sharedDecimals,
        address _lzEndpoint
    ) OFTV2(_name, _symbol, _sharedDecimals, _lzEndpoint) { }

    /**
     * @notice Mints tokens on the destination chain.
     * @dev Only callable by the LayerZero endpoint via the OFT mechanism.
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
