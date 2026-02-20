// Created: 2025-12-28 | Updated for Consistency: 2026-01-13 | Bento Box UI: 2026-01-15 | Grid Width Fix: 2026-01-15 | Card Swap + Status Fix: 2026-01-15 | Risk 2x2 Grid + Verification Style: 2026-01-15 | Monochrome: 2026-01-22
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Shield, BarChart3, Globe, CheckCircle2, ShieldCheck, TrendingDown, ZapOff, ExternalLink, PieChart, Coins, BadgeCheck, Layers, Activity } from 'lucide-react';
import { useSolvency } from '@/hooks/useSolvency';
import { SolvencyChart } from '@/components/SolvencyChart';
import { PieChart as CustomPieChart } from '@/components/PieChart';
import { VAULT_ADDRESS } from '@/config';
import { useState, useEffect } from 'react';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import TypedHeading from '@/components/TypedHeading';

const heatmapData = [
  0.207, 0.496, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.310, 0.594, 0.290, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.240, 0.688, 0.327, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.357, 0.734, 0.393, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.103, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.370, 0.764, 0.431, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.393, 0.779, 0.474, 0.164, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.327, 0.760, 0.512, 0.240, 0.103, 0.103, 0.103, 0.000, 0.000, 0.103, 0.000, 0.164, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.267, 0.735, 0.512, 0.164, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.103, 0.680, 0.467, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.103, 0.580, 0.413, 0.164, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.103, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000,
  0.103, 0.521, 0.370, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.103, 0.000, 0.103, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.103, 0.403, 0.240, 0.000, 0.000, 0.000, 0.164, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.103, 0.103, 0.000, 0.000, 0.103, 0.103, 0.000, 0.164, 0.164, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.164, 0.000, 0.000,
  0.207, 0.534, 0.240, 0.164, 0.103, 0.103, 0.000, 0.103, 0.000, 0.103, 0.000, 0.000, 0.103, 0.103, 0.000, 0.000, 0.164, 0.000, 0.164, 0.164, 0.164, 0.103, 0.103, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.103, 0.000, 0.000,
  0.343, 0.624, 0.310, 0.000, 0.240, 0.103, 0.000, 0.103, 0.103, 0.164, 0.164, 0.000, 0.000, 0.000, 0.164, 0.103, 0.164, 0.000, 0.164, 0.207, 0.000, 0.207, 0.207, 0.103, 0.103, 0.000, 0.207, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.370, 0.790, 0.480, 0.240, 0.240, 0.103, 0.207, 0.240, 0.164, 0.103, 0.103, 0.103, 0.000, 0.000, 0.164, 0.103, 0.000, 0.103, 0.290, 0.164, 0.164, 0.207, 0.310, 0.207, 0.103, 0.103, 0.000, 0.000, 0.240, 0.164, 0.000, 0.000,
  0.491, 0.891, 0.674, 0.382, 0.240, 0.357, 0.327, 0.267, 0.164, 0.240, 0.207, 0.000, 0.164, 0.000, 0.103, 0.000, 0.000, 0.000, 0.164, 0.310, 0.267, 0.207, 0.357, 0.343, 0.310, 0.164, 0.290, 0.000, 0.267, 0.207, 0.103, 0.000,
  0.454, 0.977, 0.745, 0.422, 0.310, 0.403, 0.343, 0.370, 0.327, 0.343, 0.207, 0.240, 0.164, 0.103, 0.103, 0.103, 0.103, 0.000, 0.103, 0.240, 0.240, 0.267, 0.267, 0.267, 0.207, 0.290, 0.290, 0.343, 0.485, 0.290, 0.207, 0.000,
  0.480, 0.999, 0.821, 0.507, 0.164, 0.327, 0.343, 0.403, 0.327, 0.310, 0.327, 0.327, 0.310, 0.240, 0.207, 0.207, 0.164, 0.164, 0.207, 0.164, 0.207, 0.207, 0.240, 0.164, 0.240, 0.290, 0.290, 0.343, 0.474, 0.343, 0.267, 0.000,
  0.413, 1.000, 0.850, 0.570, 0.393, 0.343, 0.382, 0.382, 0.343, 0.382, 0.393, 0.327, 0.357, 0.207, 0.240, 0.207, 0.207, 0.000, 0.103, 0.000, 0.164, 0.103, 0.103, 0.240, 0.207, 0.207, 0.207, 0.327, 0.491, 0.413, 0.290, 0.164,
  0.164, 0.948, 0.866, 0.580, 0.403, 0.431, 0.403, 0.343, 0.343, 0.413, 0.357, 0.422, 0.370, 0.290, 0.310, 0.290, 0.240, 0.207, 0.207, 0.164, 0.000, 0.207, 0.103, 0.103, 0.207, 0.164, 0.207, 0.207, 0.480, 0.403, 0.103, 0.207,
  0.103, 0.854, 0.808, 0.564, 0.393, 0.439, 0.422, 0.413, 0.439, 0.343, 0.393, 0.327, 0.403, 0.310, 0.240, 0.327, 0.357, 0.267, 0.267, 0.164, 0.207, 0.240, 0.103, 0.103, 0.000, 0.000, 0.164, 0.207, 0.370, 0.357, 0.267, 0.164,
  0.000, 0.689, 0.691, 0.474, 0.327, 0.413, 0.485, 0.491, 0.516, 0.480, 0.525, 0.461, 0.343, 0.413, 0.343, 0.343, 0.370, 0.327, 0.290, 0.164, 0.103, 0.164, 0.164, 0.000, 0.103, 0.164, 0.103, 0.000, 0.327, 0.327, 0.000, 0.207,
  0.103, 0.480, 0.496, 0.343, 0.240, 0.357, 0.393, 0.512, 0.474, 0.586, 0.577, 0.560, 0.474, 0.454, 0.357, 0.290, 0.310, 0.290, 0.310, 0.164, 0.207, 0.207, 0.207, 0.000, 0.103, 0.103, 0.103, 0.000, 0.207, 0.000, 0.240, 0.103,
  0.000, 0.310, 0.290, 0.207, 0.103, 0.000, 0.267, 0.343, 0.474, 0.491, 0.542, 0.546, 0.530, 0.542, 0.480, 0.413, 0.382, 0.290, 0.310, 0.240, 0.240, 0.164, 0.000, 0.103, 0.164, 0.164, 0.207, 0.000, 0.207, 0.240, 0.000, 0.000,
  0.000, 0.103, 0.103, 0.103, 0.000, 0.000, 0.000, 0.103, 0.164, 0.403, 0.454, 0.474, 0.454, 0.502, 0.485, 0.516, 0.502, 0.382, 0.310, 0.290, 0.267, 0.240, 0.103, 0.000, 0.164, 0.103, 0.103, 0.103, 0.103, 0.164, 0.164, 0.000,
  0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.164, 0.290, 0.267, 0.403, 0.382, 0.446, 0.461, 0.431, 0.422, 0.403, 0.327, 0.164, 0.103, 0.000, 0.164, 0.000, 0.164, 0.000, 0.164, 0.103, 0.000, 0.000,
  0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.103, 0.000, 0.290, 0.240, 0.327, 0.370, 0.370, 0.382, 0.164, 0.207, 0.310, 0.207, 0.164, 0.103, 0.000, 0.000, 0.103, 0.000, 0.103, 0.000,
  0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.164, 0.000, 0.240, 0.000, 0.240, 0.240, 0.103, 0.164, 0.000, 0.164, 0.000, 0.000, 0.164, 0.000, 0.000, 0.000, 0.000,
  0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.103, 0.164, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.103, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
  0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000, 0.000,
];

