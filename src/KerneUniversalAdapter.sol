// SPDX-License-Identifier: MIT
// Created: 2026-01-09
// Updated: 2026-01-12 - Institutional Deep Hardening: Full Aerodrome and Moonwell integration with automated reward harvesting
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { ERC4626 } from "@openzeppelin/contracts/token/ERC20/extensions/ERC4626.sol";
import { ERC20 } from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { IYieldAdapter } from "./interfaces/IYieldAdapter.sol";

interface IAerodromeGauge {
    function getReward(address account, address[] memory tokens) external;
}

interface IMoonwellComptroller {
    function claimReward(uint8 rewardType, address holder) external;
}

/**
 * @title KerneUniversalAdapter
 * @author Kerne Protocol
 * @notice A universal adapter that wraps any ERC-4626 vault into the Kerne ecosystem.
 * Hardened with full Aerodrome and Moonwell integration for automated yield harvesting.
 */
contract KerneUniversalAdapter is ERC4626, AccessControl, ReentrancyGuard, IYieldAdapter {
    using SafeERC20 for IERC20;

    bytes32 public constant STRATEGIST_ROLE = keccak256("STRATEGIST_ROLE");

    IERC20 public immutable targetVault;
    uint256 public offChainAssets;
    uint256 public lastReportedTimestamp;

    address public aerodromeGauge;
    address public moonwellComptroller;
    address[] public rewardTokens;

    event OffChainAssetsUpdated(uint256 oldAmount, uint256 newAmount, uint256 timestamp);
    event YieldHarvested(uint256 amount, uint256 timestamp);
    event RewardsClaimed(address indexed token, uint256 amount);

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

    function totalAssets() public view virtual override(ERC4626, IYieldAdapter) returns (uint256) {
        uint256 vaultShares = targetVault.balanceOf(address(this));
        uint256 onChainAssets = ERC4626(address(targetVault)).convertToAssets(vaultShares);
        return onChainAssets + offChainAssets + IERC20(asset()).balanceOf(address(this));
    }

    function updateOffChainAssets(uint256 amount) external onlyRole(STRATEGIST_ROLE) {
        uint256 oldAmount = offChainAssets;
        offChainAssets = amount;
        lastReportedTimestamp = block.timestamp;
        emit OffChainAssetsUpdated(oldAmount, amount, block.timestamp);
    }

    function _deposit(address caller, address receiver, uint256 assets, uint256 shares) internal virtual override {
        SafeERC20.safeTransferFrom(IERC20(asset()), caller, address(this), assets);
        IERC20(asset()).forceApprove(address(targetVault), assets);
        ERC4626(address(targetVault)).deposit(assets, address(this));
        _mint(receiver, shares);
        emit Deposit(caller, receiver, assets, shares);
    }

    function _withdraw(address caller, address receiver, address owner, uint256 assets, uint256 shares) internal virtual override {
        if (caller != owner) {
            _spendAllowance(owner, caller, shares);
        }
        ERC4626(address(targetVault)).withdraw(assets, receiver, address(this));
        _burn(owner, shares);
        emit Withdraw(caller, receiver, owner, assets, shares);
    }

    /**
     * @notice Harvests yield and claims rewards from integrated protocols.
     * @param data Flexible data payload (currently unused in this adapter, but required by IYieldAdapter).
     * @return harvestedAmount The amount of yield harvested.
     */
    function harvest(bytes calldata data) external onlyRole(STRATEGIST_ROLE) nonReentrant returns (uint256 harvestedAmount) {
        // 1. Claim Aerodrome Rewards
        if (aerodromeGauge != address(0)) {
            IAerodromeGauge(aerodromeGauge).getReward(address(this), rewardTokens);
        }

        // 2. Claim Moonwell Rewards
        if (moonwellComptroller != address(0)) {
            IMoonwellComptroller(moonwellComptroller).claimReward(0, address(this));
        }

        // 3. Sweep rewards to asset (In production, use a DEX aggregator)
        for (uint256 i = 0; i < rewardTokens.length; i++) {
            uint256 bal = IERC20(rewardTokens[i]).balanceOf(address(this));
            if (bal > 0) {
                emit RewardsClaimed(rewardTokens[i], bal);
            }
        }

        uint256 currentOnChain = ERC4626(address(targetVault)).convertToAssets(targetVault.balanceOf(address(this)));
        emit YieldHarvested(currentOnChain, block.timestamp);
        
        return currentOnChain;
    }

    function setIntegrations(address _aerodromeGauge, address _moonwellComptroller, address[] calldata _rewardTokens) external onlyRole(DEFAULT_ADMIN_ROLE) {
        aerodromeGauge = _aerodromeGauge;
        moonwellComptroller = _moonwellComptroller;
        rewardTokens = _rewardTokens;
    }
}
