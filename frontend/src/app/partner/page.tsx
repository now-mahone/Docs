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
    <div className="min-h-screen bg-[#191919] text-[#19b097] font-sans p-8 md:p-24 selection:bg-[#4c7be7]/20">
      <div className="max-w-4xl mx-auto border border-[#37bf8d]/20 p-8 bg-[#000000] shadow-2xl rounded-sm">
        <header className="mb-12 border-b border-[#37bf8d]/20 pb-4">
          <h1 className=" font-heading font-medium tracking-tighter uppercase text-[#ffffff]">
            Kerne Infrastructure-as-a-Service
          </h1>
          <p className="text-[#ffffff] opacity-40 mt-2 font-bold text-xs uppercase tracking-widest">
            [SYSTEM STATUS: OPERATIONAL] [VERSION: 1.0.4]
          </p>
        </header>

        <section className="space-y-8">
          <div className="flex flex-col md:flex-row justify-between items-start gap-6">
            <div className="flex-1">
              <h2 className=" font-heading font-medium mb-4 text-[#ffffff]">
                {">"} The White-Label Solution
              </h2>
              <p className="text-[#ffffff] opacity-60 leading-relaxed font-medium">
                Deploy your own institutional-grade delta neutral vault in minutes.
                Kerne provides the smart contracts, the hedging engine, and the
                real time monitoring infrastructure. You provide the capital and
                the brand.
              </p>
            </div>
            <div className="w-full md:w-auto">
              <a 
                href="/docs/white_label_pitch_v2.md" 
                download
                className="inline-block border border-[#19b097] text-[#19b097] px-6 py-3 text-s hover:bg-[#19b097] hover:text-[#000000] transition-all uppercase font-bold tracking-widest rounded-full"
              >
                Download Pitch Deck
              </a>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="border border-[#1f1f1f] p-8 bg-[#191919] rounded-sm shadow-lg">
              <h3 className=" font-heading font-medium mb-2 text-[#37bf8d]">Setup Fee</h3>
              <p className="text-xl font-heading font-medium text-[#ffffff]">$5,000</p>
              <p className="text-xs text-[#ffffff] opacity-20 mt-2 uppercase font-bold tracking-tight">One-time deployment cost</p>
              <button className="mt-6 w-full border border-[#19b097]/30 text-[#19b097] py-2 text-xs font-bold hover:bg-[#19b097]/10 transition-colors uppercase rounded-sm">
                PAY VIA kUSD
              </button>
            </div>
            <div className="border border-[#1f1f1f] p-8 bg-[#191919] rounded-sm shadow-lg">
              <h3 className=" font-heading font-medium mb-2 text-[#37bf8d]">Performance Fee</h3>
              <p className="text-xl font-heading font-medium text-[#ffffff]">15%</p>
              <p className="text-xs text-[#ffffff] opacity-20 mt-2 uppercase font-bold tracking-tight">On generated yield only</p>
            </div>
            <div className="border border-[#1f1f1f] p-8 bg-[#191919] rounded-sm shadow-lg">
              <h3 className=" font-heading font-medium mb-2 text-[#37bf8d]">Min. TVL</h3>
              <p className="text-xl font-heading font-medium text-[#ffffff]">$1M+</p>
              <p className="text-xs text-[#ffffff] opacity-20 mt-2 uppercase font-bold tracking-tight">Target for white-label</p>
            </div>
          </div>

          <div className="border border-[#37bf8d]/20 p-8 bg-[#191919]/50 rounded-sm">
            <h2 className=" font-heading font-medium mb-6 text-[#ffffff]">
              {">"} Revenue Simulator
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              <div className="space-y-6">
                <div>
                  <label className="block text-xs text-[#ffffff] opacity-40 mb-2 uppercase font-bold tracking-widest">Target TVL ($)</label>
                  <input 
                    type="range" min="100000" max="10000000" step="100000"
                    value={simTvl} onChange={(e) => setSimTvl(Number(e.target.value))}
                    className="w-full accent-[#37bf8d]"
                  />
                  <div className="text-xl font-heading font-medium mt-2 text-[#ffffff]">${simTvl.toLocaleString()}</div>
                </div>
                <div>
                  <label className="block text-xs text-[#ffffff] opacity-40 mb-2 uppercase font-bold tracking-widest">Expected APY (%)</label>
                  <input 
                    type="range" min="1" max="30" step="0.5"
                    value={simApy} onChange={(e) => setSimApy(Number(e.target.value))}
                    className="w-full accent-[#37bf8d]"
                  />
                  <div className="text-xl font-heading font-medium mt-2 text-[#ffffff]">{simApy}%</div>
                </div>
              </div>
              <div className="bg-[#000000] p-6 border border-[#1f1f1f] space-y-4 rounded-sm">
                <div className="flex justify-between items-center text-s font-medium">
                  <span className="text-[#ffffff] opacity-40">Gross Annual Profit</span>
                  <span className="text-[#ffffff] font-bold">${annualProfit.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
                <div className="flex justify-between items-center text-s font-medium">
                  <span className="text-[#ffffff] opacity-40">Kerne Infrastructure Fee (15%)</span>
                  <span className="text-[#0d33ec]">-${kerneFee.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
                <div className="pt-4 border-t border-[#1f1f1f] flex justify-between items-center">
                  <span className="text-[#19b097] font-bold">Net Partner Revenue</span>
                  <span className="text-xl font-heading font-medium text-[#ffffff]">${partnerShare.toLocaleString(undefined, {maximumFractionDigits: 0})}</span>
                </div>
              </div>
            </div>
          </div>

          <div>
            <h2 className=" font-heading font-medium mb-4 text-[#ffffff]">
              {">"} Included Infrastructure
            </h2>
            <ul className="list-none space-y-3 text-[#ffffff] opacity-60 font-medium">
              <li className="flex items-center gap-2">[+] <span className="opacity-100">Custom ERC-4626 Vault Deployment</span></li>
              <li className="flex items-center gap-2">[+] <span className="opacity-100">Dedicated Python Hedging Instance</span></li>
              <li className="flex items-center gap-2">[+] <span className="opacity-100">Real-time Discord/Telegram Alerts</span></li>
              <li className="flex items-center gap-2">[+] <span className="opacity-100">Transparency Dashboard Integration</span></li>
              <li className="flex items-center gap-2">[+] <span className="opacity-100">24/7 Technical Support</span></li>
            </ul>
          </div>

          <div className="mt-12 pt-12 border-t border-[#1f1f1f]">
            <h2 className=" font-heading font-medium mb-8 text-[#ffffff]">
              {">"} Request Onboarding
            </h2>
            <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <input 
                  type="text" 
                  placeholder="INSTITUTION NAME" 
                  className="bg-[#191919] border border-[#1f1f1f] p-4 text-[#ffffff] focus:border-[#19b097] outline-none rounded-sm font-sans font-medium"
                />
                <input 
                  type="email" 
                  placeholder="CONTACT EMAIL" 
                  className="bg-[#191919] border border-[#1f1f1f] p-4 text-[#ffffff] focus:border-[#19b097] outline-none rounded-sm font-sans font-medium"
                />
              </div>
              <textarea 
                placeholder="DEPLOYMENT REQUIREMENTS / TARGET TVL" 
                rows={4}
                className="w-full bg-[#191919] border border-[#1f1f1f] p-4 text-[#ffffff] focus:border-[#19b097] outline-none rounded-sm font-sans font-medium"
              ></textarea>
              <button 
                type="submit"
                className="w-full bg-[#19b097] text-[#ffffff] px-8 py-5 font-bold hover:bg-[#37bf8d] transition-all uppercase tracking-widest rounded-full text-s shadow-lg"
              >
                Submit Infrastructure Request
              </button>
            </form>
            <p className="text-xs text-[#ffffff] opacity-20 mt-6 font-bold uppercase tracking-widest text-center">
              * All requests are routed to our institutional desk for manual review.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}
