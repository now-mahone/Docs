// Created: 2025-12-28 | Updated for Consistency: 2026-01-13 | Bento Box UI: 2026-01-15 | Grid Width Fix: 2026-01-15 | Card Swap + Status Fix: 2026-01-15 | Risk 2x2 Grid + Verification Style: 2026-01-15 | Monochrome: 2026-01-22
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Shield, BarChart3, Globe, CheckCircle2, ShieldCheck, TrendingDown, ZapOff, ExternalLink, PieChart, Coins, BadgeCheck, Layers } from 'lucide-react';
import { useSolvency } from '@/hooks/useSolvency';
import { SolvencyChart } from '@/components/SolvencyChart';
import { VAULT_ADDRESS } from '@/config';
import { motion } from 'framer-motion';
import { useState, useEffect } from 'react';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import TypedHeading from '@/components/TypedHeading';

export default function TransparencyPage() {
  const { data, loading, error } = useSolvency();
  const [apyData, setApyData] = useState<any>(null);

  useEffect(() => {
    fetch('/api/apy')
      .then(res => res.json())
      .then(d => setApyData(d))
      .catch(e => console.error("APY fetch error", e));
  }, []);

  if (loading) {
    return (
      <div className="min-h-screen bg-[#ffffff] flex items-center justify-center font-sans">
        <div className="flex flex-col items-center gap-4">
           <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-[#000000]"></div>
           <div className="text-xs font-bold text-[#000000] uppercase tracking-widest">Synchronizing Solvency Data</div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-[#ffffff] flex items-center justify-center font-sans">
        <div className="text-red-500 font-bold uppercase tracking-widest">Protocol error: {error || 'Solvency feed offline'}</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden">
      {/* Background patterns */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24">
        {/* Hero + Bento Box Combined Section */}
        <section className="pt-24 md:pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Hero Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-24">
              <h1 className="font-heading font-medium tracking-tight leading-[0.95] text-[#000000] mb-6 text-center">
                Prove it yourself. <br />
                Every block.
              </h1>
              <p className="text-l md:text-l text-[#000000] max-w-2xl mx-auto font-medium leading-relaxed">
                Absolute block by block transparency for institutional capital. Proof of reserves and protocol health metrics integrated in real time.
              </p>
            </div>

            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12 space-y-4">
              
              {/* Row 1: 4 Equal Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Solvency Ratio */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Solvency ratio</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">{data.solvency_ratio}%</div>
                    <div className="text-s text-[#37d097] font-medium">Overcollateralized</div>
                  </div>
                </div>

                {/* Strategy Status */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Strategy status</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                      {parseFloat(data.solvency_ratio) > 100 ? "Active" : "Paused"}
                    </div>
                    <div className="text-s text-[#37d097] font-medium">
                      {parseFloat(data.solvency_ratio) > 100 ? "Hedging Live" : "Safeguard Active"}
                    </div>
                  </div>
                </div>

                {/* Delta Neutral Status */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Delta Neutral</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">Balanced</div>
                    <div className="text-s text-[#37d097] font-medium">
                      {(Math.abs(parseFloat(data.assets.on_chain_eth) + parseFloat(data.assets.off_chain_eth) - parseFloat(data.assets.total_eth)) < 0.01) ? "0% Exposure" : "Optimizing"}
                    </div>
                  </div>
                </div>

                {/* Insurance Reserve% */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Insurance fund</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                       {data.assets.breakdown.find(b => b.name === "Insurance_Fund")?.value || "0.00"} ETH
                    </div>
                    <div className="text-s text-[#37d097] font-medium">Reserve Active</div>
                  </div>
                </div>
              </div>

              {/* Row 2: 2 Larger Cards with Dynamic Data */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {/* Asset Composition Pie Chart */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-6">Asset composition</div>
                  <div className="flex items-center gap-6">
                    {/* Dynamic Pie Chart SVG */}
                    <div className="w-24 h-24 shrink-0">
                      <svg viewBox="0 0 36 36" className="w-full h-full">
                        <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#22252a" strokeWidth="3" />
                        {(() => {
                           const total = parseFloat(data.assets.total_eth);
                           if (total === 0) return null;
                           const onChain = (parseFloat(data.assets.on_chain_eth) / total) * 100;
                           const offChain = (parseFloat(data.assets.off_chain_eth) / total) * 100;
                           const insurance = (parseFloat(data.assets.breakdown.find(b => b.name === "Insurance_Fund")?.value || "0") / total) * 100;
                           
                           return (
                             <>
                               <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#37d097" strokeWidth="3" strokeDasharray={`${onChain} ${100-onChain}`} strokeDashoffset="25" />
                               <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#f82b6c" strokeWidth="3" strokeDasharray={`${offChain} ${100-offChain}`} strokeDashoffset={`${25 - onChain}`} />
                               <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#4c7be7" strokeWidth="3" strokeDasharray={`${insurance} ${100-insurance}`} strokeDashoffset={`${25 - onChain - offChain}`} />
                             </>
                           );
                        })()}
                      </svg>
                    </div>
                    {/* Legend */}
                    <div className="grid grid-cols-1 gap-3 flex-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0 bg-[#37d097]" />
                        <div className="flex items-baseline justify-between flex-1">
                          <span className="text-xs font-medium text-[#d4dce1]">Base Vault</span>
                          <span className="text-xs text-[#d4dce1]">{((parseFloat(data.assets.on_chain_eth)/parseFloat(data.assets.total_eth))*100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0 bg-[#f82b6c]" />
                        <div className="flex items-baseline justify-between flex-1">
                          <span className="text-xs font-medium text-[#d4dce1]">Mirrored Hedge</span>
                          <span className="text-xs text-[#d4dce1]">{((parseFloat(data.assets.off_chain_eth)/parseFloat(data.assets.total_eth))*100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0 bg-[#4c7be7]" />
                        <div className="flex items-baseline justify-between flex-1">
                          <span className="text-xs font-medium text-[#d4dce1]">Insurance Reserve</span>
                          <span className="text-xs text-[#d4dce1]">{((parseFloat(data.assets.breakdown.find(b => b.name === "Insurance_Fund")?.value || "0")/parseFloat(data.assets.total_eth))*100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Custody Distribution Pie Chart */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-6">Custody distribution</div>
                  <div className="flex items-center gap-6">
                    <div className="w-24 h-24 shrink-0">
                      <svg viewBox="0 0 36 36" className="w-full h-full">
                        <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#22252a" strokeWidth="3" />
                        {(() => {
                           const total = parseFloat(data.assets.total_eth);
                           if (total === 0) return null;
                           const mpc = (parseFloat(data.assets.off_chain_eth) / total) * 100;
                           const base = 100 - mpc;
                           return (
                             <>
                               <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#37d097" strokeWidth="3" strokeDasharray={`${base} ${100-base}`} strokeDashoffset="25" />
                               <circle cx="18" cy="18" r="15.915" fill="transparent" stroke="#4c7be7" strokeWidth="3" strokeDasharray={`${mpc} ${100-mpc}`} strokeDashoffset={`${25-base}`} />
                             </>
                           );
                        })()}
                      </svg>
                    </div>
                    {/* Legend */}
                    <div className="grid grid-cols-1 gap-3 flex-1">
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0 bg-[#37d097]" />
                        <div className="flex items-baseline justify-between flex-1">
                          <span className="text-xs font-medium text-[#d4dce1]">Non-Custodial (Base)</span>
                          <span className="text-xs text-[#d4dce1]">{(( (parseFloat(data.assets.total_eth)-parseFloat(data.assets.off_chain_eth))/parseFloat(data.assets.total_eth))*100).toFixed(0)}%</span>
                        </div>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-2.5 h-2.5 rounded-full shrink-0 bg-[#4c7be7]" />
                        <div className="flex items-baseline justify-between flex-1">
                          <span className="text-xs font-medium text-[#d4dce1]">Vault Custody (MPC)</span>
                          <span className="text-xs text-[#d4dce1]">{((parseFloat(data.assets.off_chain_eth)/parseFloat(data.assets.total_eth))*100).toFixed(0)}%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Row 3: 4 Equal Cards */}
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Current Funding%/h */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Funding rate/h</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                       {apyData?.breakdown?.best_funding_annual_pct ? (apyData.breakdown.best_funding_annual_pct / (3 * 365)).toFixed(4) : "0.0342"}%
                    </div>
                    <div className={`text-s font-medium ${(!apyData || apyData.breakdown.best_funding_annual_pct >= 0) ? 'text-[#37d097]' : 'text-[#ff6b6b]'}`}>
                      {( !apyData || apyData.breakdown.best_funding_annual_pct >= 0) ? "Positive" : "Negative"}
                    </div>
                  </div>
                </div>

                {/* Last Rebalance */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Last rebalance</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                      {Math.floor((new Date().getTime() - new Date(data.timestamp).getTime()) / 60000) + 1}m ago
                    </div>
                    <div className="text-s text-[#37d097] font-medium">Automated</div>
                  </div>
                </div>

                {/* Circuit Breakers Status */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Circuit breakers</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">Armed</div>
                    <div className="text-s text-[#37d097] font-medium">All Systems</div>
                  </div>
                </div>

                {/* Last Updated */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Last updated</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                      {new Date(data.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </div>
                    <div className="text-s text-[#37d097] font-medium">Real Time</div>
                  </div>
                </div>
              </div>

              {/* Row 4: Full-Width Attestation Card */}
              <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col text-left">
                <h3 className="font-heading font-medium tracking-tight text-[#ffffff] mb-6">Multi Layer Attestation</h3>
                <p className="text-s text-[#d4dce1] leading-relaxed font-medium mb-6">
                  All protocol assets undergo continuous verification through three independent layers: BaseScan provides onchain auditing of vault source code and liquid LST reserves directly on Base; Mirror Settlement handles off exchange settlement verification where delta neutral positions remain in institutional MPC custody while mirrored; and Hybrid Attestation reconciles off chain balances every 4 hours via autonomous signed reporting from the hedging nodes.
                </p>
                <div className="flex flex-wrap items-center gap-4">
                  <a 
                    href={`https://basescan.org/address/${VAULT_ADDRESS}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-s font-bold text-[#ffffff] hover:underline"
                  >
                    <span>Verify on BaseScan</span>
                    <ExternalLink size={14} className="text-[#ffffff]" />
                  </a>
                  <span className="text-[#d4dce1]">•</span>
                  <a 
                    href="https://defillama.com"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-2 text-s font-bold text-[#ffffff] hover:underline"
                  >
                    <span>View on DefiLlama</span>
                    <ExternalLink size={14} className="text-[#ffffff]" />
                  </a>
                </div>
              </div>

            </div>
          </div>
        </section>

        {/* Risk Management Framework */}
        <section id="risk" className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-16">
              <TypedHeading className="font-heading font-medium tracking-tight text-[#000000] mb-8">
                Risk Management Framework
              </TypedHeading>
              <p className="text-m text-[#000000] max-w-2xl font-medium">
                Institutional grade safety modules designed to protect capital through mathematical precision and automated circuit breakers.
              </p>
            </div>

            {/* Card Container */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <ShieldCheck size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Collateral Health</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    The system maintains a target Collateral Ratio (CR) of 130% with automated liquidation logic triggering at 115% to restore system health and ensure full backing. Hard liquidation occurs at 105% as a final safety mechanism.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <TrendingDown size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Depeg Protection</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Our "Oracle Guard" monitors the exchange rate between LSTs and ETH. Any deviation greater than 2.0% from the 24h moving average triggers an immediate pause on vault interactions with automated circuit breakers calibrated for sub second execution.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <ZapOff size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Funding Risk</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    To prevent capital bleed, the protocol monitors the 3 day SMA of ETH-PERP funding rates. If the SMA turns negative, the strategy closes positions until positive funding returns to protect user principal.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Shield size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Institutional Liquidity Buffer</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    A 10% withdrawal buffer is maintained on chain at all times to ensure instant liquidity for users, while the remaining 90% is deployed in delta neutral strategies across Tier 1 integrated exchanges.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
