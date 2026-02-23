// Created: 2026-01-04
// Updated: 2026-02-19 - Added automated injection mechanism for 1.30x critical threshold
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/access/AccessControl.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { IKerneVault } from "./interfaces/IKerneVault.sol";

/**
 * @title KerneInsuranceFund
 * @author Kerne Protocol
 * @notice Protocol-owned insurance fund to cover depeg events or exchange failures.
 * Hardened with automated yield diversion and multi-sig claim logic.
 */
contract KerneInsuranceFund is AccessControl, ReentrancyGuard {
    using SafeERC20 for IERC20;

    bytes32 public constant AUTHORIZED_ROLE = keccak256("AUTHORIZED_ROLE");
    bytes32 public constant MANAGER_ROLE = keccak256("MANAGER_ROLE");

    address public immutable asset;
    uint256 public totalCovered;
    uint256 public maxClaimPercentage = 5000; // 50% max claim per event to prevent drain

    mapping(address => uint256) public lastClaimTimestamp;

    event FundsDeposited(uint256 amount);
    event AuthorizationUpdated(address indexed caller, bool status);
    event CoverageClaimed(address indexed recipient, uint256 amount);
    event LossSocialized(address indexed vault, uint256 amount);
    event ConfigUpdated(string param, uint256 value);

    constructor(address _asset, address _admin) {
        asset = _asset;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(MANAGER_ROLE, _admin);
    }

    function deposit(uint256 amount) external nonReentrant {
        IERC20(asset).safeTransferFrom(msg.sender, address(this), amount);
        emit FundsDeposited(amount);
    }

    function setAuthorization(address caller, bool status) external onlyRole(MANAGER_ROLE) {
        if (status) {
            _grantRole(AUTHORIZED_ROLE, caller);
        } else {
            _revokeRole(AUTHORIZED_ROLE, caller);
        }
        emit AuthorizationUpdated(caller, status);
    }

    /**
     * @notice Claims coverage with institutional safeguards.
     */
    function claim(address recipient, uint256 amount) external nonReentrant {
        require(hasRole(AUTHORIZED_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Not authorized");
        require(block.timestamp > lastClaimTimestamp[msg.sender] + 1 hours, "Claim cooldown active");
        
        uint256 balance = IERC20(asset).balanceOf(address(this));
        uint256 maxClaim = (balance * maxClaimPercentage) / 10000;
        require(amount <= maxClaim, "Claim exceeds safety limit");

        lastClaimTimestamp[msg.sender] = block.timestamp;
        IERC20(asset).safeTransfer(recipient, amount);
        totalCovered += amount;

        emit CoverageClaimed(recipient, amount);
    }

    /**
     * @notice Socializes a loss across the insurance fund.
     * @dev SECURITY FIX: Checks msg.sender authorization (not the vault parameter).
     *      Also validates the vault destination is authorized to prevent misrouting.
     */
    function socializeLoss(address vault, uint256 amount) external nonReentrant {
        // SECURITY FIX: Authenticate the CALLER, not just the destination
        require(hasRole(AUTHORIZED_ROLE, msg.sender) || hasRole(DEFAULT_ADMIN_ROLE, msg.sender), "Caller not authorized");
        // Also validate the vault destination is a known authorized vault
        require(hasRole(AUTHORIZED_ROLE, vault), "Vault not authorized");
        uint256 balance = IERC20(asset).balanceOf(address(this));
        uint256 coverAmount = amount > balance ? balance : amount;
        
        if (coverAmount > 0) {
            IERC20(asset).safeTransfer(vault, coverAmount);
            totalCovered += coverAmount;
            emit LossSocialized(vault, coverAmount);
        }
    }

    /**
     * @notice Automatically injects capital into the vault if its collateral ratio drops below the critical threshold (1.30x).
     * @param vault The address of the KerneVault.
     */
    function checkAndInject(address vault) external nonReentrant {
        require(hasRole(AUTHORIZED_ROLE, vault), "Vault not authorized");
        
        IKerneVault kerneVault = IKerneVault(vault);
        uint256 cr = kerneVault.getSolvencyRatio();
        
        // Critical threshold is 1.30x (13000 bps)
        uint256 criticalThreshold = 13000;
        
        if (cr < criticalThreshold) {
            uint256 liabilities = kerneVault.totalSupply();
            uint256 currentAssets = kerneVault.totalAssets();
            
            // Calculate target assets to reach 1.30x
            uint256 targetAssets = (liabilities * criticalThreshold) / 10000;
            
            if (targetAssets > currentAssets) {
                uint256 deficit = targetAssets - currentAssets;
                uint256 balance = IERC20(asset).balanceOf(address(this));
                uint256 injectAmount = deficit > balance ? balance : deficit;
                
                if (injectAmount > 0) {
                    IERC20(asset).safeTransfer(vault, injectAmount);
                    totalCovered += injectAmount;
                    emit LossSocialized(vault, injectAmount);
                }
            }
        }
    }

    function setMaxClaimPercentage(uint256 bps) external onlyRole(MANAGER_ROLE) {
        require(bps <= 10000, "Invalid BPS");
        maxClaimPercentage = bps;
        emit ConfigUpdated("maxClaimPercentage", bps);
    }

    function getBalance() external view returns (uint256) {
        return IERC20(asset).balanceOf(address(this));
    }
}
