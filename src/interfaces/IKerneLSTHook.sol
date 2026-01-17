// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IKerneLSTHook {
    function updateShadowYield(address vault, uint256 amount) external;
    function getVerifiedAssets(address vault) external view returns (uint256);
}
