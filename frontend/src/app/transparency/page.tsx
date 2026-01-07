// Created: 2025-12-28
// Updated: 2025-12-30 - Integrated Solvency Dashboard v2.0
'use client';

import React from 'react';
import { useSolvency } from '@/hooks/useSolvency';
import { MetricCard } from '@/components/MetricCard';
import { SolvencyChart } from '@/components/SolvencyChart';
import { VAULT_ADDRESS } from '@/config';

export default function TransparencyPage() {
  const { data, loading, error } = useSolvency();

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-zinc-100 p-8 flex items-center justify-center font-mono">
        <div className="animate-pulse text-emerald-500 uppercase tracking-widest">Loading_Solvency_Data...</div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-black text-zinc-100 p-8 flex items-center justify-center font-mono">
        <div className="text-red-500 uppercase tracking-widest">Error_Loading_Data: {error || 'Unknown Error'}</div>
      </div>
    );
  }

  return (
    <main className="min-h-screen bg-black text-zinc-100 p-8 md:p-24 font-mono selection:bg-emerald-500 selection:text-black">
      <div className="max-w-4xl mx-auto space-y-12">
        <header className="border-b border-zinc-800 pb-8 flex flex-col md:flex-row md:items-end md:justify-between gap-4">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter uppercase">Solvency_Dashboard_v2.0</h1>
            <p className="text-zinc-500 mt-2">Real-Time Proof of Reserves & Protocol Health</p>
          </div>
          <div className="text-right">
            <div className="text-[10px] text-zinc-500 uppercase tracking-widest mb-1">Last_Verified</div>
            <div className="text-xs text-emerald-500">{new Date(data.timestamp).toLocaleString()}</div>
          </div>
        </header>

        {/* Solvency Ratio & Status */}
        <section className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div className="md:col-span-2 p-6 bg-zinc-900/30 border border-zinc-800 flex flex-col justify-between">
            <div>
              <h3 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Protocol_Solvency_Ratio</h3>
              <div className="flex items-baseline gap-4">
                <span className="text-6xl font-bold text-white">{data.solvency_ratio}%</span>
                <span className={`text-sm px-2 py-1 border ${
                  data.status === 'OVERCOLLATERALIZED' ? 'border-emerald-500 text-emerald-500' : 'border-red-500 text-red-500'
                }`}>
                  {data.status}
                </span>
              </div>
            </div>
            <p className="text-xs text-zinc-500 mt-6 leading-relaxed">
              The solvency ratio represents the total protocol assets (on-chain + off-chain) divided by total liabilities (kUSD supply). A ratio above 100% indicates full collateralization.
            </p>
          </div>
          <MetricCard 
            label="TOTAL_LIABILITIES" 
            value={`$${parseFloat(data.liabilities.total_usd).toLocaleString()}`} 
            subValue="kUSD_CIRCULATING_SUPPLY"
          />
        </section>

        {/* Asset Breakdown */}
        <section className="space-y-6">
          <h2 className="text-xl text-emerald-500 border-l-2 border-emerald-500 pl-4 uppercase">Asset_Composition</h2>
          <div className="p-8 bg-zinc-900/30 border border-zinc-800 space-y-8">
            <SolvencyChart breakdown={data.assets.breakdown} />
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8 pt-8 border-t border-zinc-800">
              <div>
                <h4 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">On-Chain_Reserves</h4>
                <div className="text-2xl font-bold text-white">{data.assets.on_chain_eth} ETH</div>
                <div className="text-sm text-zinc-500 mt-1">Vault Smart Contract (Base)</div>
              </div>
              <div>
                <h4 className="text-xs text-zinc-500 uppercase tracking-widest mb-4">Off-Chain_Collateral</h4>
                <div className="text-2xl font-bold text-white">{data.assets.off_chain_eth} ETH</div>
                <div className="text-sm text-zinc-500 mt-1">Institutional Reserve & CEX Reserves</div>
              </div>
            </div>
          </div>
        </section>

        {/* Live Proof Section */}
        <section className="space-y-6">
          <h2 className="text-xl text-emerald-500 border-l-2 border-emerald-500 pl-4 uppercase">Verification_Nodes</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <a 
              href={`https://basescan.org/address/${VAULT_ADDRESS}`}
              target="_blank"
              rel="noopener noreferrer"
              className="p-6 bg-zinc-900/50 border border-zinc-800 hover:border-emerald-500 transition-colors group"
            >
              <h3 className="text-white mb-2 group-hover:text-emerald-500">BASESCAN_EXPLORER</h3>
              <p className="text-sm text-zinc-500">Verify on-chain balances and contract source code directly on the Base network.</p>
            </a>
            <div className="p-6 bg-zinc-900/50 border border-zinc-800">
              <h3 className="text-white mb-2">OES_MIRROR_X</h3>
              <p className="text-sm text-zinc-500">Off-Exchange Settlement verified via Ceffu MirrorX. Assets remain in MPC custody while mirrored to CEX.</p>
              <div className="mt-4 text-[10px] text-emerald-500 uppercase tracking-widest">Status: Active_Mirror</div>
            </div>
            <div className="p-6 bg-zinc-900/50 border border-zinc-800 opacity-80">
              <h3 className="text-white mb-2">STRATEGIST_ATTESTATION</h3>
              <p className="text-sm text-zinc-500">Off-chain balances are updated every 4 hours via signed messages from the Kerne Strategist Bot.</p>
            </div>
          </div>
        </section>

        {/* Strategy Note */}
        <section className="p-6 bg-zinc-950 border border-dashed border-zinc-800">
          <h3 className="text-xs text-zinc-500 uppercase mb-4 tracking-widest">Transparency_Protocol_Note</h3>
          <p className="text-sm text-zinc-400 leading-relaxed">
            Kerne Protocol utilizes a delta-neutral hedging strategy. Assets are split between on-chain liquidity for immediate withdrawals and off-chain collateral (Institutional Reserve & CEX Reserves) to maintain short positions against ETH price volatility. The Institutional Reserve represents protocol-owned capital and verified off-exchange settlement (OES) balances deployed to ensure deep liquidity and stability during the Genesis phase.
          </p>
        </section>

        <div className="flex justify-center">
          <a 
            href="/api/solvency" 
            target="_blank"
            className="text-[10px] text-emerald-500/50 hover:text-emerald-500 uppercase tracking-[0.2em] border border-emerald-500/20 px-4 py-2 rounded hover:bg-emerald-500/5 transition-all"
          >
            View_Raw_Institutional_Data_Feed
          </a>
        </div>

        <footer className="pt-12 border-t border-zinc-800 text-center text-xs text-zinc-600 uppercase tracking-widest">
          Kerne Protocol // Trust_Through_Mathematics
        </footer>
      </div>
    </main>
  );
}