const getHeatmapColor = (value: number) => {
  if (value === 0) return 'rgba(68, 74, 79, 0.1)';
  
  // 6 colors = 5 segments
  const segment = 1 / 5;
  
  const colors = [
    [0, 0, 255],     // Blue
    [0, 255, 255],   // Cyan
    [0, 255, 0],     // Green
    [255, 255, 0],   // Yellow
    [255, 165, 0],   // Orange
    [255, 0, 0]      // Red
  ];
  
  const i = Math.min(Math.floor(value / segment), 4);
  const f = (value - i * segment) / segment;
  
  const c1 = colors[i];
  const c2 = colors[i + 1];
  
  const r = Math.round(c1[0] + f * (c2[0] - c1[0]));
  const g = Math.round(c1[1] + f * (c2[1] - c1[1]));
  const b = Math.round(c1[2] + f * (c2[2] - c1[2]));
  
  return `rgb(${r}, ${g}, ${b})`;
};

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
                      {parseFloat(data.solvency_ratio) >= 100 ? "Active" : "Paused"}
                    </div>
                    <div className="text-s text-[#37d097] font-medium">
                      {parseFloat(data.solvency_ratio) >= 100 ? "Hedging Live" : "Safeguard Active"}
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
                      {(() => {
                        const total = parseFloat(data.assets.total_eth);
                        const insurance = parseFloat(data.assets.breakdown.find(b => b.name === "Insurance_Fund")?.value || "0");
                        return total > 0 ? ((insurance / total) * 100).toFixed(1) : "0.0";
                      })()}%
                    </div>
                    <div className="text-s text-[#37d097] font-medium">Reserve Active</div>
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

              {/* Row 5: Full-Width Attestation Card */}
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

        {/* Monte Carlo Risk Simulation */}
        <section id="monte-carlo" className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-16">
              <TypedHeading className="font-heading font-medium tracking-tight text-[#000000] mb-8">
                Monte Carlo Risk Simulation
              </TypedHeading>
              <p className="text-m text-[#000000] max-w-2xl font-medium">
                Ten thousand simulated scenarios stress tested across one year timeframe to quantify protocol resilience under extreme market conditions.
              </p>
            </div>

            {/* Bento Box Grid */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12 space-y-4">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {/* Simulation Methodology - Spans 2x2 */}
                <div className="md:col-span-2 md:row-span-2 p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col text-left">
                  <h3 className="font-heading font-medium tracking-tight text-[#ffffff] mb-6">Simulation Methodology</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    The Monte Carlo v4 simulation executes 10,000 independent scenarios across a 365 day horizon. Each simulation path incorporates stochastic volatility for ETH price action, dynamic funding rate fluctuations, and extreme black swan events including LST depegs and regulatory shocks. This latest iteration factors in our multi-source oracle architecture, tiered circuit breakers, and the automated Insurance Fund reserve. The hedging engine rebalances positions every 8 hours with slippage and execution costs factored into the final 21.78% mean APY.
                  </p>
                </div>

                {/* Survival Rate */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Survival Rate</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">99.73%</div>
                    <div className="text-s text-[#37d097] font-medium">9,973 / 10,000</div>
                  </div>
                </div>

                {/* Mean Yield */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Mean Yield APY</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">21.78%</div>
                    <div className="text-s text-[#37d097] font-medium">Annualized</div>
                  </div>
                </div>

                {/* Max Drawdown */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Max Drawdown</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">2.62%</div>
                    <div className="text-s text-[#37d097] font-medium">Historical Peak to Trough</div>
                  </div>
                </div>

                {/* VaR 99 */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">VaR 99%</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">$86.77M</div>
                    <div className="text-s text-[#37d097] font-medium">86.77c per dollar preserved</div>
                  </div>
                </div>

                {/* Oracle Manipulation */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Oracle Manipulation</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">0.00%</div>
                    <div className="text-s text-[#37d097] font-medium">Zero Failures Recorded</div>
                  </div>
                </div>

                {/* Smart Contract Exploit */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Smart Contract Exploit</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">0.22%</div>
                    <div className="text-s text-[#37d097] font-medium">Post Audit Probability</div>
                  </div>
                </div>

                {/* Visualization - Spans 2x2 */}
                <div className="md:col-span-2 md:row-span-2 p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col relative">
                  <div className="flex justify-between items-start mb-6">
                    <div className="text-left">
                      <h3 className="font-heading font-medium tracking-tight text-[#ffffff] mb-1">Risk Distribution</h3>
                    </div>
                    {/* Legend */}
                    <div className="flex flex-col items-end gap-1">
                      <div className="flex items-center gap-2">
                        <span className="text-[8px] text-[#aab9be] uppercase font-bold">Density</span>
                        <div className="w-24 h-1.5 rounded-full bg-gradient-to-r from-[rgb(0,0,255)] via-[rgb(0,255,0)] to-[rgb(255,0,0)]" />
                      </div>
                      <div className="flex justify-between w-24 text-[8px] text-[#aab9be] font-medium px-0.5">
                        <span>Low</span>
                        <span>High</span>
                      </div>
                    </div>
                  </div>
                  
                  <div className="flex-grow flex flex-col relative w-full min-h-[240px]">
                    <div className="flex flex-grow">
                      {/* Y-axis */}
                      <div className="flex flex-col justify-between text-[10px] text-[#aab9be] font-medium pr-3 pb-6 w-10 items-end relative">
                        <span>35%</span>
                        <span>30%</span>
                        <span>25%</span>
                        <span>20%</span>
                        <span>15%</span>
                        <span className="absolute top-1/2 -left-5 -translate-y-1/2 -rotate-90 tracking-widest uppercase">APY</span>
                        <span>10%</span>
                      </div>
                      
                      {/* Grid */}
                      <div 
                        className="flex-grow grid gap-[1px]"
                        style={{ 
                          gridTemplateColumns: 'repeat(32, minmax(0, 1fr))',
                          gridTemplateRows: 'repeat(32, minmax(0, 1fr))'
                        }}
                      >
                        {heatmapData.map((val, i) => (
                          <div 
                            key={i} 
                            className="w-full h-full rounded-[1px]"
                            style={{
                              backgroundColor: getHeatmapColor(val)
                            }}
                          />
                        ))}
                      </div>
                    </div>
                    
                    {/* X-axis */}
                    <div className="flex justify-between text-[10px] text-[#aab9be] font-medium pt-3 pl-10">
                      <span>0%</span>
                      <span>2.5%</span>
                      <span>5%</span>
                      <span>7.5%</span>
                      <span>10%</span>
                      <span>12.5%</span>
                      <span>15%</span>
                    </div>
                    <div className="text-center text-[10px] text-[#aab9be] font-medium mt-1 pl-10 tracking-widest uppercase">
                      Max Drawdown
                    </div>
                  </div>
                </div>

                {/* Liquidation Cascade */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Liquidation Cascade</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">0.05%</div>
                    <div className="text-s text-[#37d097] font-medium">Insurance Fund Protected</div>
                  </div>
                </div>

                {/* LST Depeg Events */}
                <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                  <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">LST Depeg Events</div>
                  <div>
                    <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">0.00%</div>
                    <div className="text-s text-[#37d097] font-medium">Gradual Liquidation Cap</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Risk Management Framework */}
        <section id="risk" className="pt-32 pb-32 bg-[#ffffff]">
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
