// Created: 2026-01-30
// Rebuilt from scratch: 2026-02-23 - Clean deposit/withdrawal logic
'use client';

import React, { useState, useEffect, useMemo } from 'react';
import { useAccount, useWriteContract, useWaitForTransactionReceipt, useBalance, useChainId, useReadContract, useSwitchChain } from 'wagmi';
import { parseEther, formatEther, erc20Abi, maxUint256 } from 'viem';
import { VAULT_ADDRESS, ARB_VAULT_ADDRESS, OP_VAULT_ADDRESS, WETH_ADDRESS, ARB_WSTETH_ADDRESS } from '@/config';
import KerneVaultABI from '@/abis/KerneVault.json';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Vault, ChevronDown } from 'lucide-react';

type Chain = 'Base' | 'Arbitrum' | 'OP Mainnet';
type Tab = 'deposit' | 'withdraw';

const CHAIN_IDS: Record<Chain, number> = {
  'Base': 8453,
  'Arbitrum': 42161,
  'OP Mainnet': 10,
};

const VAULT_ADDRESSES: Record<Chain, `0x${string}`> = {
  'Base': VAULT_ADDRESS,
  'Arbitrum': ARB_VAULT_ADDRESS,
  'OP Mainnet': OP_VAULT_ADDRESS,
};

const TOKEN_ADDRESSES: Record<Chain, `0x${string}` | undefined> = {
  'Base': WETH_ADDRESS,
  'Arbitrum': ARB_WSTETH_ADDRESS,
  'OP Mainnet': undefined,
};

const CHAIN_LOGOS: Record<Chain, string> = {
  'Base': '/Base-Square-Blue.svg',
  'Arbitrum': '/Arbitrum-Mark.svg',
  'OP Mainnet': '/OP-Mainnet.svg',
};

