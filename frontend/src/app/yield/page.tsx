"use client";

import { Shield, Zap, TrendingUp, ArrowRight } from "lucide-react";
import Link from "next/link";

// Created: 2026-01-04
// SEO-optimized landing page for organic yield discovery

export default function YieldComparisonPage() {
  const competitors = [
    { name: "Lido (stETH)", apy: "3.2%", risk: "Low", type: "LST" },
    { name: "Rocket Pool (rETH)", apy: "2.9%", risk: "Low", type: "LST" },
    { name: "Aave (WETH)", apy: "1.8%", risk: "Minimal", type: "Lending" },
    { name: "Kerne (kLP)", apy: "12.4%", risk: "Institutional", type: "Delta Neutral" },
  ];

  return (
    <div className="min-h-screen bg-[#f9f9f4] text-[#191919] font-sans p-8 pt-24 selection:bg-[#4c7be7]/20">
      <div className="max-w-4xl mx-auto">
        <div className="mb-16 text-center">
          <h1 className=" font-heading font-medium mb-6 tracking-tighter text-[#000000] uppercase">
            The Yield Gap
          </h1>
          <p className="text-[#191919] opacity-60 text-l max-w-2xl mx-auto font-medium">
            Why settle for 3% when the market offers 12%? Kerne captures the delta neutral
            basis that institutional desks have traded for decades.
          </p>
        </div>

        <div className="grid gap-4 mb-16">
          {competitors.map((c, i) => (
            <div key={i} className={`p-6 border ${c.name === 'Kerne (kLP)' ? 'border-[#37bf8d] bg-[#ebf9f4]' : 'border-[#f1f1ed] bg-[#ffffff]'} rounded-sm flex items-center justify-between shadow-sm`}>
              <div>
                <div className="text-s text-[#191919] opacity-40 mb-1 font-bold">{c.type}</div>
                <div className="text-xl font-heading font-medium text-[#000000]">{c.name}</div>
              </div>
              <div className="text-right">
                <div className={`text-xl font-heading font-medium ${c.name === 'Kerne (kLP)' ? 'text-[#19b097]' : 'text-[#191919] opacity-60'}`}>
                  {c.apy} APY
                </div>
                <div className="text-xs text-[#191919] opacity-40 font-bold uppercase tracking-widest">Risk: {c.risk}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="p-8 bg-[#ffffff] border border-[#f1f1ed] rounded-sm shadow-sm">
            <Shield className="text-[#4c7be7] mb-6 w-8 h-8" />
            <h3 className="font-heading font-medium mb-3 uppercase text-[#000000]">Delta Neutral</h3>
            <p className="text-s text-[#191919] opacity-60 font-medium leading-relaxed">No exposure to ETH price volatility. We hedge 100% of the collateral.</p>
          </div>
          <div className="p-8 bg-[#ffffff] border border-[#f1f1ed] rounded-sm shadow-sm">
            <Zap className="text-[#4c7be7] mb-6 w-8 h-8" />
            <h3 className="font-heading font-medium mb-3 uppercase text-[#000000]">Funding Capture</h3>
            <p className="text-s text-[#191919] opacity-60 font-medium leading-relaxed">We collect funding rates from over-leveraged long positions on CEXs.</p>
          </div>
          <div className="p-8 bg-[#ffffff] border border-[#f1f1ed] rounded-sm shadow-sm">
            <TrendingUp className="text-[#19b097] mb-6 w-8 h-8" />
            <h3 className="font-heading font-medium mb-3 uppercase text-[#000000]">Auto-Compound</h3>
            <p className="text-s text-[#191919] opacity-60 font-medium leading-relaxed">Yield is automatically harvested and reinvested into the strategy.</p>
          </div>
        </div>

        <div className="text-center">
          <Link href="/terminal" className="inline-flex items-center gap-3 bg-[#4c7be7] text-[#ffffff] px-10 py-5 rounded-full font-bold hover:bg-[#0d33ec] transition-all shadow-lg text-s">
            Launch Terminal <ArrowRight className="w-5 h-5" />
          </Link>
        </div>
      </div>
    </div>
  );
}
