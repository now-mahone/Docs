// Created: 2026-01-06
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Shield, BarChart3, Lock, Zap } from 'lucide-react';
import { motion } from 'framer-motion';

export default function PrimePage() {
  return (
    <main className="min-h-screen bg-[#f9f9f4] text-[#191919] p-8 font-sans selection:bg-[#4c7be7]/20">
      <header className="mb-16 border-b border-[#f1f1ed] pb-8 flex justify-between items-center max-w-7xl mx-auto">
        <div className="flex items-center gap-6">
          <Link href="/terminal" className="text-[#191919] opacity-40 hover:opacity-100 transition-colors">
            <ArrowLeft size={20} />
          </Link>
          <h1 className=" font-heading font-medium tracking-tight text-[#000000]">Prime Brokerage</h1>
        </div>
        <div className="px-4 py-1.5 bg-[#4c7be7]/5 border border-[#4c7be7]/10 rounded-full text-xs font-bold text-[#4c7be7]">
          Institutional Access
        </div>
      </header>

      <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-2 space-y-8">
          <section className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
            <h2 className=" font-heading font-medium mb-6 text-[#000000]">Prime Allocation</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="p-6 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                <div className="text-xs font-bold text-[#191919] opacity-40 uppercase tracking-tight mb-2">Available Liquidity</div>
                <div className="text-xl font-heading font-medium text-[#000000]">0.00 ETH</div>
              </div>
              <div className="p-6 bg-[#f9f9f4] rounded-sm border border-[#f1f1ed]">
                <div className="text-xs font-bold text-[#191919] opacity-40 uppercase tracking-tight mb-2">Active Utilization</div>
                <div className="text-xl font-heading font-medium text-[#000000]">0.00%</div>
              </div>
            </div>
          </section>

          <section className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
            <h2 className=" font-heading font-medium mb-6 text-[#000000]">Active Strategies</h2>
            <div className="space-y-4">
              <div className="p-6 border border-[#f1f1ed] rounded-sm flex items-center justify-between group transition-all">
                <div className="flex items-center gap-4">
                  <div className="w-10 h-10 bg-[#4c7be7]/5 rounded-full flex items-center justify-center text-[#4c7be7] group-hover:bg-[#4c7be7] group-hover:text-[#ffffff] transition-all">
                    <Zap size={20} />
                  </div>
                  <div>
                    <div className="text-s font-bold text-[#000000]">Delta-Neutral Basis</div>
                    <div className="text-xs text-[#191919] opacity-40 font-bold uppercase">Executing on Base / Binance</div>
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-s font-bold text-[#4c7be7]">12.4% APY</div>
                  <div className="text-xs text-[#191919] opacity-40 italic font-bold">Active</div>
                </div>
              </div>
            </div>
          </section>
        </div>

        <div className="lg:col-span-1 space-y-8">
          <section className="bg-[#ffffff] border border-[#f1f1ed] rounded-sm p-8 shadow-sm">
            <h2 className=" font-heading font-medium mb-6 text-[#000000]">Requirements</h2>
            <ul className="space-y-4">
              <li className="flex items-start gap-3">
                <Shield size={16} className="text-[#4c7be7] mt-1" />
                <span className="text-s text-[#191919] opacity-60 font-medium">Minimum allocation of 10 ETH required for Prime access.</span>
              </li>
              <li className="flex items-start gap-3">
                <Lock size={16} className="text-[#4c7be7] mt-1" />
                <span className="text-s text-[#191919] opacity-60 font-medium">Verified institutional wallet (Safe/Fireblocks supported).</span>
              </li>
            </ul>
            <button className="w-full mt-8 py-4 bg-[#4c7be7] text-[#ffffff] font-bold rounded-full hover:bg-[#0d33ec] transition-all shadow-md">
              Apply for Prime
            </button>
          </section>
        </div>
      </div>
    </main>
  );
}
