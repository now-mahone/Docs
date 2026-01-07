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
    { name: "Kerne (kLP)", apy: "12.4%", risk: "Institutional", type: "Delta-Neutral" },
  ];

  return (
    <div className="min-h-screen bg-black text-white font-mono p-8 pt-24">
      <div className="max-w-4xl mx-auto">
        <div className="mb-16 text-center">
          <h1 className="text-5xl font-bold mb-6 tracking-tighter">
            THE_YIELD_GAP
          </h1>
          <p className="text-zinc-400 text-lg max-w-2xl mx-auto">
            Why settle for 3% when the market offers 12%? Kerne captures the delta-neutral 
            basis that institutional desks have traded for decades.
          </p>
        </div>

        <div className="grid gap-4 mb-16">
          {competitors.map((c, i) => (
            <div key={i} className={`p-6 border ${c.name === 'Kerne (kLP)' ? 'border-emerald-500 bg-emerald-500/5' : 'border-zinc-800 bg-zinc-900/30'} rounded-lg flex items-center justify-between`}>
              <div>
                <div className="text-sm text-zinc-500 mb-1">{c.type}</div>
                <div className="text-xl font-bold">{c.name}</div>
              </div>
              <div className="text-right">
                <div className={`text-2xl font-bold ${c.name === 'Kerne (kLP)' ? 'text-emerald-400' : 'text-zinc-300'}`}>
                  {c.apy} APY
                </div>
                <div className="text-xs text-zinc-500">Risk: {c.risk}</div>
              </div>
            </div>
          ))}
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <div className="p-6 border border-zinc-800 rounded-lg">
            <Shield className="text-blue-500 mb-4 w-8 h-8" />
            <h3 className="font-bold mb-2">DELTA_NEUTRAL</h3>
            <p className="text-xs text-zinc-500">No exposure to ETH price volatility. We hedge 100% of the collateral.</p>
          </div>
          <div className="p-6 border border-zinc-800 rounded-lg">
            <Zap className="text-yellow-500 mb-4 w-8 h-8" />
            <h3 className="font-bold mb-2">FUNDING_CAPTURE</h3>
            <p className="text-xs text-zinc-500">We collect funding rates from over-leveraged long positions on CEXs.</p>
          </div>
          <div className="p-6 border border-zinc-800 rounded-lg">
            <TrendingUp className="text-emerald-500 mb-4 w-8 h-8" />
            <h3 className="font-bold mb-2">AUTO_COMPOUND</h3>
            <p className="text-xs text-zinc-500">Yield is automatically harvested and reinvested into the strategy.</p>
          </div>
        </div>

        <div className="text-center">
          <Link href="/terminal" className="inline-flex items-center gap-2 bg-white text-black px-8 py-4 rounded-full font-bold hover:bg-zinc-200 transition-colors">
            ENTER_TERMINAL <ArrowRight className="w-4 h-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
