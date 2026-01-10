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
    <Card className="bg-card border-border rounded-xl shadow-sm overflow-hidden">
      <CardHeader className="border-b border-border bg-grey-50/50">
        <CardTitle className="text-sm font-heading font-bold text-muted-foreground uppercase tracking-widest">
          Vault_Interaction_Core
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <Tabs defaultValue="deposit" className="w-full">
          <TabsList className="grid w-full grid-cols-2 bg-grey-100 rounded-lg p-1">
            <TabsTrigger 
              value="deposit" 
              className="rounded-md data-[state=active]:bg-white data-[state=active]:text-primary data-[state=active]:shadow-sm font-heading font-bold"
            >
              DEPOSIT
            </TabsTrigger>
            <TabsTrigger 
              value="withdraw" 
              className="rounded-md data-[state=active]:bg-white data-[state=active]:text-primary data-[state=active]:shadow-sm font-heading font-bold"
            >
              WITHDRAW
            </TabsTrigger>
          </TabsList>

          <TabsContent value="deposit" className="mt-6 space-y-6">
            {credits !== null && (
              <div className="p-3 bg-primary/10 border border-primary/20 rounded-lg flex justify-between items-center">
                <span className="text-[10px] font-sans text-primary uppercase tracking-widest font-bold">Kerne_Credits_Accrued</span>
                <span className="text-sm font-sans font-bold text-primary">{credits.toFixed(2)} PTS</span>
              </div>
            )}
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-sans font-bold text-muted-foreground">
                <span>ASSET: WETH</span>
                <span>BALANCE: {wethBalance ? formatUnits(wethBalance, 18) : '0.00'}</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={depositAmount}
                  onChange={(e) => setDepositAmount(e.target.value)}
                  className="bg-white border-border rounded-lg font-sans font-bold text-lg h-12 focus-visible:ring-primary/20"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => wethBalance && setDepositAmount(formatUnits(wethBalance, 18))}
                  className="absolute right-2 top-2 text-xs font-sans font-bold hover:bg-grey-100 rounded-md"
                >
                  MAX
                </Button>
              </div>
            </div>

            {projection && (
              <div className="p-4 bg-grey-50 border border-dashed border-border font-sans text-xs space-y-1 rounded-lg">
                <div className="text-muted-foreground uppercase tracking-tighter font-bold">Yield_Projection (12.4% APY)</div>
                <div className="text-primary font-bold">
                  [EST_WEEKLY_REVENUE: +{projection.weekly} ETH]
                </div>
                <div className="text-primary-dark font-bold">
                  [EST_ANNUAL_REVENUE: +{projection.annual} ETH]
                </div>
              </div>
            )}

            {needsApproval ? (
              <Button
                onClick={handleApprove}
                disabled={isPending || !depositAmount}
                className="w-full bg-primary text-primary-foreground hover:bg-primary-dark rounded-lg font-heading font-bold h-12 shadow-sm transition-all"
              >
                {isPending ? 'PROCESSING...' : 'APPROVE_WETH'}
              </Button>
            ) : (
              <Button
                onClick={handleDeposit}
                disabled={isPending || !depositAmount}
                className="w-full bg-primary text-primary-foreground hover:bg-primary-dark rounded-lg font-heading font-bold h-12 shadow-sm transition-all"
              >
                {isPending ? 'PROCESSING...' : 'CONFIRM_DEPOSIT'}
              </Button>
            )}
          </TabsContent>

          <TabsContent value="withdraw" className="mt-6 space-y-6">
            <div className="space-y-2">
              <div className="flex justify-between text-xs font-sans font-bold text-muted-foreground">
                <span>ASSET: KERNE-V1</span>
                <span>VAULT_BALANCE: {convertToAssets ? formatUnits(convertToAssets, 18) : '0.00'} WETH</span>
              </div>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00"
                  value={withdrawAmount}
                  onChange={(e) => setWithdrawAmount(e.target.value)}
                  className="bg-white border-border rounded-lg font-sans font-bold text-lg h-12 focus-visible:ring-primary/20"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => convertToAssets && setWithdrawAmount(formatUnits(convertToAssets, 18))}
                  className="absolute right-2 top-2 text-xs font-sans font-bold hover:bg-grey-100 rounded-md"
                >
                  MAX
                </Button>
              </div>
            </div>

            <Button
              onClick={handleWithdraw}
              disabled={isPending || !withdrawAmount}
              className="w-full bg-grey-100 text-foreground hover:bg-grey-200 rounded-lg font-heading font-bold h-12 shadow-sm transition-all"
            >
              {isPending ? 'PROCESSING...' : 'CONFIRM_WITHDRAWAL'}
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
