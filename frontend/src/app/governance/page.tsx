// Created: 2025-12-28
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Shield, Landmark, Scale, Gavel } from 'lucide-react';

export default function GovernancePage() {
  return (
    <main className="min-h-screen bg-[#f9f9f4] text-[#191919] p-8 font-sans selection:bg-[#4c7be7]/20">
      <header className="max-w-7xl mx-auto mb-16 border-b border-[#f1f1ed] pb-8 flex justify-between items-center">
        <div className="flex items-center gap-6">
          <Link href="/terminal" className="text-[#191919] opacity-40 hover:opacity-100 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <h1 className=" font-heading font-medium tracking-tight text-[#000000]">Governance Hub</h1>
        </div>
        <div className="px-4 py-1.5 bg-[#4c7be7]/5 border border-[#4c7be7]/10 rounded-full text-xs font-bold text-[#4c7be7]">
          $KERNE Holders
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <section className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
            <h2 className=" font-heading font-medium mb-6 text-[#000000]">Active Proposals</h2>
            <div className="space-y-4">
              <div className="p-6 border border-[#f1f1ed] rounded-sm flex items-center justify-between">
                <div>
                   <div className="text-xs font-bold text-[#4c7be7] uppercase tracking-tight mb-1">KIP-001</div>
                   <div className="text-s font-bold text-[#000000]">Initial Fee Structure Activation</div>
                </div>
                <div className="px-3 py-1 bg-[#f9f9f4] border border-[#f1f1ed] rounded-full text-xs font-bold text-[#191919] opacity-40 uppercase">
                   Simulated
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="lg:col-span-1 space-y-8">
          <section className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
             <h2 className=" font-heading font-medium mb-6 text-[#000000]">Staking Overview</h2>
             <div className="space-y-6 mb-8">
                <div className="p-4 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                   <div className="text-xs font-bold text-[#191919] opacity-40 uppercase">My Staked $KERNE</div>
                   <div className="text-xl font-heading font-medium text-[#000000] mt-1">0.00</div>
                </div>
                <div className="p-4 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                   <div className="text-xs font-bold text-[#191919] opacity-40 uppercase">Voting Power</div>
                   <div className="text-xl font-heading font-medium text-[#000000] mt-1">0.00%</div>
                </div>
             </div>
             <button className="w-full py-4 bg-[#4c7be7] text-[#ffffff] font-bold rounded-full hover:bg-[#0d33ec] transition-all shadow-md">
                Stake $KERNE
             </button>
          </section>
        </div>
      </div>
    </main>
  );
}
