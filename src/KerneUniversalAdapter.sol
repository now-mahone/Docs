// SPDX-License-Identifier: MIT
// Created: 2026-01-09
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";

/**
 * @title KerneUniversalAdapter
 * @author Kerne Protocol
 * @notice A universal adapter that wraps any ERC-4626 vault into the Kerne ecosystem.
 * This allows Kerne to leverage external yield sources while maintaining delta-neutrality.
 */
contract KerneUniversalAdapter is ERC4626, AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    /// @notice The external ERC-4626 vault being wrapped
    IERC20 public immutable targetVault;

    /// @notice Off-chain assets for delta-neutral hedging
    uint256 public offChainAssets;

    /// @notice Last time off-chain assets were reported
    uint256 public lastReportedTimestamp;

    event OffChainAssetsUpdated(uint256 oldAmount, uint256 newAmount, uint256 timestamp);

    constructor(
        IERC20 _asset,
        IERC20 _targetVault,
        string memory _name,
        string memory _symbol,
        address _admin,
        address _strategist
    ) ERC4626(_asset) ERC20(_name, _symbol) {
        targetVault = _targetVault;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(STRATEGIST_ROLE, _strategist);
    }

    /**
     * @notice Returns the total amount of assets managed by the adapter.
     * Includes assets in the target vault and off-chain hedging assets.
     */
    function totalAssets() public view virtual override returns (uint256) {
        // Assets in target vault = targetVault.previewRedeem(targetVault.balanceOf(address(this)))
        // But targetVault is IERC20, we need to cast it to ERC4626 to use previewRedeem
        uint256 vaultShares = targetVault.balanceOf(address(this));
        uint256 onChainAssets = ERC4626(address(targetVault)).convertToAssets(vaultShares);
        return onChainAssets + offChainAssets + IERC20(asset()).balanceOf(address(this));
    }

    /**
     * @notice Updates the amount of assets held off-chain for hedging.
     */
    function updateOffChainAssets(uint256 amount) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAmount = offChainAssets;
        offChainAssets = amount;
        lastReportedTimestamp = block.timestamp;
        emit OffChainAssetsUpdated(oldAmount, amount, block.timestamp);
    }

    /**
     * @dev Internal deposit logic: deposits into the target vault.
     */
    function _deposit(address caller, address receiver, uint256 assets, uint256 shares) internal virtual override {
        // 1. Transfer assets from caller to this contract
        SafeERC20.safeTransferFrom(IERC20(asset()), caller, address(this), assets);

        // 2. Deposit assets into the target vault
        // We use forceApprove to handle USDT-like tokens and ensure targetVault can pull assets
        IERC20(asset()).forceApprove(address(targetVault), assets);
        
        // We use the assets amount to deposit into the target vault.
        // The target vault will mint its own shares to this adapter.
        ERC4626(address(targetVault)).deposit(assets, address(this));

        // 3. Mint adapter shares to receiver
        _mint(receiver, shares);

        emit Deposit(caller, receiver, assets, shares);
    }

    /**
     * @notice Sweeps assets to an external address (e.g., for CEX deposit).
     * @param amount The amount of underlying assets to sweep.
     * @param destination The address to receive the assets.
     */
    function sweepToExchange(uint256 amount, address destination) external onlyRole(DEFAULT_ADMIN_ROLE) nonReentrant {
        require(destination != address(0), "Invalid destination");
        
        uint256 liquidBalance = IERC20(asset()).balanceOf(address(this));
        if (liquidBalance < amount) {
            // If not enough liquid, withdraw from target vault
            uint256 needed = amount - liquidBalance;
            ERC4626(address(targetVault)).withdraw(needed, address(this), address(this));
        }
        
        SafeERC20.safeTransfer(IERC20(asset()), destination, amount);
    }

    /**
     * @dev Internal withdraw logic: withdraws from the target vault.
     */
    function _withdraw(
        address caller,
        address receiver,
        address owner,
        uint256 assets,
        uint256 shares
    ) internal virtual override {
        if (caller != owner) {
            _spendAllowance(owner, caller, shares);
        }

        // 1. Withdraw assets from the target vault
        // We need to ensure we have enough liquid assets in the target vault
        ERC4626(address(targetVault)).withdraw(assets, receiver, address(this));

        // 2. Burn adapter shares
        _burn(owner, shares);

        emit Withdraw(caller, receiver, owner, assets, shares);
    }
}
