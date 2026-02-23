// Created: 2026-01-30
// Rebuilt: 2026-02-13 - Fixed layout with zero shift
'use client';

import React, { useState, useEffect } from 'react';
import { useAccount, useWriteContract, useWaitForTransactionReceipt, useBalance, useChainId, useReadContract, useSwitchChain, usePublicClient } from 'wagmi';
import { parseEther, formatEther, erc20Abi } from 'viem';
import { VAULT_ADDRESS, ARB_VAULT_ADDRESS, OP_VAULT_ADDRESS, WETH_ADDRESS, ARB_WSTETH_ADDRESS } from '@/config';
import KerneVaultABI from '@/abis/KerneVault.json';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Vault, ChevronDown } from 'lucide-react';

export function VaultInteraction() {
  const { isConnected, address } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  const publicClient = usePublicClient();
  const [amount, setAmount] = useState('');
  const [selectedChain, setSelectedChain] = useState('Base');
  const [ethPrice, setEthPrice] = useState(3150);
  const [needsApproval, setNeedsApproval] = useState(false);
  const [activeTab, setActiveTab] = useState<'deposit' | 'withdraw'>('deposit');

  // Chain ID mapping
  const requiredChainId = selectedChain === 'Base' 
    ? 8453 
    : selectedChain === 'Arbitrum' 
      ? 42161 
      : 10;

  const isCorrectNetwork = isConnected && chainId !== undefined && chainId === requiredChainId;

  useEffect(() => {
    console.log('Network Debug:', {
      isConnected,
      chainId,
      requiredChainId,
      isCorrectNetwork,
      selectedChain
    });
  }, [isConnected, chainId, requiredChainId, isCorrectNetwork, selectedChain]);

  const tokenAddress = selectedChain === 'Base' 
    ? WETH_ADDRESS 
    : selectedChain === 'Arbitrum' 
      ? ARB_WSTETH_ADDRESS 
      : undefined;

  const { data: balanceData } = useBalance({
    address: address,
    token: tokenAddress,
    chainId: selectedChain === 'Base' ? 8453 : selectedChain === 'Arbitrum' ? 42161 : 10,
  });

  const targetVault = selectedChain === 'Base' 
    ? VAULT_ADDRESS 
    : selectedChain === 'Arbitrum' 
      ? ARB_VAULT_ADDRESS 
      : OP_VAULT_ADDRESS;

  const { 
    writeContract, 
    data: hash, 
    isPending,
    error: writeError,
    reset: resetWrite
  } = useWriteContract();

  const { isLoading: isConfirming, isSuccess: isConfirmed } = 
    useWaitForTransactionReceipt({ 
      hash,
      chainId: requiredChainId 
    });

  const { data: vaultShareBalance, refetch: refetchVaultBalance } = useReadContract({
    address: targetVault,
    abi: KerneVaultABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    chainId: requiredChainId,
    query: {
      enabled: !!address && !!targetVault && targetVault !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: userAssets, refetch: refetchUserAssets } = useReadContract({
    address: targetVault,
    abi: KerneVaultABI.abi,
    functionName: 'convertToAssets',
    args: vaultShareBalance ? [vaultShareBalance] : undefined,
    chainId: requiredChainId,
    query: {
      enabled: !!vaultShareBalance && !!targetVault && targetVault !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: tokenAddress,
    abi: erc20Abi,
    functionName: 'allowance',
    args: address && targetVault ? [address, targetVault] : undefined,
    chainId: requiredChainId,
    query: {
      enabled: !!address && !!tokenAddress && !!targetVault,
      refetchInterval: isConfirming ? 1000 : false,
    },
  });

  useEffect(() => {
    if (amount && allowance !== undefined && tokenAddress && targetVault) {
      try {
        const amountWei = parseEther(amount);
        setNeedsApproval(allowance < amountWei);
      } catch (e) {
        setNeedsApproval(false);
      }
    } else {
      setNeedsApproval(false);
    }
  }, [amount, allowance, tokenAddress, targetVault]);

  useEffect(() => {
    if (isConfirmed) {
      console.log('Transaction confirmed, refetching data...');

      const refetchInterval = setInterval(() => {
        refetchAllowance();
        refetchVaultBalance();
        refetchUserAssets();
      }, 500);
      
      const timer = setTimeout(() => {
        clearInterval(refetchInterval);
        resetWrite();
        refetchAllowance();
        refetchVaultBalance();
        refetchUserAssets();
        console.log('Write state reset');
      }, 2000);
      
      return () => {
        clearInterval(refetchInterval);
        clearTimeout(timer);
      };
    }
  }, [isConfirmed, resetWrite, refetchAllowance, refetchVaultBalance, refetchUserAssets]);

  useEffect(() => {
    const fetchPrice = async () => {
      try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT');
        const data = await res.json();
        if (data.price) setEthPrice(parseFloat(data.price));
      } catch (e) {
        console.error("Failed to fetch ETH price in VaultInteraction", e);
      }
    };
    fetchPrice();
  }, []);

  const usdValue = amount ? (parseFloat(amount) * ethPrice).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';

  const handleSwitchNetwork = async () => {
    try {
      await switchChain({ chainId: requiredChainId });
    } catch (error) {
      console.error('Failed to switch network:', error);
    }
  };

  const handleApprove = async () => {
    if (!isCorrectNetwork) {
      console.error('Wrong network! Current:', chainId, 'Required:', requiredChainId);
      return;
    }
    
    if (!amount || isNaN(parseFloat(amount)) || !address || !tokenAddress || !targetVault) {
      console.error('Missing required data for approval');
      return;
    }
    
    try {
      const amountWei = parseEther(amount);
      
      console.log('Approving:', {
        token: tokenAddress,
        spender: targetVault,
        amount: formatEther(amountWei),
        chainId: requiredChainId
      });
      
      writeContract({
        address: tokenAddress,
        abi: erc20Abi,
        functionName: 'approve',
        args: [targetVault, amountWei],
        chainId: requiredChainId,
      });
    } catch (error) {
      console.error('Approval error:', error);
    }
  };

  const handleDeposit = async () => {
    if (!isCorrectNetwork) {
      console.error('Wrong network! Current:', chainId, 'Required:', requiredChainId);
      return;
    }
    
    if (!amount || isNaN(parseFloat(amount)) || !address || !targetVault) {
      console.error('Missing required data for deposit');
      return;
    }

    if (!targetVault || targetVault === '0x0000000000000000000000000000000000000000') {
      console.error("Vault address not configured for", selectedChain);
      return;
    }

    try {
      const amountWei = parseEther(amount);
      
      console.log('Depositing:', {
        vault: targetVault,
        amount: formatEther(amountWei),
        receiver: address,
        chainId: requiredChainId
      });
      
      // Add explicit gas limit for L2s to prevent MetaMask over-estimation
      const gasLimit = selectedChain === 'Base' ? 250000n : undefined;
      
      writeContract({
        address: targetVault,
        abi: KerneVaultABI.abi,
        functionName: 'deposit',
        args: [amountWei, address],
        chainId: requiredChainId,
        gas: gasLimit,
      });
    } catch (error) {
      console.error('Deposit error:', error);
    }
  };

  const { data: ethBalance } = useBalance({
    address: address,
    chainId: requiredChainId,
  });

  const handleWithdraw = async () => {
    if (!isCorrectNetwork) {
      console.error('Wrong network! Current:', chainId, 'Required:', requiredChainId);
      return;
    }
    
    if (!amount || isNaN(parseFloat(amount)) || !address || !targetVault) {
      console.error('Missing required data for withdrawal');
      return;
    }
    
    try {
      const amountWei = parseEther(amount);
      const isMax = typeof userAssets === 'bigint' && amountWei >= userAssets;

      console.log('Withdrawing:', {
        vault: targetVault,
        amount: formatEther(amountWei),
        isMax,
        receiver: address,
        chainId: requiredChainId
      });

      // Add explicit gas limit for L2s to prevent MetaMask over-estimation
      const gasLimit = selectedChain === 'Base' ? 300000n : undefined;

      if (isMax && typeof vaultShareBalance === 'bigint') {
        writeContract({
          address: targetVault,
          abi: KerneVaultABI.abi,
          functionName: 'redeem',
          args: [vaultShareBalance, address, address],
          chainId: requiredChainId,
          gas: gasLimit,
        });
      } else {
        writeContract({
          address: targetVault,
          abi: KerneVaultABI.abi,
          functionName: 'withdraw',
          args: [amountWei, address, address],
          chainId: requiredChainId,
          gas: gasLimit,
        });
      }
    } catch (error) {
      console.error('Withdrawal error:', error);
    }
  };

  const chainLogos: { [key: string]: string } = {
    'Base': '/Base-Square-Blue.svg',
    'Arbitrum': '/Arbitrum-Mark.svg',
    'OP Mainnet': '/OP-Mainnet.svg'
  };

  return (
    <div className="p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex flex-col flex-1">
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide">Vault Interaction</span>
          <DropdownMenu modal={false}>
            <DropdownMenuTrigger className="flex items-center gap-4 text-xl font-heading font-medium text-[#ffffff] mt-4 outline-none text-left">
              <img src={chainLogos[selectedChain]} alt={selectedChain} className="w-5 h-5 object-contain" />
              {selectedChain}
              <ChevronDown size={20} className="text-[#aab9be] ml-1" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="bg-[#000000] border-[#444a4f] text-[#ffffff] min-w-[260px] p-4 shadow-2xl space-y-1">
              <DropdownMenuItem 
                onClick={() => setSelectedChain('Base')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/Base-Square-Blue.svg" alt="Base" className="w-5 h-5 object-contain" />
                Base
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => setSelectedChain('Arbitrum')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/Arbitrum-Mark.svg" alt="Arbitrum" className="w-5 h-5 object-contain" />
                Arbitrum
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => setSelectedChain('OP Mainnet')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/OP-Mainnet.svg" alt="OP Mainnet" className="w-5 h-5 object-contain" />
                OP Mainnet
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <Vault size={16} className="text-[#aab9be] flex-shrink-0" />
      </div>

      {/* Tab Buttons */}
      <div className="grid grid-cols-2 gap-0 mb-8 border border-[#444a4f] rounded-sm p-0 h-12 overflow-hidden">
        <button
          onClick={() => setActiveTab('deposit')}
          className={`font-bold text-s h-full border-r border-[#444a4f] transition-colors ${
            activeTab === 'deposit'
              ? 'bg-[#ffffff] text-[#000000]'
              : 'bg-[#22252a] text-[#d4dce1]'
          }`}
        >
          Deposit
        </button>
        <button
          onClick={() => setActiveTab('withdraw')}
          className={`font-bold text-s h-full transition-colors ${
            activeTab === 'withdraw'
              ? 'bg-[#ffffff] text-[#000000]'
              : 'bg-[#22252a] text-[#d4dce1]'
          }`}
        >
          Withdraw
        </button>
      </div>

      {/* Content Area - Fixed Height 340px */}
      <div className="h-[340px] flex flex-col">
        {/* Input Section - Fixed 130px */}
        <div className="h-[130px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <label className="text-s font-medium text-[#aab9be] tracking-tight">
              {activeTab === 'deposit' 
                ? `Amount (${selectedChain === 'Arbitrum' ? 'wstETH' : 'WETH'})`
                : 'Amount (Kerne-V1)'
              }
            </label>
            <span className="text-s font-medium text-[#aab9be] tracking-tight">
              Balance: {activeTab === 'deposit'
                ? (balanceData ? parseFloat(formatEther(balanceData.value)).toFixed(4) : '0.00')
                : (userAssets && typeof userAssets === 'bigint' ? parseFloat(formatEther(userAssets)).toFixed(4) : '0.00')
              }
            </span>
          </div>
          <div className="relative h-[52px] mb-3">
            <input 
              type="number"
              value={amount}
              onChange={(e: any) => setAmount(e.target.value)}
              placeholder="0.00"
              className="w-full h-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
            />
            <button 
              onClick={() => {
                if (activeTab === 'deposit' && balanceData) {
                  setAmount(formatEther(balanceData.value));
                } else if (activeTab === 'withdraw' && userAssets && typeof userAssets === 'bigint') {
                  setAmount(formatEther(userAssets));
                }
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

        {/* Spacer */}
        <div className="flex-1" />

        {/* Button Section - Fixed 80px */}
        <div className="h-[80px] flex flex-col">
          <div className="h-12 mb-2">
            {!isConnected ? (
              <button 
                disabled
                className="w-full h-full font-bold text-s rounded-sm flex items-center justify-center bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50"
              >
                Connect wallet to interact
              </button>
            ) : !isCorrectNetwork ? (
              <button 
                onClick={handleSwitchNetwork}
                className="w-full h-full font-bold text-s rounded-sm flex items-center justify-center bg-[#ffffff] text-[#000000] hover:bg-[#37d097] hover:text-[#ffffff] transition-all"
              >
                Switch to {selectedChain}
              </button>
            ) : activeTab === 'deposit' && needsApproval ? (
              <button 
                onClick={handleApprove}
                disabled={isPending || isConfirming || !amount}
                className={`w-full h-full font-bold text-s rounded-sm flex items-center justify-center transition-all ${
                  !isPending && !isConfirming && amount
                    ? 'bg-[#37d097] text-[#ffffff] hover:bg-[#37d097]/80' 
                    : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50'
                }`}
              >
                {isPending || isConfirming ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    {isPending ? 'Confirming in Wallet...' : 'Processing Approval...'}
                  </div>
                ) : 'Approve Token'}
              </button>
            ) : activeTab === 'deposit' ? (
              <button 
                onClick={handleDeposit}
                disabled={isPending || isConfirming || !amount}
                className={`w-full h-full font-bold text-s rounded-sm flex items-center justify-center transition-all ${
                  !isPending && !isConfirming && amount
                    ? 'bg-[#ffffff] text-[#000000] hover:bg-[#37d097] hover:text-[#ffffff]' 
                    : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50'
                }`}
              >
                {isPending || isConfirming ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    {isPending ? 'Confirming in Wallet...' : 'Processing Transaction...'}
                  </div>
                ) : 'Confirm Deposit'}
              </button>
            ) : (
              <button 
                onClick={handleWithdraw}
                disabled={isPending || isConfirming || !amount}
                className={`w-full h-full font-bold text-s rounded-sm flex items-center justify-center transition-all ${
                  !isPending && !isConfirming && amount
                    ? 'bg-[#ffffff] text-[#000000] hover:bg-[#37d097] hover:text-[#ffffff]' 
                    : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50'
                }`}
              >
                {isPending || isConfirming ? (
                  <div className="flex items-center gap-2">
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                    {isPending ? 'Confirming in Wallet...' : 'Processing Transaction...'}
                  </div>
                ) : 'Confirm Withdrawal'}
              </button>
            )}
          </div>
          <div className="h-6 flex items-center justify-center">
            {isConfirmed && (
              <p className="text-xs text-[#37d097] font-bold text-center leading-6">
                Transaction Successful
              </p>
            )}
            {writeError && (
              <p className="text-xs text-red-500 font-bold text-center leading-6">
                {writeError.message.includes('User rejected') ? 'Transaction rejected' : activeTab === 'deposit' && needsApproval ? 'Approval failed' : activeTab === 'deposit' ? 'Deposit failed' : 'Withdrawal failed'}
              </p>
            )}
          </div>
        </div>
      </div>

      {/* Risk Disclosure */}
      <div className="mt-8 pt-6 border-t border-[#444a4f]/30">
        <p className="text-xs text-[#444a4f] font-medium leading-relaxed">
          Risk Disclosure: Interacting with delta neutral vaults involves smart contract, execution, and counterparty risk. High frequency hedging may result in principal drawdown during extreme market volatility.
        </p>
      </div>
    </div>
  );
}