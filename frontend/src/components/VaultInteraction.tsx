// Created: 2026-02-23
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

  const BASE_ID = 8453;
  const VAULT = VAULT_ADDRESS; 
  const WETH = WETH_ADDRESS;

  const isBase = chainId === BASE_ID;

  const { writeContract, data: hash, isPending, reset: resetWrite } = useWriteContract();
  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({ hash });

  const { data: wethBalance, refetch: refetchWeth } = useBalance({
    address,
    token: WETH,
    chainId: BASE_ID,
  });

  const { data: vaultShares, refetch: refetchShares } = useReadContract({
    address: VAULT,
    abi: KerneVaultABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
  });

  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: WETH,
    abi: erc20Abi,
    functionName: 'allowance',
    args: address && VAULT ? [address, VAULT] : undefined,
  });

  useEffect(() => {
    if (isConfirmed) {
      setTimeout(() => {
        refetchWeth();
        refetchShares();
        refetchAllowance();
        setAmount('');
        resetWrite();
      }, 2000);
    }
  }, [isConfirmed]);

  const handleAction = () => {
    if (!isConnected) return;
    if (!isBase) {
      switchChain({ chainId: BASE_ID });
      return;
    }
    if (!amount || isNaN(parseFloat(amount))) return;
    const val = parseEther(amount);

    if (activeTab === 'deposit') {
      const currentAllowance = allowance ? BigInt(allowance.toString()) : 0n;
      if (currentAllowance < val) {
        writeContract({ address: WETH, abi: erc20Abi, functionName: 'approve', args: [VAULT, val] });
      } else {
        writeContract({ address: VAULT, abi: KerneVaultABI.abi, functionName: 'deposit', args: [val, address] });
      }
    } else {
      writeContract({ address: VAULT, abi: KerneVaultABI.abi, functionName: 'requestWithdrawal', args: [val] });
    }
  };

  const buttonText = () => {
    if (!isConnected) return 'Connect Wallet';
    if (!isBase) return 'Switch to Base';
    if (isPending) return 'Confirm in Wallet...';
    if (isConfirming) return 'Processing...';
    if (activeTab === 'deposit') {
      const currentAllowance = allowance ? BigInt(allowance.toString()) : 0n;
      const val = amount ? parseEther(amount) : 0n;
      return currentAllowance < val ? 'Approve WETH' : 'Deposit WETH';
    }
    return 'Request Withdrawal';
  };

  return (
    <div className="p-8 bg-black border border-[#444a4f] rounded-sm h-[600px] flex flex-col text-white">
      <div className="flex justify-between items-center mb-8">
        <div>
          <p className="text-xs font-bold text-gray-400 uppercase">Vault Interaction</p>
          <h2 className="text-xl font-bold mt-2 flex items-center gap-2">
            <img src="/Base-Square-Blue.svg" className="w-5 h-5" alt="" /> Base Mainnet
          </h2>
        </div>
        <Vault className="text-gray-400" />
      </div>

      <div className="flex border border-[#444a4f] rounded-sm mb-8 overflow-hidden h-12">
        <button 
          onClick={() => setActiveTab('deposit')}
          className={`flex-1 font-bold ${activeTab === 'deposit' ? 'bg-white text-black' : 'bg-[#22252a] text-white'}`}
        >
          Deposit
        </button>
        <button 
          onClick={() => setActiveTab('withdraw')}
          className={`flex-1 font-bold ${activeTab === 'withdraw' ? 'bg-white text-black' : 'bg-[#22252a] text-white'}`}
        >
          Withdraw
        </button>
      </div>

      <div className="flex-1">
        <div className="flex justify-between text-sm text-gray-400 mb-2">
          <span>{activeTab === 'deposit' ? 'Amount (WETH)' : 'Amount (Shares)'}</span>
          <span>
            Balance: {activeTab === 'deposit' 
              ? (wethBalance ? parseFloat(wethBalance.formatted).toFixed(4) : '0.00')
              : (vaultShares ? parseFloat(formatEther(vaultShares as bigint)).toFixed(4) : '0.00')}
          </span>
        </div>
        <div className="relative mb-4">
          <input 
            type="number" 
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            className="w-full bg-[#22252a] border border-[#444a4f] p-4 rounded-sm outline-none focus:border-[#37d097]"
            placeholder="0.00"
          />
          <button 
            onClick={() => {
              if (activeTab === 'deposit' && wethBalance) setAmount(wethBalance.formatted);
              else if (activeTab === 'withdraw' && vaultShares) setAmount(formatEther(vaultShares as bigint));
            }}
            className="absolute right-4 top-4 text-[#37d097] font-bold text-sm"
          >
            MAX
          </button>
        </div>
        <p className="text-sm text-gray-400">≈ ${(parseFloat(amount || '0') * ethPrice).toFixed(2)}</p>
      </div>

      <div className="mt-auto">
        <button 
          onClick={handleAction}
          disabled={isConnected && isBase && (isPending || isConfirming || !amount)}
          className={`w-full py-4 rounded-sm font-bold transition-all ${
            !isConnected || !isBase || (amount && !isPending && !isConfirming)
              ? 'bg-white text-black hover:bg-[#37d097] hover:text-white'
              : 'bg-gray-800 text-gray-500 cursor-not-allowed'
          }`}
        >
          {buttonText()}
        </button>
        <div className="h-8 mt-2 flex items-center justify-center">
          {isConfirmed && <p className="text-[#37d097] font-bold text-sm">Success!</p>}
        </div>
      </div>

      <p className="text-[10px] text-gray-600 mt-4 pt-4 border-t border-gray-800">
        Risk Disclosure: Interacting with delta neutral vaults involves smart contract and market risks.
      </p>
    </div>
  );
}