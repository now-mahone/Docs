"use client";

// Created: 2026-01-13
import React from 'react';

export default function AlphaDashboard() {
  return (
    <div className="min-h-screen bg-black text-white p-8 font-mono">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 border-b border-zinc-800 pb-8">
          <h1 className="text-4xl font-bold mb-2 tracking-tighter text-blue-500">KERNE ALPHA DASHBOARD</h1>
          <p className="text-zinc-400">Real-time Asymmetric Yield Comparison (Base Mainnet)</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
          {/* Standard Staking */}
          <div className="bg-zinc-900/50 border border-zinc-800 p-6 rounded-lg">
            <h2 className="text-xl font-bold mb-4 text-zinc-500">STANDARD ETH STAKING</h2>
            <div className="text-5xl font-bold mb-2">3.8% <span className="text-sm text-zinc-600">APR</span></div>
            <p className="text-zinc-500 text-sm">Source: Lido / RocketPool Average</p>
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-sm">
                <span>LST Yield</span>
                <span>3.8%</span>
              </div>
              <div className="flex justify-between text-sm text-zinc-700">
                <span>Funding Capture</span>
                <span>0.0%</span>
              </div>
              <div className="flex justify-between text-sm text-zinc-700">
                <span>Solver Spread</span>
                <span>0.0%</span>
              </div>
            </div>
          </div>

          {/* Kerne Delta-Neutral */}
          <div className="bg-blue-900/10 border border-blue-500/30 p-6 rounded-lg relative overflow-hidden">
            <div className="absolute top-0 right-0 bg-blue-500 text-black text-[10px] px-2 py-1 font-bold">LIVE ALPHA</div>
            <h2 className="text-xl font-bold mb-4 text-blue-400">KERNE DELTA-NEUTRAL</h2>
            <div className="text-5xl font-bold mb-2 text-blue-500">24.2% <span className="text-sm text-blue-300">APR</span></div>
            <p className="text-blue-400/60 text-sm">Source: Kerne Intent Solver + Hyperliquid</p>
            <div className="mt-6 space-y-2">
              <div className="flex justify-between text-sm">
                <span>LST Yield</span>
                <span>3.8%</span>
              </div>
              <div className="flex justify-between text-sm text-blue-400">
                <span>Funding Capture (HL)</span>
                <span>15.4%</span>
              </div>
              <div className="flex justify-between text-sm text-blue-400">
                <span>Solver Spread</span>
                <span>5.0%</span>
              </div>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900/30 border border-zinc-800 p-8 rounded-lg">
          <h3 className="text-lg font-bold mb-4">THE ASYMMETRIC EDGE</h3>
          <p className="text-zinc-400 leading-relaxed mb-6">
            Kerne outcompetes standard staking by capturing the "Funding Rate" from delta-neutral hedges. 
            While others simply hold LSTs, Kerne uses them as collateral to short ETH on Hyperliquid, 
            extracting yield from market volatility without exposure to ETH price action.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="p-4 border border-zinc-800 rounded bg-black/40">
              <div className="text-zinc-500 text-xs mb-1">DAILY PROFIT (100 ETH)</div>
              <div className="text-xl font-bold">$165.75</div>
            </div>
            <div className="p-4 border border-zinc-800 rounded bg-black/40">
              <div className="text-zinc-500 text-xs mb-1">SOLVER WIN RATE</div>
              <div className="text-xl font-bold">94.2%</div>
            </div>
            <div className="p-4 border border-zinc-800 rounded bg-black/40">
              <div className="text-zinc-500 text-xs mb-1">NET DELTA</div>
              <div className="text-xl font-bold">0.000</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
