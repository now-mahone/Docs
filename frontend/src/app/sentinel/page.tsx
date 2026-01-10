'use client';

import React from 'react';
import { useSentinel } from '@/sdk/hooks/useSentinel';
import { VAULT_ADDRESS } from '@/config';
import { Shield, Activity, AlertTriangle, CheckCircle2, BarChart3, FileText, Zap, Lock } from 'lucide-react';
import { motion } from 'framer-motion';

export default function SentinelDashboard() {
  const { risk, loading } = useSentinel(VAULT_ADDRESS);

  if (loading) {
    return (
      <div className="min-h-screen bg-white flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans selection:bg-primary/20">
      <main className="pt-32 pb-24 px-6 max-w-7xl mx-auto">
        <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6 mb-16">
          <div>
            <h1 className="text-4xl md:text-5xl font-heading font-bold tracking-tight mb-4 uppercase">
              Kerne <span className="text-primary italic">Sentinel</span>
            </h1>
            <p className="text-zinc-500 font-medium max-w-xl">
              Institutional-grade risk monitoring and solvency verification engine. 
              Real-time delta tracking and automated stress testing.
            </p>
          </div>
          <div className="flex items-center gap-3 px-4 py-2 bg-green-50 border border-green-100 rounded-full text-green-600 text-[10px] font-bold uppercase tracking-widest">
            <span className="flex h-2 w-2 rounded-full bg-green-500 animate-pulse" />
            System Operational
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8 mb-12">
          {/* Health Score Card */}
          <div className="lg:col-span-2 p-8 bg-zinc-50 border border-zinc-100 rounded-3xl relative overflow-hidden">
            <div className="relative z-10">
              <div className="flex justify-between items-center mb-8">
                <h3 className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Protocol Health Score</h3>
                <Shield className="text-primary" size={20} />
              </div>
              <div className="flex items-end gap-4 mb-8">
                <span className="text-8xl font-heading font-bold leading-none">
                  {risk?.health_score.toFixed(0)}
                </span>
                <span className="text-2xl font-heading font-bold text-zinc-300 mb-2">/ 100</span>
              </div>
              <div className="w-full h-3 bg-zinc-200 rounded-full overflow-hidden">
                <motion.div 
                  initial={{ width: 0 }}
                  animate={{ width: `${risk?.health_score}%` }}
                  className="h-full bg-primary"
                />
              </div>
            </div>
            <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-full -translate-y-1/2 translate-x-1/2 blur-3xl" />
          </div>

          {/* Real-time Delta Card */}
          <div className="p-8 bg-zinc-900 text-white rounded-3xl">
            <div className="flex justify-between items-center mb-8">
              <h3 className="text-[11px] font-bold uppercase tracking-widest text-zinc-500">Net Delta Exposure</h3>
              <Activity className="text-primary" size={20} />
            </div>
            <div className="text-5xl font-heading font-bold mb-4">
              {risk?.net_delta.toFixed(4)}
            </div>
            <p className="text-[10px] text-zinc-500 font-medium uppercase tracking-wider mb-8">
              Target: 0.0000 (Delta Neutral)
            </p>
            <div className="p-4 bg-white/5 rounded-2xl border border-white/10">
              <div className="flex justify-between items-center text-[10px] font-bold uppercase tracking-tight">
                <span>Status</span>
                <span className="text-primary">Optimized</span>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4">On-chain Liq. Distance</div>
            <div className="text-2xl font-heading font-bold">{(risk?.liquidation_distance_onchain || 0 * 100).toFixed(2)}%</div>
          </div>
          <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4">CEX Liq. Distance</div>
            <div className="text-2xl font-heading font-bold">{(risk?.liquidation_distance_cex || 0 * 100).toFixed(2)}%</div>
          </div>
          <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4">LST Peg Deviation</div>
            <div className="text-2xl font-heading font-bold text-green-500">0.02%</div>
          </div>
          <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
            <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-4">Solvency Ratio</div>
            <div className="text-2xl font-heading font-bold text-primary">1.10x</div>
          </div>
        </div>

        {/* Stress Test Reports */}
        <div className="bg-zinc-50 border border-zinc-100 rounded-3xl p-8 md:p-12">
          <div className="flex justify-between items-center mb-12">
            <h3 className="text-2xl font-heading font-bold uppercase tracking-tight">Stress Test <span className="text-primary italic">Reports</span></h3>
            <button className="px-6 py-2.5 bg-zinc-900 text-white text-[10px] font-bold uppercase tracking-wider rounded-full hover:bg-zinc-800 transition-all">
              Run New Simulation
            </button>
          </div>
          
          <div className="space-y-4">
            {[
              { name: "Black Swan (-50% ETH)", date: "2026-01-09", status: "Passed", score: "82/100" },
              { name: "LST Depeg (stETH -10%)", date: "2026-01-08", status: "Passed", score: "91/100" },
              { name: "CEX Liquidity Crunch", date: "2026-01-07", status: "Passed", score: "88/100" },
            ].map((report, idx) => (
              <div key={idx} className="p-6 bg-white border border-zinc-200 rounded-2xl flex flex-col sm:flex-row justify-between items-center gap-6 hover:border-primary/50 transition-all cursor-pointer group">
                <div className="flex items-center gap-6">
                  <div className="w-12 h-12 bg-zinc-50 rounded-xl flex items-center justify-center text-zinc-400 group-hover:text-primary transition-colors">
                    <FileText size={24} />
                  </div>
                  <div>
                    <div className="text-sm font-bold uppercase tracking-tight">{report.name}</div>
                    <div className="text-[10px] text-zinc-400 font-medium">{report.date}</div>
                  </div>
                </div>
                <div className="flex items-center gap-12">
                  <div className="text-center">
                    <div className="text-[10px] font-bold text-zinc-400 uppercase mb-1">Health Score</div>
                    <div className="text-sm font-bold">{report.score}</div>
                  </div>
                  <div className="px-4 py-1.5 bg-green-50 text-green-600 text-[10px] font-bold uppercase tracking-widest rounded-full">
                    {report.status}
                  </div>
                  <ChevronRight size={20} className="text-zinc-300 group-hover:text-primary transition-colors" />
                </div>
              </div>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}

function ChevronRight({ size, className }: { size: number, className?: string }) {
  return (
    <svg 
      width={size} 
      height={size} 
      viewBox="0 0 24 24" 
      fill="none" 
      stroke="currentColor" 
      strokeWidth="2" 
      strokeLinecap="round" 
      strokeLinejoin="round" 
      className={className}
    >
      <path d="m9 18 6-6-6-6"/>
    </svg>
  );
}
