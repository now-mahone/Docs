"use client";

import React from "react";

// Created: 2025-12-29

export default function PartnerPortal() {
  const [simTvl, setSimTvl] = React.useState(1000000);
  const [simApy, setSimApy] = React.useState(12.5);

  const annualProfit = simTvl * (simApy / 100);
  const partnerShare = annualProfit * 0.85; // 15% performance fee
  const kerneFee = annualProfit * 0.15;

  return (
    <div className="min-h-screen bg-black text-green-500 font-mono p-8 md:p-24">
      <div className="max-w-4xl mx-auto border border-green-900 p-8 bg-zinc-950 shadow-2xl">
        <header className="mb-12 border-b border-green-900 pb-4">
          <h1 className="text-4xl font-bold tracking-tighter uppercase">
            Kerne Infrastructure-as-a-Service
          </h1>
          <p className="text-zinc-500 mt-2">
            [SYSTEM STATUS: OPERATIONAL] [VERSION: 1.0.4]
          </p>
        </header>

        <section className="space-y-8">
          <div className="flex flex-col md:flex-row justify-between items-start gap-6">
            <div className="flex-1">
              <h2 className="text-2xl font-semibold mb-4 text-white">
                {">"} The White-Label Solution
              </h2>
              <p className="text-zinc-400 leading-relaxed">
                Deploy your own institutional-grade delta-neutral vault in minutes. 
                Kerne provides the smart contracts, the hedging engine, and the 
                real-time monitoring infrastructure. You provide the capital and 
                the brand.
              </p>
            </div>
            <div className="w-full md:w-auto">
              <a 
                href="/docs/white_label_pitch_v2.md" 
                download
                className="inline-block border border-green-500 text-green-500 px-6 py-3 text-sm hover:bg-green-500 hover:text-black transition-all uppercase font-bold tracking-widest"
              >
                Download Pitch Deck (PDF)
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="border border-zinc-800 p-6 bg-black">
              <h3 className="text-xl font-bold mb-2 text-green-400">Setup Fee</h3>
              <p className="text-3xl font-bold text-white">$5,000</p>
              <p className="text-xs text-zinc-500 mt-2">One-time deployment cost</p>
              <button className="mt-4 w-full border border-green-900 py-2 text-xs hover:bg-green-900 transition-colors">
                PAY VIA kUSD
              </button>
            </div>
            <div className="border border-zinc-800 p-6 bg-black">
              <h3 className="text-xl font-bold mb-2 text-green-400">Performance Fee</h3>
              <p className="text-3xl font-bold text-white">15%</p>
              <p className="text-xs text-zinc-500 mt-2">On generated yield only</p>
            </div>
            <div className="border border-zinc-800 p-6 bg-black">
              <h3 className="text-xl font-bold mb-2 text-green-400">Min. TVL</h3>
              <p className="text-3xl font-bold text-white">$1M</p>
              <p className="text-xs text-zinc-500 mt-2">Target for white-label</p>
            </div>
          </div>

          <div className="border border-green-900 p-8 bg-zinc-950/50">
            <h2 className="text-2xl font-semibold mb-6 text-white">
              {">"} Revenue Simulator
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              <div className="space-y-6">
                <div>
                  <label className="block text-xs text-zinc-500 mb-2 uppercase">Target TVL ($)</label>
                  <input 
                    type="range" min="100000" max="10000000" step="100000"
                    value={simTvl} onChange={(e) => setSimTvl(Number(e.target.value))}
                    className="w-full accent-green-500"
                  />
                  <div className="text-xl font-bold mt-2">${simTvl.toLocaleString()}</div>
                </div>
                <div>
                  <label className="block text-xs text-zinc-500 mb-2 uppercase">Expected APY (%)</label>
                  <input 
                    type="range" min="1" max="30" step="0.5"
                    value={simApy} onChange={(e) => setSimApy(Number(e.target.value))}
                    className="w-full accent-green-500"
                  />
                  <div className="text-xl font-bold mt-2">{simApy}%</div>
                </div>
              </div>
              <div className="bg-black p-6 border border-zinc-800 space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 text-sm">Gross Annual Profit</span>
                  <span className="text-white font-bold">${annualProfit.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-zinc-500 text-sm">Kerne Infrastructure Fee (15%)</span>
                  <span className="text-red-900">-${kerneFee.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
                <div className="pt-4 border-t border-zinc-800 flex justify-between items-center">
                  <span className="text-green-400 font-bold">Net Partner Revenue</span>
                  <span className="text-2xl font-bold text-white">${partnerShare.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h2 className="text-2xl font-semibold mb-4 text-white">
              {">"} Included Infrastructure
            </h2>
            <ul className="list-none space-y-2 text-zinc-400">
              <li>[+] Custom ERC-4626 Vault Deployment</li>
              <li>[+] Dedicated Python Hedging Instance</li>
              <li>[+] Real-time Discord/Telegram Alerts</li>
              <li>[+] Transparency Dashboard Integration</li>
              <li>[+] 24/7 Technical Support</li>
            </ul>
          </div>

          <div className="mt-12 pt-8 border-t border-green-900">
            <h2 className="text-2xl font-semibold mb-6 text-white">
              {">"} Request Onboarding
            </h2>
            <form className="space-y-4" onSubmit={(e) => e.preventDefault()}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <input 
                  type="text" 
                  placeholder="INSTITUTION NAME" 
                  className="bg-black border border-zinc-800 p-4 text-green-500 focus:border-green-500 outline-none"
                />
                <input 
                  type="email" 
                  placeholder="CONTACT EMAIL" 
                  className="bg-black border border-zinc-800 p-4 text-green-500 focus:border-green-500 outline-none"
                />
              </div>
              <textarea 
                placeholder="DEPLOYMENT REQUIREMENTS / TARGET TVL" 
                rows={4}
                className="w-full bg-black border border-zinc-800 p-4 text-green-500 focus:border-green-500 outline-none"
              ></textarea>
              <button 
                type="submit"
                className="w-full bg-green-600 text-black px-8 py-4 font-bold hover:bg-green-400 transition-colors uppercase tracking-widest"
              >
                Submit Infrastructure Request
              </button>
            </form>
            <p className="text-xs text-zinc-600 mt-4">
              * All requests are routed to our institutional desk for manual review.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
