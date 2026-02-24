// Created: 2026-01-30
// Rebuilt from scratch: 2026-02-23 - Clean deposit/withdrawal logic
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useAccount, useWriteContract, useWaitForTransactionReceipt, useBalance, useChainId, useReadContract, useSwitchChain } from 'wagmi';
import { parseEther, formatEther, erc20Abi } from 'viem';
import { VAULT_ADDRESS, WETH_ADDRESS } from '@/config';
import KerneVaultABI from '@/abis/KerneVault.json';
import { Vault } from 'lucide-react';

export function VaultInteraction() {
  const { isConnected, address } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw'>('deposit');
  const [amount, setAmount] = useState('');
  const [ethPrice, setEthPrice] = useState(3150);

  // Constants for Base
  const REQUIRED_CHAIN_ID = 8453;
  const VAULT = VAULT_ADDRESS; // 0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC
  const TOKEN = WETH_ADDRESS;

  const isCorrectNetwork = isConnected && chainId === REQUIRED_CHAIN_ID;

  // Contract interactions
  const { writeContract, data: txHash, isPending, error: writeError, reset: resetWrite } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({ 
    hash: txHash,
    chainId: REQUIRED_CHAIN_ID 
  });

  // Token balance (WETH)
  const { data: tokenBalance, refetch: refetchTokenBalance } = useBalance({
    address: address,
    token: TOKEN,
    chainId: REQUIRED_CHAIN_ID,
  });

  // Vault share balance (kLP)
  const { data: vaultShareBalance, refetch: refetchVaultBalance } = useReadContract({
    address: VAULT,
    abi: KerneVaultABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    chainId: REQUIRED_CHAIN_ID,
  });

  // Convert shares to assets for display
  const { data: userAssets, refetch: refetchUserAssets } = useReadContract({
    address: VAULT,
    abi: KerneVaultABI.abi,
    functionName: 'convertToAssets',
    args: vaultShareBalance ? [vaultShareBalance] : undefined,
    chainId: REQUIRED_CHAIN_ID,
  });

  // Token allowance
  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: TOKEN,
    abi: erc20Abi,
    functionName: 'allowance',
    args: address && VAULT ? [address, VAULT] : undefined,
    chainId: REQUIRED_CHAIN_ID,
  });

  // Check if approval is needed
  const needsApproval = useMemo(() => {
    if (activeTab !== 'deposit' || !amount || allowance === undefined) return false;
    try {
      const amountWei = parseEther(amount);
      return allowance < amountWei;
    } catch {
      return false;
    }
  }, [activeTab, amount, allowance]);

  // USD value
  const usdValue = useMemo(() => {
    if (!amount) return '0.00';
    try {
      const value = parseFloat(amount) * ethPrice;
      return value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    } catch {
      return '0.00';
    }
  }, [amount, ethPrice]);

  // Fetch ETH price
  useEffect(() => {
    const fetchPrice = async () => {
      try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT');
        const data = await res.json();
        if (data.price) setEthPrice(parseFloat(data.price));
      } catch (e) {
        console.error('Failed to fetch ETH price:', e);
      }
    };
    fetchPrice();
    const interval = setInterval(fetchPrice, 60000);
    return () => clearInterval(interval);
  }, []);

  // Refetch balances on confirmation
  useEffect(() => {
    if (isConfirmed) {
      const timer = setTimeout(() => {
        refetchTokenBalance();
        refetchVaultBalance();
        refetchUserAssets();
        refetchAllowance();
        setAmount('');
        resetWrite();
      }, 2000);
      return () => clearTimeout(timer);
    }
  }, [isConfirmed, refetchTokenBalance, refetchVaultBalance, refetchUserAssets, refetchAllowance, resetWrite]);

  // Handlers
  const handleButtonClick = () => {
    if (!isConnected) return;
    if (!isCorrectNetwork) {
      switchChain({ chainId: REQUIRED_CHAIN_ID });
      return;
    }
    
    if (!amount || parseFloat(amount) <= 0) return;
    const amountWei = parseEther(amount);

    if (activeTab === 'deposit') {
      if (needsApproval) {
        writeContract({
          address: TOKEN,
          abi: erc20Abi,
          functionName: 'approve',
          args: [VAULT, amountWei],
          chainId: REQUIRED_CHAIN_ID,
        });
      } else {
        writeContract({
          address: VAULT,
          abi: KerneVaultABI.abi,
          functionName: 'deposit',
          args: [amountWei, address],
          chainId: REQUIRED_CHAIN_ID,
        });
      }
    } else {
      // Withdrawal logic: use requestWithdrawal for the hardened vault
      writeContract({
        address: VAULT,
        abi: KerneVaultABI.abi,
        functionName: 'requestWithdrawal',
        args: [amountWei],
        chainId: REQUIRED_CHAIN_ID,
      });
    }
  };

  const displayBalance = useMemo(() => {
    if (activeTab === 'deposit') {
      return tokenBalance ? parseFloat(formatEther(tokenBalance.value)).toFixed(4) : '0.00';
    }
    return userAssets && typeof userAssets === 'bigint' ? parseFloat(formatEther(userAssets)).toFixed(4) : '0.00';
  }, [activeTab, tokenBalance, userAssets]);

  const getButtonText = () => {
    if (!isConnected) return 'Connect wallet to interact';
    if (!isCorrectNetwork) return 'Switch to Base';
    if (isPending) return 'Confirming in Wallet...';
    if (isConfirming) return 'Processing Transaction...';
    if (activeTab === 'deposit') {
      return needsApproval ? 'Approve WETH' : 'Confirm Deposit';
    }
    return 'Request Withdrawal';
  };

  return (
    <div className="p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex flex-col flex-1">
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide">Vault Interaction</span>
          <div className="flex items-center gap-4 text-xl font-heading font-medium text-[#ffffff] mt-4">
            <img src="/Base-Square-Blue.svg" alt="Base" className="w-5 h-5 object-contain" />
            Base Mainnet
          </div>
        </div>
        <Vault size={16} className="text-[#aab9be] flex-shrink-0" />
      </div>

      {/* Tab Buttons */}
      <div className="grid grid-cols-2 gap-0 mb-8 border border-[#444a4f] rounded-sm p-0 h-12 overflow-hidden">
        <button
          onClick={() => setActiveTab('deposit')}
          className={`font-bold text-s h-full border-r border-[#444a4f] transition-colors ${
            activeTab === 'deposit' ? 'bg-[#ffffff] text-[#000000]' : 'bg-[#22252a] text-[#d4dce1]'
          }`}
        >
          Deposit
        </button>
        <button
          onClick={() => setActiveTab('withdraw')}
          className={`font-bold text-s h-full transition-colors ${
            activeTab === 'withdraw' ? 'bg-[#ffffff] text-[#000000]' : 'bg-[#22252a] text-[#d4dce1]'
          }`}
        >
          Withdraw
        </button>
      </div>

      {/* Content Area */}
      <div className="h-[340px] flex flex-col">
        <div className="h-[130px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <label className="text-s font-medium text-[#aab9be] tracking-tight">
              {activeTab === 'deposit' ? 'Amount (WETH)' : 'Amount (Kerne-V1)'}
            </label>
            <span className="text-s font-medium text-[#aab9be] tracking-tight">
              Balance: {displayBalance}
            </span>
          </div>
          <div className="relative h-[52px] mb-3">
            <input 
              type="number"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full h-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            />
            <button 
              onClick={() => {
                if (activeTab === 'deposit' && tokenBalance) setAmount(formatEther(tokenBalance.value));
                else if (activeTab === 'withdraw' && userAssets) setAmount(formatEther(userAssets as bigint));
              }}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#37d097] hover:text-[#37d097]/80 transition-colors"
            >
              MAX
            </button>
          </div>
          <div className="flex justify-start">
            <span className="text-s font-medium text-[#aab9be] tracking-tight">≈ ${usdValue}</span>
          </div>
        </div>

        <div className="flex-1" />

        <div className="h-[80px] flex flex-col">
          <div className="h-12 mb-2">
            <button 
              onClick={handleButtonClick}
              disabled={isConnected && isCorrectNetwork && (isPending || isConfirming || !amount || parseFloat(amount) <= 0)}
              className={`w-full h-full font-bold text-s rounded-sm flex items-center justify-center transition-all ${
                !isConnected || !isCorrectNetwork || (amount && parseFloat(amount) > 0 && !isPending && !isConfirming)
                  ? activeTab === 'deposit' && needsApproval && isCorrectNetwork ? 'bg-[#37d097] text-[#ffffff]' : 'bg-[#ffffff] text-[#000000]'
                  : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50'
              }`}
            >
              {getButtonText()}
            </button>
          </div>
          <div className="h-6 flex items-center justify-center">
            {isConfirmed && <p className="text-xs text-[#37d097] font-bold">Transaction Successful</p>}
            {writeError && <p className="text-xs text-red-500 font-bold">Transaction Failed</p>}
          </div>
        </div>
      </div>

      <div className="mt-8 pt-6 border-t border-[#444a4f]/30">
        <p className="text-xs text-[#444a4f] font-medium leading-relaxed">
          Risk Disclosure: Interacting with delta neutral vaults involves smart contract, execution, and counterparty risk. High frequency hedging may result in principal drawdown during extreme market volatility.
        </p>
      </div>
    </div>
  );
}