export function VaultInteraction() {
  const { isConnected, address } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  
  const [selectedChain, setSelectedChain] = useState<Chain>('Base');
  const [activeTab, setActiveTab] = useState<Tab>('deposit');
  const [amount, setAmount] = useState('');
  const [ethPrice, setEthPrice] = useState(3150);

  // Derived values
  const requiredChainId = CHAIN_IDS[selectedChain];
  const vaultAddress = VAULT_ADDRESSES[selectedChain];
  const tokenAddress = TOKEN_ADDRESSES[selectedChain];
  const isCorrectNetwork = isConnected && chainId === requiredChainId;

  // Contract interactions
  const { writeContract, data: txHash, isPending, isError: writeError, reset: resetWrite } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({ 
    hash: txHash,
    chainId: requiredChainId 
  });

  // Token balance
  const { data: tokenBalance, refetch: refetchTokenBalance } = useBalance({
    address: address,
    token: tokenAddress,
    chainId: requiredChainId,
  });

  // Vault share balance
  const { data: vaultShareBalance, refetch: refetchVaultBalance } = useReadContract({
    address: vaultAddress,
    abi: KerneVaultABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    chainId: requiredChainId,
  });

  // Convert shares to assets
  const { data: userAssets, refetch: refetchUserAssets } = useReadContract({
    address: vaultAddress,
    abi: KerneVaultABI.abi,
    functionName: 'convertToAssets',
    args: vaultShareBalance ? [vaultShareBalance] : undefined,
    chainId: requiredChainId,
  });

  // Token allowance
  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: tokenAddress,
    abi: erc20Abi,
    functionName: 'allowance',
    args: address && vaultAddress ? [address, vaultAddress] : undefined,
    chainId: requiredChainId,
  });

  // Check if approval is needed
  const needsApproval = useMemo(() => {
    if (activeTab !== 'deposit' || !amount || !allowance || !tokenAddress) return false;
    try {
      const amountWei = parseEther(amount);
      return allowance < amountWei;
    } catch {
      return false;
    }
  }, [activeTab, amount, allowance, tokenAddress]);

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
  const handleSwitchNetwork = async () => {
    try {
      await switchChain({ chainId: requiredChainId });
    } catch (error) {
      console.error('Failed to switch network:', error);
    }
  };

  const handleApprove = async () => {
    if (!isCorrectNetwork || !amount || !tokenAddress || !vaultAddress) return;
    
    try {
      const amountWei = parseEther(amount);
      writeContract({
        address: tokenAddress,
        abi: erc20Abi,
        functionName: 'approve',
        args: [vaultAddress, amountWei],
        chainId: requiredChainId,
      });
    } catch (error) {
      console.error('Approval error:', error);
    }
  };

  const handleDeposit = async () => {
    if (!isCorrectNetwork || !amount || !address || !vaultAddress) return;
    
    try {
      const amountWei = parseEther(amount);
      writeContract({
        address: vaultAddress,
        abi: KerneVaultABI.abi,
        functionName: 'deposit',
        args: [amountWei, address],
        chainId: requiredChainId,
      });
    } catch (error) {
      console.error('Deposit error:', error);
    }
  };

  const handleWithdraw = async () => {
    if (!isCorrectNetwork || !amount || !address || !vaultAddress || !vaultShareBalance) return;
    
    try {
      const amountWei = parseEther(amount);
      
      // Always use redeem with shares for simplicity and gas efficiency
      // Convert the asset amount user wants to withdraw into shares
      if (userAssets && typeof userAssets === 'bigint' && typeof vaultShareBalance === 'bigint') {
        // Calculate shares needed for desired asset amount
        // shares = (amountWei * totalShares) / totalAssets
        const sharesToRedeem = userAssets > 0n 
          ? (amountWei * vaultShareBalance) / userAssets 
          : 0n;
        
        console.log('Withdrawal debug:', {
          amountRequested: formatEther(amountWei),
          userAssets: formatEther(userAssets),
          vaultShareBalance: formatEther(vaultShareBalance),
          sharesToRedeem: formatEther(sharesToRedeem)
        });
        
        if (sharesToRedeem > 0n) {
          writeContract({
            address: vaultAddress,
            abi: KerneVaultABI.abi,
            functionName: 'redeem',
            args: [sharesToRedeem, address, address],
            chainId: requiredChainId,
          });
        } else {
          console.error('Cannot calculate shares to redeem');
        }
      } else {
        console.error('Missing required data for withdrawal:', { userAssets, vaultShareBalance });
      }
    } catch (error) {
      console.error('Withdrawal error:', error);
    }
  };

  const handleMaxClick = () => {
    if (activeTab === 'deposit' && tokenBalance) {
      setAmount(formatEther(tokenBalance.value));
    } else if (activeTab === 'withdraw' && userAssets && typeof userAssets === 'bigint') {
      setAmount(formatEther(userAssets));
    }
  };

  const getButtonText = () => {
    if (!isConnected) return 'Connect wallet to interact';
    if (!isCorrectNetwork) return `Switch to ${selectedChain}`;
    if (isPending) return 'Confirming in Wallet...';
    if (isConfirming) return 'Processing Transaction...';
    if (activeTab === 'deposit') {
      if (needsApproval) return 'Approve Token';
      return 'Confirm Deposit';
    }
    return 'Confirm Withdrawal';
  };

  const isButtonDisabled = () => {
    if (!isConnected) return true;
    if (!isCorrectNetwork) return false; // Allow network switch
    if (isPending || isConfirming) return true;
    if (!amount || parseFloat(amount) <= 0) return true;
    return false;
  };

  const handleButtonClick = () => {
    if (!isConnected) return;
    if (!isCorrectNetwork) {
      handleSwitchNetwork();
      return;
    }
    if (activeTab === 'deposit') {
      if (needsApproval) {
        handleApprove();
      } else {
        handleDeposit();
      }
    } else {
      handleWithdraw();
    }
  };

  const displayBalance = useMemo(() => {
    if (activeTab === 'deposit') {
      return tokenBalance ? parseFloat(formatEther(tokenBalance.value)).toFixed(4) : '0.00';
    }
    return userAssets && typeof userAssets === 'bigint' ? parseFloat(formatEther(userAssets)).toFixed(4) : '0.00';
  }, [activeTab, tokenBalance, userAssets]);

  const tokenSymbol = selectedChain === 'Arbitrum' ? 'wstETH' : 'WETH';

  return (
    <div className="p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm h-[600px] flex flex-col">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div className="flex flex-col flex-1">
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide">Vault Interaction</span>
          <DropdownMenu modal={false}>
            <DropdownMenuTrigger className="flex items-center gap-4 text-xl font-heading font-medium text-[#ffffff] mt-4 outline-none text-left">
              <img src={CHAIN_LOGOS[selectedChain]} alt={selectedChain} className="w-5 h-5 object-contain" />
              {selectedChain}
              <ChevronDown size={20} className="text-[#aab9be] ml-1" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="bg-[#000000] border-[#444a4f] text-[#ffffff] min-w-[260px] p-4 shadow-2xl space-y-1">
              {(Object.keys(CHAIN_LOGOS) as Chain[]).map((chain) => (
                <DropdownMenuItem 
                  key={chain}
                  onClick={() => setSelectedChain(chain)}
                  className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
                >
                  <img src={CHAIN_LOGOS[chain]} alt={chain} className="w-5 h-5 object-contain" />
                  {chain}
                </DropdownMenuItem>
              ))}
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

      {/* Content Area */}
      <div className="h-[340px] flex flex-col">
        {/* Input Section */}
        <div className="h-[130px] flex flex-col">
          <div className="flex justify-between items-center mb-3">
            <label className="text-s font-medium text-[#aab9be] tracking-tight">
              {activeTab === 'deposit' ? `Amount (${tokenSymbol})` : 'Amount (Kerne-V1)'}
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
              onClick={handleMaxClick}
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

        {/* Button Section */}
        <div className="h-[80px] flex flex-col">
          <div className="h-12 mb-2">
            <button 
              onClick={handleButtonClick}
              disabled={isButtonDisabled()}
              className={`w-full h-full font-bold text-s rounded-sm flex items-center justify-center transition-all ${
                !isButtonDisabled() && isCorrectNetwork
                  ? needsApproval && activeTab === 'deposit'
                    ? 'bg-[#37d097] text-[#ffffff] hover:bg-[#37d097]/80'
                    : 'bg-[#ffffff] text-[#000000] hover:bg-[#37d097] hover:text-[#ffffff]'
                  : !isConnected || (isCorrectNetwork && (isPending || isConfirming || !amount))
                  ? 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-not-allowed opacity-50'
                  : 'bg-[#ffffff] text-[#000000] hover:bg-[#37d097] hover:text-[#ffffff]'
              }`}
            >
              {(isPending || isConfirming) ? (
                <div className="flex items-center gap-2">
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-current"></div>
                  {getButtonText()}
                </div>
              ) : (
                getButtonText()
              )}
            </button>
          </div>
          <div className="h-6 flex items-center justify-center">
            {isConfirmed && (
              <p className="text-xs text-[#37d097] font-bold text-center leading-6">
                Transaction Successful
              </p>
            )}
            {writeError && (
              <p className="text-xs text-red-500 font-bold text-center leading-6">
                Transaction failed
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