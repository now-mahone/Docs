// Created: 2025-12-28
'use client';

import { useState, useMemo } from 'react';
import { useAccount } from 'wagmi';
import { formatUnits, parseUnits } from 'viem';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useVault } from '@/hooks/useVault';
import { useToken } from '@/hooks/useToken';
import { VAULT_ADDRESS } from '@/config';
import { toast } from 'sonner';
import { useEffect } from 'react';

export function VaultInterface() {
  const { address } = useAccount();
  const [credits, setCredits] = useState<number | null>(null);
  const { 
    convertToAssets, 
    deposit, 
    withdraw, 
    isPending: isVaultPending,
    refetchBalanceOf,
    refetchTotalAssets
  } = useVault();
  
  const { 
    allowance, 
    balance: wethBalance, 
    approve, 
    isPending: isTokenPending,
    refetchAllowance,
    refetchBalance: refetchWethBalance
  } = useToken(address, VAULT_ADDRESS);

  const [depositAmount, setDepositAmount] = useState('');
  const [withdrawAmount, setWithdrawAmount] = useState('');

  const isPending = isVaultPending || isTokenPending;

  useEffect(() => {
    if (address) {
      fetch(`/api/credits?address=${address}`)
        .then(res => res.json())
        .then(data => setCredits(data.credits))
        .catch(err => console.error("Failed to fetch credits", err));
    }
  }, [address]);

  // Yield Projection Logic
  const projection = useMemo(() => {
    if (!depositAmount || isNaN(Number(depositAmount))) return null;
    const amount = Number(depositAmount);
    const annual = amount * 0.124;
    const weekly = annual / 52;
    return {
      weekly: weekly.toFixed(4),
      annual: annual.toFixed(4),
    };
  }, [depositAmount]);

  const handleApprove = async () => {
    if (!depositAmount) return;
    const toastId = toast.loading("INITIALIZING APPROVAL...");
    try {
      await approve(depositAmount);
      refetchAllowance();
      toast.success("WETH APPROVED", { id: toastId });
    } catch (e) {
      toast.error("APPROVAL FAILED", { id: toastId });
    }
  };

  const handleDeposit = async () => {
    if (!depositAmount) return;
    const toastId = toast.loading("CONFIRMING DEPOSIT...");
    try {
      const amountBI = parseUnits(depositAmount, 18);
      await deposit(amountBI);
      setDepositAmount('');
      refetchBalanceOf();
      refetchTotalAssets();
      refetchWethBalance();
      refetchAllowance();
      toast.success("DEPOSIT SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("DEPOSIT FAILED", { id: toastId });
    }
  };

  const handleWithdraw = async () => {
    if (!withdrawAmount) return;
    const toastId = toast.loading("CONFIRMING WITHDRAWAL...");
    try {
      // For simplicity, we assume 1 share = 1 asset for the input, 
      // but the vault uses shares. In a real app, we'd convert.
      const amountBI = parseUnits(withdrawAmount, 18);
      await withdraw(amountBI);
      setWithdrawAmount('');
      refetchBalanceOf();
      refetchTotalAssets();
      refetchWethBalance();
      toast.success("WITHDRAWAL SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("WITHDRAWAL FAILED", { id: toastId });
    }
  };

  const needsApproval = useMemo(() => {
    if (!depositAmount || !allowance) return true;
    try {
      return allowance < parseUnits(depositAmount, 18);
    } catch {
      return true;
    }
  }, [depositAmount, allowance]);

  return (
    <Card className="bg-white border-[#f1f1ed] rounded-sm overflow-hidden">
      <CardHeader className="border-b border-[#f1f1ed] bg-[#f9f9f4]/30 px-6 py-4">
        <CardTitle className="text-xs font-bold text-zinc-400 uppercase tracking-tight">
          Vault Interaction
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <Tabs defaultValue="deposit" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-[#f1f1ed] rounded-full p-1.5 h-12">
            <TabsTrigger 
              value="deposit" 
              className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs"
            >
              Deposit
            </TabsTrigger>
            <TabsTrigger 
              value="withdraw" 
              className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs"
            >
              Withdraw
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="mt-8 space-y-6">
            {credits !== null && (
              <div className="px-4 py-3 bg-primary/5 border border-primary/10 rounded-sm flex justify-between items-center">
                <span className="text-xs font-bold text-primary tracking-tight">Kerne Credits</span>
                <span className="text-xs font-bold text-primary">{credits.toFixed(2)} pts</span>
              </div>
            )}
            <div className="space-y-3">
              <div className="flex justify-between text-xs font-bold text-zinc-400">
                <span>Asset: WETH</span>
                <span>Balance: {wethBalance ? formatUnits(wethBalance, 18) : '0.00'}</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="bg-zinc-50 border-zinc-100 rounded-sm font-bold text-l h-14 focus-visible:ring-primary/20 px-4"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => wethBalance && setDepositAmount(formatUnits(wethBalance, 18))}
                  className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7"
                >
                  Max
                </Button>
              </div>
            </div>

            {projection && (
              <div className="p-4 bg-zinc-50 rounded-sm space-y-2 border border-zinc-100">
                <div className="text-xs font-bold text-zinc-400 uppercase tracking-tight">Yield Projection (12.4% APY)</div>
                <div className="flex justify-between items-center">
                   <span className="text-xs font-medium text-zinc-500">Weekly</span>
                   <span className="text-xs font-bold text-[#000000]">+{projection.weekly} ETH</span>
                </div>
                <div className="flex justify-between items-center">
                   <span className="text-xs font-medium text-zinc-500">Annual</span>
                   <span className="text-xs font-bold text-primary">+{projection.annual} ETH</span>
                </div>
              </div>
            )}

            {needsApproval ? (
              <Button
                onClick={handleApprove}
                disabled={isPending || !depositAmount}
                className="w-full bg-primary text-white hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
              >
                {isPending ? 'Processing...' : 'Approve WETH'}
              </Button>
            ) : (
              <Button
                onClick={handleDeposit}
                disabled={isPending || !depositAmount}
                className="w-full bg-primary text-white hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
              >
                {isPending ? 'Processing...' : 'Confirm Deposit'}
              </Button>
            )}
          </TabsContent>

          <TabsContent value="withdraw" className="mt-8 space-y-6">
            <div className="space-y-3">
              <div className="flex justify-between text-xs font-bold text-zinc-400">
                <span>Asset: Kerne V1</span>
                <span>Balance: {convertToAssets ? formatUnits(convertToAssets, 18) : '0.00'} WETH</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="bg-zinc-50 border-zinc-100 rounded-sm font-bold text-l h-14 focus-visible:ring-primary/20 px-4"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => convertToAssets && setWithdrawAmount(formatUnits(convertToAssets, 18))}
                  className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7"
                >
                  Max
                </Button>
              </div>
            </div>

            <Button
              onClick={handleWithdraw}
              disabled={isPending || !withdrawAmount}
              className="w-full bg-[#191919] text-white hover:bg-[#1f1f1f] rounded-full font-bold h-14 transition-all text-s"
            >
              {isPending ? 'Processing...' : 'Confirm Withdrawal'}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
