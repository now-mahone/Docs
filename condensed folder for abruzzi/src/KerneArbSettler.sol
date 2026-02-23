// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

import { IERC20 } from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import { SafeERC20 } from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import { AccessControl } from "@openzeppelin/contracts/access/AccessControl.sol";
import { IOFT, SendParam, MessagingFee, MessagingReceipt } from "@layerzerolabs/oft-evm/v2/interfaces/IOFT.sol";

/**
 * @title KerneArbSettler
 * @notice Batches arb profits on Arbitrum and settles to Base Treasury via OFT.
 * @dev Institutional-grade cross-chain settlement for the Kerne ecosystem.
 */
contract KerneArbSettler is AccessControl {
    using SafeERC20 for IERC20;

    bytes32 public constant SETTLER_ROLE = keccak256("SETTLER_ROLE");
    
    IOFT public immutable kusdOFT;        // kUSD OFT on Arbitrum
    uint32 public constant BASE_EID = 30184;  // Base endpoint ID
    address public baseTreasury;           // Treasury address on Base
    
    uint256 public minSettleAmount = 100e18;  // Min 100 kUSD to settle
    uint256 public pendingProfits;
    
    event ProfitsAccumulated(address indexed token, uint256 amount);
    event SettlementSent(uint256 amount, bytes32 guid);
    event BaseTreasuryUpdated(address oldTreasury, address newTreasury);
    
    constructor(address _kusdOFT, address _baseTreasury, address _admin) {
        kusdOFT = IOFT(_kusdOFT);
        baseTreasury = _baseTreasury;
        _grantRole(DEFAULT_ADMIN_ROLE, _admin);
        _grantRole(SETTLER_ROLE, _admin);
    }
    
    /**
     * @notice Accumulates profits from arbitrage operations.
     * @param amount The amount of kUSD to accumulate.
     */
    function accumulateProfits(uint256 amount) external onlyRole(SETTLER_ROLE) {
        pendingProfits += amount;
        emit ProfitsAccumulated(address(kusdOFT), amount);
    }
    
    /**
     * @notice Settles accumulated profits to Base Treasury via LayerZero OFT.
     * @param _extraOptions LayerZero extra options (e.g. for gas limit).
     */
    function settle(bytes calldata _extraOptions) external payable onlyRole(SETTLER_ROLE) {
        require(pendingProfits >= minSettleAmount, "Below min settle");
        
        uint256 toSettle = pendingProfits;
        pendingProfits = 0;
        
        SendParam memory params = SendParam({
            dstEid: BASE_EID,
            to: bytes32(uint256(uint160(baseTreasury))),
            amountLD: toSettle,
            minAmountLD: (toSettle * 9900) / 10000, // 1% slippage max
            extraOptions: _extraOptions,
            composeMsg: "",
            oftCmd: ""
        });
        
        MessagingFee memory fee = kusdOFT.quoteSend(params, false);
        require(msg.value >= fee.nativeFee, "Insufficient fee");
        
        (MessagingReceipt memory receipt, ) = kusdOFT.send{value: fee.nativeFee}(
            params, 
            fee, 
            payable(msg.sender)
        );
        
        emit SettlementSent(toSettle, receipt.guid);
    }

    /**
     * @notice Quotes the settlement fee.
     */
    function quoteSettle(uint256 amount, bytes calldata _extraOptions) external view returns (uint256 nativeFee, uint256 zroFee) {
        SendParam memory params = SendParam({
            dstEid: BASE_EID,
            to: bytes32(uint256(uint160(baseTreasury))),
            amountLD: amount,
            minAmountLD: (amount * 9900) / 10000,
            extraOptions: _extraOptions,
            composeMsg: "",
            oftCmd: ""
        });
        MessagingFee memory fee = kusdOFT.quoteSend(params, false);
        return (fee.nativeFee, fee.lzTokenFee);
    }
    
    function setMinSettleAmount(uint256 _min) external onlyRole(DEFAULT_ADMIN_ROLE) {
        minSettleAmount = _min;
    }

    function setBaseTreasury(address _baseTreasury) external onlyRole(DEFAULT_ADMIN_ROLE) {
        emit BaseTreasuryUpdated(baseTreasury, _baseTreasury);
        baseTreasury = _baseTreasury;
    }

    /**
     * @notice Emergency withdraw of tokens.
     */
    function recoverTokens(address token) external onlyRole(DEFAULT_ADMIN_ROLE) {
        uint256 balance = IERC20(token).balanceOf(address(this));
        SafeERC20.safeTransfer(IERC20(token), msg.sender, balance);
    }
}
