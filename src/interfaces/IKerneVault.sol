// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IKerneVault {
    function getSolvencyRatio() external view returns (uint256);
    function totalSupply() external view returns (uint256);
    function totalAssets() external view returns (uint256);
    function offChainAssets() external view returns (uint256);
    function hedgingReserve() external view returns (uint256);
}
