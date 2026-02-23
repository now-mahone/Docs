// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IKerneLSTSolver {
    function executeLSTSwap(
        address tokenIn,
        address tokenOut,
        uint256 amount,
        bytes calldata data
    ) external returns (uint256);
}
