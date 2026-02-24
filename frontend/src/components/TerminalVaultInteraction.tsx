// Created: 2026-02-23
'use client';

import { useState, useMemo, useEffect } from 'react';
import { useAccount, useChainId, useSwitchChain } from 'wagmi';
import { formatUnits, parseUnits } from 'viem';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useVault } from '@/hooks/useVault';
import { useToken } from '@/hooks/useToken';
import { VAULT_ADDRESS, ARB_VAULT_ADDRESS, OP_VAULT_ADDRESS, WETH_ADDRESS } from '@/config';
import { toast } from 'sonner';
import { Wallet2, ArrowDownCircle, ArrowUpCircle, Loader2, Shield } from 'lucide-react';

export function TerminalVaultInteraction() {
  const { address, isConnected } = useAccount();
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();
  
  const isCorrectNetwork = chainId === 8453;

  const { 
    convertToAssets, 
    deposit, 
    withdraw, 
    isPending: isVaultPending,
    isSuccess: isVaultSuccess,
    error: vaultError,
    refetchBalanceOf,
    refetchTotalAssets
  } = useVault();
  
  const { 
    allowance, 
    balance: wethBalance, 
    approve, 
    isPending: isTokenPending,
    isConfirmed: isTokenConfirmed,
    error: tokenError,
    refetchAllowance,
    refetchBalance: refetchWethBalance
  } = useToken(address, VAULT_ADDRESS);

  // Real-time refetching after transactions
  useEffect(() => {
    if (isTokenConfirmed) {
      toast.success("WETH Approved - Step 1/2 Complete", {
        description: "Now click 'Confirm Deposit' to transfer your WETH",
      });
      // Force refetch allowance with a small delay to ensure on-chain state is updated
      setTimeout(() => {
        refetchAllowance();
      }, 1500);
    }
  }, [isTokenConfirmed, refetchAllowance]);

  useEffect(() => {
    if (isVaultSuccess) {
      toast.success("Transaction Complete!", {
        description: "Your transaction has been successfully processed",
      });
      setDepositAmount('');
      setWithdrawAmount('');
      // Refetch all balances
      setTimeout(() => {
        refetchBalanceOf();
        refetchTotalAssets();
        refetchWethBalance();
        refetchAllowance();
      }, 1500);
    }
  }, [isVaultSuccess, refetchBalanceOf, refetchTotalAssets, refetchWethBalance, refetchAllowance]);

  // Error handling
  useEffect(() => {
    if (vaultError) {
      console.error('[TerminalVaultInteraction] Vault error:', vaultError);
      toast.error("Transaction Failed", {
        description: vaultError.message || "An error occurred. Please try again.",
      });
    }
  }, [vaultError]);

  useEffect(() => {
    if (tokenError) {
      console.error('[TerminalVaultInteraction] Token error:', tokenError);
      toast.error("Approval Failed", {
        description: tokenError.message || "Could not approve WETH. Please try again.",
      });
    }
  }, [tokenError]);

  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');

  const isPending = isVaultPending || isTokenPending;

  const handleApprove = () => {
    if (!depositAmount) {
      toast.error("Please enter an amount");
      return;
    }
    
    console.log('[TerminalVaultInteraction] Handling approval for:', depositAmount);
    approve(depositAmount);
  };

  const handleDeposit = () => {
    if (!depositAmount) {
      toast.error("Please enter an amount");
      return;
    }
    
    if (!address) {
      toast.error("Wallet not connected");
      return;
    }
    
    try {
      const amountBI = parseUnits(depositAmount, 18);
      console.log('[TerminalVaultInteraction] Handling deposit for:', amountBI.toString());
      deposit(amountBI);
    } catch (e) {
      console.error("Deposit failed", e);
      toast.error("Invalid amount format");
    }
  };

  const handleWithdraw = () => {
    if (!withdrawAmount) {
      toast.error("Please enter an amount");
      return;
    }
    
    if (!address) {
      toast.error("Wallet not connected");
      return;
    }
    
    try {
      const amountBI = parseUnits(withdrawAmount, 18);
      console.log('[TerminalVaultInteraction] Handling withdrawal for:', amountBI.toString());
      withdraw(amountBI);
    } catch (e) {
      console.error("Withdrawal failed", e);
      toast.error("Invalid amount format");
    }
  };

  const needsApproval = useMemo(() => {
    if (!depositAmount || !allowance) {
      console.log('[needsApproval] Missing data:', { depositAmount, allowance: allowance?.toString() });
      return true;
    }
    
    try {
      const requiredAmount = parseUnits(depositAmount, 18);
      const needsApproval = allowance < requiredAmount;
      console.log('[needsApproval] Check:', {
        depositAmount,
        allowance: allowance.toString(),
        requiredAmount: requiredAmount.toString(),
        needsApproval,
      });
      return needsApproval;
    } catch (e) {
      console.error('[needsApproval] Error parsing amount:', e);
      return true;
    }
  }, [depositAmount, allowance]);

  if (!isConnected) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#444a4f] rounded-sm">
        <div className="p-4 bg-[#16191c] rounded-full border border-[#444a4f]">
          <Wallet2 size={32} className="text-[#aab9be]" />
        </div>
        <div>
          <h3 className="text-lg font-heading font-medium text-[#ffffff]">Connect Wallet</h3>
          <p className="text-sm text-[#aab9be] mt-1">Please connect your wallet to interact with the Kerne Vault.</p>
        </div>
      </div>
    );
  }

  if (!isCorrectNetwork) {
    return (
      <div className="h-full flex flex-col items-center justify-center p-8 text-center space-y-4 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#ff6b6b]/20 rounded-sm">
        <div className="p-4 bg-[#16191c] rounded-full border border-[#ff6b6b]/40">
          <Shield size={32} className="text-[#ff6b6b]" />
        </div>
        <div>
          <h3 className="text-lg font-heading font-medium text-[#ffffff]">Wrong Network</h3>
          <p className="text-sm text-[#aab9be] mt-1 mb-6">The Kerne Vault is currently only available on Base Mainnet.</p>
          <Button 
            onClick={() => switchChain({ chainId: 8453 })}
            className="w-full bg-[#ffffff] text-[#000000] hover:bg-[#aab9be] rounded-sm font-bold h-12 transition-all text-xs uppercase tracking-widest"
          >
            Switch to Base
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="h-full flex flex-col bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#37d097] rounded-sm overflow-hidden">
      <div className="p-6 border-b border-[#444a4f] flex justify-between items-center">
        <div>
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide block mb-1">VAULT INTERACTION</span>
          <p className="text-lg font-heading font-medium text-[#ffffff]">Kerne Vault V1</p>
        </div>
        <div className="px-2 py-1 bg-[#37d097]/10 border border-[#37d097]/20 rounded-sm">
          <span className="text-[10px] font-bold text-[#37d097] uppercase">Base Mainnet</span>
        </div>
      </div>

      <div className="flex-1 p-6 flex flex-col">
        <Tabs defaultValue="deposit" className="w-full flex-1 flex flex-col">
          <TabsList className="grid w-full grid-cols-2 bg-[#16191c] border border-[#444a4f] rounded-sm p-1 h-12">
            <TabsTrigger 
              value="deposit" 
              className="rounded-sm data-[state=active]:bg-[#aab9be] data-[state=active]:text-[#000000] font-bold text-xs transition-all"
            >
              Deposit
            </TabsTrigger>
            <TabsTrigger 
              value="withdraw" 
              className="rounded-sm data-[state=active]:bg-[#aab9be] data-[state=active]:text-[#000000] font-bold text-xs transition-all"
            >
              Withdraw
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="mt-6 flex-1 flex flex-col space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">
                <span>Asset: WETH</span>
                <span>Balance: {wethBalance ? parseFloat(formatUnits(wethBalance, 18)).toFixed(4) : '0.0000'}</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={depositAmount}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Only allow positive numbers with up to 18 decimals
                    if (value === '' || /^\d*\.?\d{0,18}$/.test(value)) {
                      setDepositAmount(value);
                    }
                  }}
                  min="0"
                  step="0.000001"
                  className="bg-[#000000] border-[#444a4f] rounded-sm font-medium text-lg h-14 focus-visible:ring-[#37d097]/20 text-[#ffffff] px-4"
                />
                <button
                  onClick={() => wethBalance && setDepositAmount(formatUnits(wethBalance, 18))}
                  className="absolute right-3 top-3.5 text-[10px] font-bold text-[#37d097] hover:text-[#ffffff] transition-colors uppercase tracking-widest bg-[#37d097]/10 px-2 py-1 rounded-sm border border-[#37d097]/20"
                >
                  Max
                </button>
              </div>
            </div>

            <div className="p-4 bg-[#16191c] border border-[#444a4f] rounded-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">Estimated APY</span>
                <span className="text-xs font-bold text-[#37d097]">18.40%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">Protocol Fee</span>
                <span className="text-xs font-bold text-[#ffffff]">0.00%</span>
              </div>
            </div>

            <div className="mt-auto space-y-3">
              <Button
                onClick={handleApprove}
                disabled={!needsApproval || isPending || !depositAmount}
                className={`w-full rounded-sm font-bold h-14 transition-all text-xs uppercase tracking-widest ${
                  needsApproval 
                    ? 'bg-[#ffffff] text-[#000000] hover:bg-[#aab9be]' 
                    : 'bg-[#16191c] text-[#37d097] border border-[#37d097] cursor-not-allowed'
                }`}
              >
                {needsApproval ? (
                  <>
                    {isPending ? <Loader2 className="animate-spin mr-2" size={16} /> : <ArrowDownCircle className="mr-2" size={16} />}
                    {isPending ? 'Processing...' : 'Step 1: Approve WETH'}
                  </>
                ) : (
                  <>✓ WETH Approved</>
                )}
              </Button>
              
              <Button
                onClick={handleDeposit}
                disabled={needsApproval || isPending || !depositAmount}
                className={`w-full rounded-sm font-bold h-14 transition-all text-xs uppercase tracking-widest ${
                  needsApproval
                    ? 'bg-[#16191c] text-[#aab9be] border border-[#444a4f] cursor-not-allowed'
                    : 'bg-[#37d097] text-[#000000] hover:bg-[#2eb07f]'
                }`}
              >
                {isPending ? <Loader2 className="animate-spin mr-2" size={16} /> : <ArrowDownCircle className="mr-2" size={16} />}
                {isPending ? 'Processing...' : 'Step 2: Confirm Deposit'}
              </Button>
            </div>
          </TabsContent>

          <TabsContent value="withdraw" className="mt-6 flex-1 flex flex-col space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">
                <span>Asset: Kerne Shares</span>
                <span>Balance: {convertToAssets ? parseFloat(formatUnits(convertToAssets, 18)).toFixed(4) : '0.0000'} WETH</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={withdrawAmount}
                  onChange={(e) => {
                    const value = e.target.value;
                    // Only allow positive numbers with up to 18 decimals
                    if (value === '' || /^\d*\.?\d{0,18}$/.test(value)) {
                      setWithdrawAmount(value);
                    }
                  }}
                  min="0"
                  step="0.000001"
                  className="bg-[#000000] border-[#444a4f] rounded-sm font-medium text-lg h-14 focus-visible:ring-[#37d097]/20 text-[#ffffff] px-4"
                />
                <button
                  onClick={() => convertToAssets && setWithdrawAmount(formatUnits(convertToAssets, 18))}
                  className="absolute right-3 top-3.5 text-[10px] font-bold text-[#37d097] hover:text-[#ffffff] transition-colors uppercase tracking-widest bg-[#37d097]/10 px-2 py-1 rounded-sm border border-[#37d097]/20"
                >
                  Max
                </button>
              </div>
            </div>

            <div className="p-4 bg-[#16191c] border border-[#444a4f] rounded-sm space-y-3">
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">Cooldown</span>
                <span className="text-xs font-bold text-[#37d097]">Instant</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] font-bold text-[#aab9be] uppercase tracking-wider">Withdrawal Fee</span>
                <span className="text-xs font-bold text-[#ffffff]">0.00%</span>
              </div>
            </div>

            <div className="mt-auto">
              <Button
                onClick={handleWithdraw}
                disabled={isPending || !withdrawAmount}
                className="w-full bg-[#ffffff] text-[#000000] hover:bg-[#aab9be] rounded-sm font-bold h-14 transition-all text-xs uppercase tracking-widest"
              >
                {isPending ? <Loader2 className="animate-spin mr-2" size={16} /> : <ArrowUpCircle className="mr-2" size={16} />}
                {isPending ? 'Processing...' : 'Confirm Withdrawal'}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}