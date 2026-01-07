// Created: 2026-01-06
'use client';

import React from 'react';
import PrimeTerminal from '@/components/PrimeTerminal';
import { Shield, Info } from 'lucide-react';

export default function PrimePage() {
  return (
    <main className="min-h-screen bg-obsidian text-zinc-100 p-6 font-mono">
      <header className="mb-12 border-b border-zinc-800 pb-4">
        <h1 className="text-xl font-bold tracking-tighter uppercase">Institutional_Prime_Brokerage</h1>
        <p className="text-[10px] text-zinc-500 mt-1 uppercase tracking-widest">Direct_CEX_Access_&_Advanced_Hedging</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2">
          <PrimeTerminal />
          
          <div className="mt-8 p-6 bg-zinc-900/30 border border-zinc-800 rounded-xl">
            <h3 className="text-xs font-bold uppercase tracking-widest mb-4 flex items-center gap-2">
              <Info size={16} className="text-blue-400" />
              Prime_Brokerage_Overview
            </h3>
            <div className="space-y-4 text-[11px] text-zinc-400 leading-relaxed">
              <p>
                Kerne Prime provides institutional partners with a dedicated sub-account on our partner exchanges (Binance, Bybit, OKX). 
                This allows for direct execution of delta-neutral strategies while maintaining the security of the Kerne Vault infrastructure.
              </p>
              <p>
                <span className="text-white font-bold">SaaS Model:</span> Unlike retail vaults, Prime accounts operate on a fixed 0.50% annual fee, 
                allowing institutions to retain 100% of the generated yield beyond the base protocol costs.
              </p>
              <ul className="list-disc pl-4 space-y-2">
                <li>Direct API access for custom hedging logic.</li>
                <li>Isolated sub-account collateral management.</li>
                <li>Real-time execution monitoring and reporting.</li>
                <li>Priority support and bespoke risk parameter configuration.</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="lg:col-span-1 space-y-6">
          <div className="p-6 bg-blue-600/10 border border-blue-500/30 rounded-xl">
            <h3 className="text-xs font-bold uppercase tracking-widest mb-4 text-blue-400">Onboarding_Status</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">KYB_Verification</span>
                <span className="text-[10px] text-emerald-500 font-bold uppercase">Verified</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">Sub-Account_ID</span>
                <span className="text-[10px] text-zinc-300 font-mono">KP-8829-X</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">API_Access</span>
                <span className="text-[10px] text-emerald-500 font-bold uppercase">Active</span>
              </div>
            </div>
            <button className="w-full mt-6 py-3 bg-blue-600 text-white text-[10px] font-bold uppercase tracking-widest hover:bg-blue-500 transition-all">
              DOWNLOAD_API_KEYS
            </button>
          </div>

          <div className="p-6 bg-zinc-900/30 border border-zinc-800 rounded-xl">
            <h3 className="text-xs font-bold uppercase tracking-widest mb-4 text-zinc-300">Risk_Parameters</h3>
            <div className="space-y-4">
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">Max_Leverage</span>
                <span className="text-[10px] text-zinc-300">3.0x</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">Liquidation_Buffer</span>
                <span className="text-[10px] text-zinc-300">20%</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-[10px] text-zinc-500 uppercase">Auto-Deleverage</span>
                <span className="text-[10px] text-emerald-500 font-bold uppercase">Enabled</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
