// Created: 2026-01-06
'use client';

import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { formatUnits } from 'viem';
import { useVault } from '@/hooks/useVault';

interface PartnerAnalyticsProps {
  vaultAddress: string;
}

export function PartnerAnalytics({ vaultAddress }: PartnerAnalyticsProps) {
  const { totalAssets, offChainAssets, grossPerformanceFeeBps } = useVault();

  const stats = useMemo(() => {
    const total = totalAssets ? parseFloat(formatUnits(totalAssets, 18)) : 0;
    const offChain = offChainAssets ? parseFloat(formatUnits(offChainAssets, 18)) : 0;
    const fee = grossPerformanceFeeBps ? Number(grossPerformanceFeeBps) / 100 : 0;
    
    // Simulated revenue based on 15% APY
    const annualRevenue = total * 0.15 * (fee / 100);
    const monthlyRevenue = annualRevenue / 12;

    return {
      total,
      offChain,
      fee,
      annualRevenue,
      monthlyRevenue
    };
  }, [totalAssets, offChainAssets, grossPerformanceFeeBps]);

  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Card className="bg-zinc-900/50 border-zinc-800 rounded-none">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-mono text-zinc-500 uppercase">Vault_TVL</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-mono text-white">{stats.total.toFixed(2)} ETH</div>
          <div className="text-xs font-mono text-zinc-600 mt-1">
            {((stats.offChain / stats.total) * 100 || 0).toFixed(2)}% UTILIZED
          </div>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900/50 border-zinc-800 rounded-none">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-mono text-zinc-500 uppercase">Performance_Fee</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-mono text-emerald-500">{stats.fee.toFixed(1)}%</div>
          <div className="text-xs font-mono text-zinc-600 mt-1">BESPOKE CONFIGURATION</div>
        </CardContent>
      </Card>

      <Card className="bg-zinc-900/50 border-zinc-800 rounded-none">
        <CardHeader className="pb-2">
          <CardTitle className="text-xs font-mono text-zinc-500 uppercase">Est_Monthly_Revenue</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="text-xl font-mono text-blue-400">${(stats.monthlyRevenue * 3000).toFixed(2)}</div>
          <div className="text-xs font-mono text-zinc-600 mt-1">BASED ON 15% PROJECTED APY</div>
        </CardContent>
      </Card>
    </div>
  );
}
