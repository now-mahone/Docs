// Created: 2025-12-29
'use client';

import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowUpRight, Droplets, TrendingUp, Zap } from 'lucide-react';
import Link from 'next/link';

export default function LiquidityPortal() {
  const pools = [
    {
      name: 'kUSD / USDC',
      platform: 'Aerodrome',
      tvl: '$1,240,582',
      apr: '24.8%',
      status: 'Active',
      type: 'Stable',
      zapEnabled: true
    },
    {
      name: 'kUSD / WETH',
      platform: 'Aerodrome',
      tvl: '$842,105',
      apr: '42.1%',
      status: 'Active',
      type: 'Volatile',
      zapEnabled: true
    }
  ];

  return (
    <main className="min-h-screen bg-obsidian text-zinc-100 p-8 font-mono">
      <header className="max-w-6xl mx-auto mb-12 border-b border-zinc-800 pb-8">
        <Link href="/terminal" className="text-zinc-500 hover:text-white transition-colors mb-4 inline-block">
          {"<"} BACK_TO_TERMINAL
        </Link>
        <h1 className="text-4xl font-bold tracking-tighter uppercase">Liquidity_Portal</h1>
        <p className="text-zinc-500 mt-2">Provide liquidity to the Kerne ecosystem and earn $KERNE + $AERO rewards.</p>
      </header>

      <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-8 mb-12">
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader>
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Droplets size={12} className="text-emerald-500" /> Total_Ecosystem_Liquidity
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">$2,082,687</div>
            <div className="text-[10px] text-emerald-500 mt-1">+12.4% (24H)</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader>
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <TrendingUp size={12} className="text-emerald-500" /> Average_LP_APR
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold">33.45%</div>
            <div className="text-[10px] text-zinc-500 mt-1">INCLUDES_TRADING_FEES</div>
          </CardContent>
        </Card>
        <Card className="bg-zinc-900 border-zinc-800 rounded-none">
          <CardHeader>
            <CardTitle className="text-[10px] text-zinc-500 uppercase tracking-widest flex items-center gap-2">
              <Zap size={12} className="text-emerald-500" /> Stability_Module_Status
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-emerald-500">OPTIMAL</div>
            <div className="text-[10px] text-zinc-500 mt-1">PEG_DEVIATION: 0.04%</div>
          </CardContent>
        </Card>
      </div>

      <div className="max-w-6xl mx-auto space-y-4">
        <h2 className="text-sm font-bold text-zinc-500 uppercase tracking-widest mb-4">Active_Liquidity_Pools</h2>
        {pools.map((pool, i) => (
          <div key={i} className="p-6 bg-zinc-900/50 border border-zinc-800 flex flex-col md:flex-row justify-between items-center gap-6 hover:bg-zinc-900 transition-colors">
            <div className="flex items-center gap-4">
              <div className="w-10 h-10 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500">
                <Droplets size={20} />
              </div>
              <div>
                <div className="text-lg font-bold">{pool.name}</div>
                <div className="text-[10px] text-zinc-500 uppercase">{pool.platform} // {pool.type}</div>
              </div>
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-12">
              <div>
                <div className="text-[10px] text-zinc-500 uppercase mb-1">TVL</div>
                <div className="text-sm font-bold">{pool.tvl}</div>
              </div>
              <div>
                <div className="text-[10px] text-zinc-500 uppercase mb-1">APR</div>
                <div className="text-sm font-bold text-emerald-500">{pool.apr}</div>
              </div>
              <div className="hidden md:block">
                <div className="text-[10px] text-zinc-500 uppercase mb-1">Status</div>
                <div className="text-sm font-bold text-emerald-500">{pool.status}</div>
              </div>
            </div>
            <div className="flex gap-2">
              {pool.zapEnabled && (
                <Button className="bg-emerald-600 text-black hover:bg-emerald-500 rounded-none font-mono uppercase text-xs px-6 flex items-center gap-2">
                  <Zap size={14} /> One_Click_Zap
                </Button>
              )}
              <Button className="bg-white text-black hover:bg-zinc-200 rounded-none font-mono uppercase text-xs px-8">
                Add_Liquidity <ArrowUpRight size={14} className="ml-2" />
              </Button>
            </div>
          </div>
        ))}
      </div>
    </main>
  );
}
