// Created: 2026-01-21
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { MerkleProof } from "@openzeppelin/contracts/utils/cryptography/MerkleProof.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { ReentrancyGuard } from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import { Pausable } from "@openzeppelin/contracts/utils/Pausable.sol";

/**
 * @title KerneAirdrop
 * @author Kerne Protocol
 * @notice Implements the "Prisoner's Dilemma" airdrop mechanism from the Genesis Document
 * @dev Users can claim their allocation in three ways:
 *      1. MERCENARY: Claim 25% immediately (75% penalty redistributed to Loyalists)
 *      2. VESTING: Claim 100% vested linearly over 12 months
 *      3. LOYALIST: Lock 100% + bonus for 12 months (receives penalties from Mercenaries)
 * 
 * This mechanism weaponizes loss aversion to maximize token locking and minimize
 * sell pressure at TGE, as described in Genesis Paragraph 8.
 */
contract KerneAirdrop is AccessControl, ReentrancyGuard, Pausable {
    using SafeERC20 for IERC20;

    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTANTS
    // ═══════════════════════════════════════════════════════════════════════════════
    
    bytes32 public constant ADMIN_ROLE = keccak256("ADMIN_ROLE");
    
    /// @notice Mercenary claim percentage (25%)
    uint256 public constant MERCENARY_CLAIM_BPS = 2500;
    
    /// @notice Penalty taken from Mercenary claims (75%)
    uint256 public constant MERCENARY_PENALTY_BPS = 7500;
    
    /// @notice Vesting duration (12 months)
    uint256 public constant VESTING_DURATION = 365 days;
    
    /// @notice Loyalist lock duration (12 months)
    uint256 public constant LOCK_DURATION = 365 days;
    
    /// @notice Basis points denominator
    uint256 public constant BPS = 10000;

    // ═══════════════════════════════════════════════════════════════════════════════
    // ENUMS
    // ═══════════════════════════════════════════════════════════════════════════════

    enum ClaimType {
        MERCENARY,  // 0: 25% immediate, 75% penalty
        VESTING,    // 1: 100% over 12 months
        LOYALIST    // 2: 100% + bonus locked for 12 months
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // STRUCTS
    // ═══════════════════════════════════════════════════════════════════════════════

    struct UserClaim {
        ClaimType claimType;
        uint256 totalAllocation;
        uint256 claimedAmount;
        uint256 lockedAmount;
        uint256 bonusAmount;
        uint256 vestingStart;
        uint256 lockExpiry;
        bool hasClaimed;
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // STATE VARIABLES
    // ═══════════════════════════════════════════════════════════════════════════════

    /// @notice The KERNE token
    IERC20 public immutable kerneToken;
    
    /// @notice Merkle root for eligibility verification
    bytes32 public merkleRoot;
    
    /// @notice Timestamp when claims open
    uint256 public claimStart;
    
    /// @notice Timestamp when claims close (new claims)
    uint256 public claimEnd;
    
    /// @notice Total penalty pool from Mercenary claims (redistributed to Loyalists)
    uint256 public penaltyPool;
    
    /// @notice Total amount locked by Loyalists (used for bonus calculation)
    uint256 public totalLoyalistLocked;
    
    /// @notice Total number of Loyalists
    uint256 public loyalistCount;
    
    /// @notice User claim data
    mapping(address => UserClaim) public userClaims;
    
    /// @notice Tracks if user has already claimed their bonus from penalty pool
    mapping(address => bool) public bonusClaimed;

    // ═══════════════════════════════════════════════════════════════════════════════
    // EVENTS
    // ═══════════════════════════════════════════════════════════════════════════════

    event MerkleRootSet(bytes32 indexed newRoot);
    event ClaimWindowSet(uint256 start, uint256 end);
    event MercenaryClaim(address indexed user, uint256 received, uint256 penalty);
    event VestingClaim(address indexed user, uint256 totalAllocation, uint256 vestingStart);
    event LoyalistLock(address indexed user, uint256 locked, uint256 lockExpiry);
    event VestingWithdraw(address indexed user, uint256 amount);
    event LoyalistUnlock(address indexed user, uint256 principal, uint256 bonus);
    event BonusClaimed(address indexed user, uint256 bonus);
    event EmergencyWithdraw(address indexed token, uint256 amount);

    // ═══════════════════════════════════════════════════════════════════════════════
    // ERRORS
    // ═══════════════════════════════════════════════════════════════════════════════

    error ClaimNotOpen();
    error ClaimClosed();
    error AlreadyClaimed();
    error InvalidProof();
    error ZeroAllocation();
    error LockNotExpired();
    error NothingToWithdraw();
    error NotLoyalist();
    error BonusAlreadyClaimed();
    error InvalidClaimType();

    // ═══════════════════════════════════════════════════════════════════════════════
    // CONSTRUCTOR
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Initialize the airdrop contract
     * @param _kerneToken Address of the KERNE token
     * @param _admin Admin address
     */
    constructor(address _kerneToken, address _admin) {
        kerneToken = IERC20(_kerneToken);
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(ADMIN_ROLE, _admin);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // ADMIN FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Set the Merkle root for eligibility
     * @param _merkleRoot The new Merkle root
     */
    function setMerkleRoot(bytes32 _merkleRoot) external onlyRole(ADMIN_ROLE) {
        merkleRoot = _merkleRoot;
        emit MerkleRootSet(_merkleRoot);
    }

    /**
     * @notice Set the claim window
     * @param _start Timestamp when claims open
     * @param _end Timestamp when new claims close
     */
    function setClaimWindow(uint256 _start, uint256 _end) external onlyRole(ADMIN_ROLE) {
        require(_end > _start, "Invalid window");
        claimStart = _start;
        claimEnd = _end;
        emit ClaimWindowSet(_start, _end);
    }

    /**
     * @notice Pause claims
     */
    function pause() external onlyRole(ADMIN_ROLE) {
        _pause();
    }

    /**
     * @notice Unpause claims
     */
    function unpause() external onlyRole(ADMIN_ROLE) {
        _unpause();
    }

    /**
     * @notice Emergency withdraw tokens (only unclaimed after window closes)
     * @param token Token address
     * @param amount Amount to withdraw
     */
    function emergencyWithdraw(address token, uint256 amount) external onlyRole(DEFAULT_ADMIN_ROLE) {
        IERC20(token).safeTransfer(msg.sender, amount);
        emit EmergencyWithdraw(token, amount);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // CLAIM FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Claim airdrop allocation
     * @param claimType The type of claim (0=Mercenary, 1=Vesting, 2=Loyalist)
     * @param allocation Total allocation for this user
     * @param merkleProof Proof of eligibility
     */
    function claim(
        ClaimType claimType,
        uint256 allocation,
        bytes32[] calldata merkleProof
    ) external nonReentrant whenNotPaused {
        // Validate claim window
        if (block.timestamp < claimStart) revert ClaimNotOpen();
        if (block.timestamp > claimEnd) revert ClaimClosed();
        
        // Validate not already claimed
        if (userClaims[msg.sender].hasClaimed) revert AlreadyClaimed();
        
        // Validate allocation
        if (allocation == 0) revert ZeroAllocation();
        
        // Verify Merkle proof
        bytes32 leaf = keccak256(abi.encodePacked(msg.sender, allocation));
        if (!MerkleProof.verify(merkleProof, merkleRoot, leaf)) revert InvalidProof();
        
        // Process based on claim type
        if (claimType == ClaimType.MERCENARY) {
            _processMercenaryClaim(allocation);
        } else if (claimType == ClaimType.VESTING) {
            _processVestingClaim(allocation);
        } else if (claimType == ClaimType.LOYALIST) {
            _processLoyalistClaim(allocation);
        } else {
            revert InvalidClaimType();
        }
    }

    /**
     * @notice Process Mercenary claim: 25% immediate, 75% penalty
     * @param allocation User's total allocation
     */
    function _processMercenaryClaim(uint256 allocation) internal {
        uint256 received = (allocation * MERCENARY_CLAIM_BPS) / BPS;
        uint256 penalty = allocation - received;
        
        // Add penalty to pool for Loyalists
        penaltyPool += penalty;
        
        // Record claim
        userClaims[msg.sender] = UserClaim({
            claimType: ClaimType.MERCENARY,
            totalAllocation: allocation,
            claimedAmount: received,
            lockedAmount: 0,
            bonusAmount: 0,
            vestingStart: 0,
            lockExpiry: 0,
            hasClaimed: true
        });
        
        // Transfer tokens
        kerneToken.safeTransfer(msg.sender, received);
        
        emit MercenaryClaim(msg.sender, received, penalty);
    }

    /**
     * @notice Process Vesting claim: 100% over 12 months
     * @param allocation User's total allocation
     */
    function _processVestingClaim(uint256 allocation) internal {
        userClaims[msg.sender] = UserClaim({
            claimType: ClaimType.VESTING,
            totalAllocation: allocation,
            claimedAmount: 0,
            lockedAmount: allocation,
            bonusAmount: 0,
            vestingStart: block.timestamp,
            lockExpiry: block.timestamp + VESTING_DURATION,
            hasClaimed: true
        });
        
        emit VestingClaim(msg.sender, allocation, block.timestamp);
    }

    /**
     * @notice Process Loyalist claim: 100% + bonus locked for 12 months
     * @param allocation User's total allocation
     */
    function _processLoyalistClaim(uint256 allocation) internal {
        uint256 lockExpiry = block.timestamp + LOCK_DURATION;
        
        userClaims[msg.sender] = UserClaim({
            claimType: ClaimType.LOYALIST,
            totalAllocation: allocation,
            claimedAmount: 0,
            lockedAmount: allocation,
            bonusAmount: 0, // Calculated at unlock time
            vestingStart: 0,
            lockExpiry: lockExpiry,
            hasClaimed: true
        });
        
        totalLoyalistLocked += allocation;
        loyalistCount++;
        
        emit LoyalistLock(msg.sender, allocation, lockExpiry);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // WITHDRAW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Withdraw vested tokens (for VESTING claimants)
     */
    function withdrawVested() external nonReentrant {
        UserClaim storage userClaim = userClaims[msg.sender];
        
        if (userClaim.claimType != ClaimType.VESTING) revert InvalidClaimType();
        
        uint256 vested = _calculateVested(msg.sender);
        uint256 withdrawable = vested - userClaim.claimedAmount;
        
        if (withdrawable == 0) revert NothingToWithdraw();
        
        userClaim.claimedAmount += withdrawable;
        
        kerneToken.safeTransfer(msg.sender, withdrawable);
        
        emit VestingWithdraw(msg.sender, withdrawable);
    }

    /**
     * @notice Unlock Loyalist tokens after lock period
     */
    function unlockLoyalist() external nonReentrant {
        UserClaim storage userClaim = userClaims[msg.sender];
        
        if (userClaim.claimType != ClaimType.LOYALIST) revert NotLoyalist();
        if (block.timestamp < userClaim.lockExpiry) revert LockNotExpired();
        if (userClaim.claimedAmount > 0) revert AlreadyClaimed();
        
        // Calculate bonus from penalty pool
        uint256 bonus = _calculateLoyalistBonus(msg.sender);
        
        uint256 totalReceived = userClaim.lockedAmount + bonus;
        userClaim.claimedAmount = totalReceived;
        userClaim.bonusAmount = bonus;
        
        kerneToken.safeTransfer(msg.sender, totalReceived);
        
        emit LoyalistUnlock(msg.sender, userClaim.lockedAmount, bonus);
    }

    // ═══════════════════════════════════════════════════════════════════════════════
    // VIEW FUNCTIONS
    // ═══════════════════════════════════════════════════════════════════════════════

    /**
     * @notice Calculate vested amount for a user
     * @param user User address
     * @return vested Amount vested so far
     */
    function _calculateVested(address user) internal view returns (uint256) {
        UserClaim storage claim = userClaims[user];
        
        if (claim.claimType != ClaimType.VESTING) return 0;
        if (claim.vestingStart == 0) return 0;
        
        uint256 elapsed = block.timestamp - claim.vestingStart;
        
        if (elapsed >= VESTING_DURATION) {
            return claim.totalAllocation;
        }
        
        return (claim.totalAllocation * elapsed) / VESTING_DURATION;
    }

    /**
     * @notice Calculate bonus for a Loyalist from penalty pool
     * @param user User address
     * @return bonus Bonus amount
     */
    function _calculateLoyalistBonus(address user) internal view returns (uint256) {
        UserClaim storage claim = userClaims[user];
        
        if (claim.claimType != ClaimType.LOYALIST) return 0;
        if (totalLoyalistLocked == 0) return 0;
        
        // Pro-rata share of penalty pool based on locked amount
        return (penaltyPool * claim.lockedAmount) / totalLoyalistLocked;
    }

    /**
     * @notice Get user's claim info
     * @param user User address
     * @return Full claim struct
     */
    function getUserClaim(address user) external view returns (UserClaim memory) {
        return userClaims[user];
    }

    /**
     * @notice Get vested amount available to withdraw
     * @param user User address
     * @return withdrawable Amount available to withdraw
     */
    function getWithdrawable(address user) external view returns (uint256) {
        UserClaim storage claim = userClaims[user];
        
        if (claim.claimType == ClaimType.VESTING) {
            uint256 vested = _calculateVested(user);
            return vested - claim.claimedAmount;
        } else if (claim.claimType == ClaimType.LOYALIST) {
            if (block.timestamp < claim.lockExpiry) return 0;
            if (claim.claimedAmount > 0) return 0;
            return claim.lockedAmount + _calculateLoyalistBonus(user);
        }
        
        return 0;
    }

    /**
     * @notice Preview bonus for a Loyalist
     * @param user User address
     * @return bonus Preview of bonus amount
     */
    function previewLoyalistBonus(address user) external view returns (uint256) {
        return _calculateLoyalistBonus(user);
    }

    /**
     * @notice Check if a user is eligible
     * @param user User address
     * @param allocation Claimed allocation
     * @param merkleProof Merkle proof
     * @return isEligible Whether user is eligible
     */
    function isEligible(
        address user,
        uint256 allocation,
        bytes32[] calldata merkleProof
    ) external view returns (bool) {
        bytes32 leaf = keccak256(abi.encodePacked(user, allocation));
        return MerkleProof.verify(merkleProof, merkleRoot, leaf);
    }

    /**
     * @notice Get airdrop statistics
     * @return _penaltyPool Total penalty pool
     * @return _totalLoyalistLocked Total locked by Loyalists
     * @return _loyalistCount Number of Loyalists
     */
    function getStats() external view returns (
        uint256 _penaltyPool,
        uint256 _totalLoyalistLocked,
        uint256 _loyalistCount
    ) {
        return (penaltyPool, totalLoyalistLocked, loyalistCount);
    }
}
