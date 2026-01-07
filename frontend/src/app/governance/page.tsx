// Created: 2025-12-29
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useGovernance } from '@/hooks/useGovernance';
import { formatUnits, parseUnits } from 'viem';
import { toast } from 'sonner';
import { useToken } from '@/hooks/useToken';
import { KERNE_STAKING_ADDRESS, KERNE_TOKEN_ADDRESS } from '@/config';
import { useAccount } from 'wagmi';
import Link from 'next/link';
import { Lock, Coins, TrendingUp, Vote } from 'lucide-react';

export default function GovernanceHub() {
  const { address } = useAccount();
  const { 
    kerneBalance, 
    stakedAmount, 
    lockEnd, 
    pendingRewards, 
    totalStaked, 
    stake, 
    withdraw, 
    claimRewards, 
    isPending,
    refetchKerneBalance,
    refetchStake,
    refetchRewards
  } = useGovernance();

  const { allowance, approve, refetchAllowance } = useToken(address, KERNE_STAKING_ADDRESS, KERNE_TOKEN_ADDRESS);

  const [stakeAmount, setStakeAmount] = useState('');
  const [lockDuration, setLockDuration] = useState('604800'); // 1 week default

  const handleStake = async () => {
    if (!stakeAmount) return;
    const toastId = toast.loading("STAKING $KERNE...");
    try {
      await stake(parseUnits(stakeAmount, 18), parseInt(lockDuration));
      setStakeAmount('');
      refetchKerneBalance();
      refetchStake();
      toast.success("STAKING SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("STAKING FAILED", { id: toastId });
    }
  };

  const handleApprove = async () => {
    if (!stakeAmount) return;
    const toastId = toast.loading("APPROVING $KERNE...");
    try {
      await approve(stakeAmount);
      refetchAllowance();
      toast.success("$KERNE APPROVED", { id: toastId });
    } catch (e) {
      toast.error("APPROVAL FAILED", { id: toastId });
    }
  };

  const needsApproval = allowance !== undefined && stakeAmount ? allowance < parseUnits(stakeAmount, 18) : true;

  return (
    <main className="min-h-screen bg-obsidian text-zinc-100 p-8 font-mono">
      <header className="max-w-6xl mx-auto mb-12 border-b border-zinc-800 pb-8">
        <Link href="/terminal" className="text-zinc-500 hover:text-white transition-colors mb-4 inline-block">
          {"<"} BACK_TO_TERMINAL
        </Link>
        <h1 className="text-4xl font-bold tracking-tighter uppercase">Governance_Hub</h1>
        <p className="text-zinc-500 mt-2">Stake $KERNE to earn protocol fees and participate in risk management.</p>
      </header>

      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Coins size={12} className="text-emerald-500" /> Your_Stake
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stakedAmount ? Number(formatUnits(stakedAmount, 18)).toFixed(2) : '0.00'}</div>
            <div className="text-[10px] text-zinc-500 mt-1">KERNE_LOCKED</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <TrendingUp size={12} className="text-emerald-500" /> Pending_Rewards
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-500">{pendingRewards ? Number(formatUnits(pendingRewards, 18)).toFixed(4) : '0.0000'}</div>
            <div className="text-[10px] text-zinc-500 mt-1">WETH_EARNED</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Vote size={12} className="text-emerald-500" /> Voting_Power
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{(Number(stakedAmount || 0n) / 1e18).toFixed(0)}</div>
            <div className="text-[10px] text-zinc-500 mt-1">veKERNE_WEIGHT</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader className="pb-2">
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Lock size={12} className="text-emerald-500" /> Total_Staked
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{totalStaked ? (Number(formatUnits(totalStaked, 18)) / 1000000).toFixed(1) : '0.0'}M</div>
            <div className="text-[10px] text-zinc-500 mt-1">GLOBAL_KERNE_LOCKED</div>
          </CardContent>
        </Card>
      </div>

      <div className="max-w-6xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <Card className="bg-black border-zinc-800 rounded-none">
            <CardHeader className="border-b border-zinc-800">
              <CardTitle className="text-sm font-mono text-zinc-400 uppercase tracking-widest">Staking_Interface</CardTitle>
            </CardHeader>
            <CardContent className="p-6 space-y-6">
              <div className="space-y-2">
                <div className="flex justify-between text-[10px] font-mono text-zinc-500 uppercase">
                  <span>Balance</span>
                  <span>{kerneBalance ? formatUnits(kerneBalance, 18) : '0.00'} KERNE</span>
                </div>
                <Input
                  type="number"
                  placeholder="0.00"
                  value={stakeAmount}
                  onChange={(e) => setStakeAmount(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
                />
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-mono text-zinc-500 uppercase">Lock_Duration</label>
                <select 
                  value={lockDuration}
                  onChange={(e) => setLockDuration(e.target.value)}
                  className="w-full bg-zinc-950 border border-zinc-800 rounded-none font-mono text-sm p-2 text-white"
                >
                  <option value="604800">1 WEEK</option>
                  <option value="2592000">1 MONTH</option>
                  <option value="15552000">6 MONTHS</option>
                  <option value="31536000">1 YEAR</option>
                </select>
              </div>

              {needsApproval ? (
                <Button
                  onClick={handleApprove}
                  disabled={isPending || !stakeAmount}
                  className="w-full bg-white text-black hover:bg-zinc-200 rounded-none font-mono"
                >
                  APPROVE_KERNE
                </Button>
              ) : (
                <Button
                  onClick={handleStake}
                  disabled={isPending || !stakeAmount}
                  className="w-full bg-emerald-600 text-white hover:bg-emerald-700 rounded-none font-mono"
                >
                  CONFIRM_STAKE
                </Button>
              )}

              <Button
                onClick={() => claimRewards()}
                disabled={isPending || !pendingRewards || pendingRewards === 0n}
                className="w-full bg-zinc-800 text-white hover:bg-zinc-700 rounded-none font-mono"
              >
                CLAIM_REWARDS
              </Button>
            </CardContent>
          </Card>
        </div>

        <div className="lg:col-span-2 space-y-4">
          <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest">Active_Proposals</h2>
          <div className="p-6 bg-zinc-900/50 border border-zinc-800 space-y-4">
            <div className="flex justify-between items-start">
              <div>
                <div className="text-xs text-emerald-500 font-bold mb-1">KIP-001 // ACTIVE</div>
                <h3 className="text-lg font-bold">Increase kUSD Mint Collateral Ratio to 160%</h3>
                <p className="text-sm text-zinc-500 mt-2">Adjusting risk parameters to account for increased market volatility in ETH-PERP funding rates.</p>
              </div>
              <div className="text-right">
                <div className="text-[10px] text-zinc-500 uppercase">Ends_In</div>
                <div className="text-sm font-bold">2D 14H</div>
              </div>
            </div>
            <div className="h-2 w-full bg-zinc-800 rounded-full overflow-hidden">
              <div className="h-full bg-emerald-500 w-[72%]" />
            </div>
            <div className="flex justify-between text-[10px] font-mono text-zinc-500">
              <span>FOR: 1.2M veKERNE (72%)</span>
              <span>AGAINST: 460K veKERNE (28%)</span>
            </div>
            <div className="flex gap-2">
              <Button className="flex-1 bg-emerald-600/20 text-emerald-500 border border-emerald-500/30 hover:bg-emerald-600/30 rounded-none font-mono text-xs">VOTE_FOR</Button>
              <Button className="flex-1 bg-red-600/20 text-red-500 border border-red-500/30 hover:bg-red-600/30 rounded-none font-mono text-xs">VOTE_AGAINST</Button>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
