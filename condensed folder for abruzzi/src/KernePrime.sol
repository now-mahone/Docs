// Created: 2026-01-06
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "./KerneVault.sol";

/**
 * @title KernePrime
 * @author Kerne Protocol
 * @notice Institutional Prime Brokerage module for advanced trading and hedging.
 */
contract KernePrime is Ownable, ReentrancyGuard {
    struct PrimeAccount {
        bool active;
        uint256 balance;
        uint256 debt; // kUSD debt for leveraged trading
        uint256 collateral; // Additional collateral if any
        uint256 creditLine; // Maximum kUSD debt allowed
        uint256 lastTradeTimestamp;
        address vault;
    }

    mapping(address => PrimeAccount) public primeAccounts;
    uint256 public liquidationThresholdBps = 11000; // 110%
    uint256 public liquidationPenaltyBps = 500; // 5%
    uint256 public totalPrimeAUM;
    uint256 public primeFeeBps = 50; // 0.5% annual SaaS-like fee

    event PrimeAccountCreated(address indexed partner, address vault);
    event FundsAllocated(address indexed partner, uint256 amount);
    event FundsDeallocated(address indexed partner, uint256 amount);

    constructor() Ownable(msg.sender) { }

    /**
     * @notice Initializes a Prime Brokerage account for a partner.
     */
    function createPrimeAccount(address _partner, address _vault, uint256 _creditLine) external onlyOwner {
        require(!primeAccounts[_partner].active, "Account already exists");
        primeAccounts[_partner] = PrimeAccount({
            active: true,
            balance: 0,
            debt: 0,
            collateral: 0,
            creditLine: _creditLine,
            lastTradeTimestamp: block.timestamp,
            vault: _vault
        });
        emit PrimeAccountCreated(_partner, _vault);
    }

    /**
     * @notice Updates the credit line for a Prime account.
     */
    function setCreditLine(address _partner, uint256 _newCreditLine) external onlyOwner {
        require(primeAccounts[_partner].active, "Account not active");
        primeAccounts[_partner].creditLine = _newCreditLine;
    }

    /**
     * @notice Borrows kUSD against the Prime account's credit line.
     */
    function borrow(uint256 _amount) external nonReentrant {
        PrimeAccount storage account = primeAccounts[msg.sender];
        require(account.active, "Not a Prime partner");
        require(account.debt + _amount <= account.creditLine, "Credit line exceeded");
        
        account.debt += _amount;
        account.lastTradeTimestamp = block.timestamp;
        
        require(getHealthFactor(msg.sender) >= 1e18, "Unsafe health factor after borrow");
        
        // In production, this would mint kUSD or transfer from a pool
        // For now, we assume the Prime contract holds kUSD or has minting rights
    }

    /**
     * @notice Repays kUSD debt.
     */
    function repay(uint256 _amount) external nonReentrant {
        PrimeAccount storage account = primeAccounts[msg.sender];
        require(account.active, "Not a Prime partner");
        if (_amount > account.debt) _amount = account.debt;
        
        account.debt -= _amount;
        // Transfer kUSD from partner to Prime contract
    }

    /**
     * @notice Allocates funds from a KerneVault to the Prime Brokerage sub-account.
     */
    function allocateToPrime(
        uint256 _amount
    ) external {
        PrimeAccount storage account = primeAccounts[msg.sender];
        require(account.active, "Not a Prime partner");

        // Ensure the vault has enough liquid buffer before allocating
        KerneVault vault = KerneVault(account.vault);
        require(IERC20(vault.asset()).balanceOf(address(vault)) >= _amount, "Insufficient vault buffer");

        vault.transferToPrime(address(this), _amount);
        account.balance += _amount;
        totalPrimeAUM += _amount;

        emit FundsAllocated(msg.sender, _amount);
    }

    /**
     * @notice Deallocates funds from Prime back to the vault.
     */
    function deallocateFromPrime(
        uint256 _amount
    ) external {
        PrimeAccount storage account = primeAccounts[msg.sender];
        require(account.active, "Not a Prime partner");
        require(account.balance >= _amount, "Insufficient balance");
        require(getHealthFactor(msg.sender) >= 1e18, "Unsafe health factor");

        account.balance -= _amount;
        totalPrimeAUM -= _amount;

        // Approve vault to pull funds back
        KerneVault vault = KerneVault(account.vault);
        IERC20(vault.asset()).approve(address(vault), _amount);
        vault.returnFromPrime(_amount);

        emit FundsDeallocated(msg.sender, _amount);
    }

    /**
     * @notice Returns the health factor of a Prime account.
     * @dev 1e18 = 1.0 (100% collateralization)
     */
    function getHealthFactor(
        address _partner
    ) public view returns (uint256) {
        PrimeAccount storage account = primeAccounts[_partner];
        if (account.debt == 0) return 100e18; // Effectively infinite

        // Simplified: balance is collateral, debt is kUSD borrowed
        // In a real scenario, we'd use an oracle for the asset price
        uint256 collateralValue = account.balance;
        uint256 thresholdValue = (collateralValue * 10000) / liquidationThresholdBps;

        return (thresholdValue * 1e18) / account.debt;
    }

    /**
     * @notice Liquidates an underwater Prime account.
     * @param _partner The partner to liquidate.
     */
    function liquidate(
        address _partner
    ) external nonReentrant {
        require(getHealthFactor(_partner) < 1e18, "Account is healthy");

        PrimeAccount storage account = primeAccounts[_partner];
        uint256 debtToCover = account.debt;
        uint256 collateralToSeize = (debtToCover * (10000 + liquidationPenaltyBps)) / 10000;

        if (collateralToSeize > account.balance) {
            collateralToSeize = account.balance;
        }

        account.balance -= collateralToSeize;
        account.debt = 0; // Debt cleared
        totalPrimeAUM -= collateralToSeize;

        // Transfer seized collateral to liquidator (or protocol treasury)
        KerneVault vault = KerneVault(account.vault);
        IERC20(vault.asset()).transfer(msg.sender, collateralToSeize);
    }

    /**
     * @notice Updates the Prime fee.
     */
    function setPrimeFee(
        uint256 _newFeeBps
    ) external onlyOwner {
        require(_newFeeBps <= 500, "Fee too high");
        primeFeeBps = _newFeeBps;
    }
}
