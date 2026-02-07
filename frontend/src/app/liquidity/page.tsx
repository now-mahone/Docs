// Created: 2025-12-28
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Shield, Droplets, Zap, Activity } from 'lucide-react';

export default function LiquidityPage() {
  return (
    <main className="min-h-screen bg-[#f9f9f4] text-[#191919] p-8 font-sans selection:bg-[#4c7be7]/20">
      <header className="max-w-7xl mx-auto mb-16 border-b border-[#f1f1ed] pb-8 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link href="/terminal" className="text-[#191919] opacity-40 hover:opacity-100 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <h1 className=" font-heading font-medium tracking-tight text-[#000000]">Liquidity Protocol</h1>
        </div>
        <div className="px-4 py-1.5 bg-[#4c7be7]/5 border border-[#4c7be7]/10 rounded-full text-xs font-bold text-[#4c7be7]">
          Aerodrome Integration
        </div>
      </header>

      <div className="max-w-7xl mx-auto space-y-8">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <div className="md:col-span-2 bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
             <h2 className=" font-heading font-medium mb-6 text-[#000000]">kUSD / USDC Pool</h2>
             <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 mb-8">
                <div className="p-6 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                  <div className="text-xs font-bold text-[#191919] opacity-40 uppercase mb-2">Total Pool TVL</div>
                  <div className="text-xl font-heading font-medium text-[#000000]">$0.00</div>
                </div>
                <div className="p-6 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                  <div className="text-xs font-bold text-[#191919] opacity-40 uppercase mb-2">My Liquidity</div>
                  <div className="text-xl font-heading font-medium text-[#000000]">$0.00</div>
                </div>
             </div>
             <button className="w-full py-4 bg-[#4c7be7] text-[#ffffff] font-bold rounded-full hover:bg-[#0d33ec] transition-all shadow-md">
                Add Liquidity via Aerodrome
             </button>
          </div>

          <div className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
             <h2 className=" font-heading font-medium mb-6 text-[#000000]">Statistics</h2>
             <div className="space-y-6">
                <div className="flex justify-between items-center text-s font-medium">
                   <div className="flex items-center gap-3">
                      <Zap size={16} className="text-[#4c7be7]" />
                      <span className="text-[#191919] opacity-60 font-medium">Trading APR</span>
                   </div>
                   <span className="text-[#4c7be7] font-bold">42.8%</span>
                </div>
                <div className="flex justify-between items-center text-s font-medium">
                   <div className="flex items-center gap-3">
                      <Activity size={16} className="text-[#4c7be7]" />
                      <span className="text-[#191919] opacity-60 font-medium">Vol (24h)</span>
                   </div>
                   <span className="text-[#000000] font-bold">$12,482</span>
                </div>
             </div>
          </div>
        </div>
      </div>
    </main>
  );
}
