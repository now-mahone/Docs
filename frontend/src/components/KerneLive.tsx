// Created: 2026-01-06
'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Globe, Shield, Zap, BarChart3, CheckCircle2 } from 'lucide-react';
import { MetricCard } from '@/components/MetricCard';

export default function KerneLive() {
  const [uptime, setUptime] = useState('99.99');
  const [totalTrades, setTotalTrades] = useState(1245);
  
  useEffect(() => {
    const interval = setInterval(() => {
      setTotalTrades(prev => prev + (Math.random() > 0.7 ? 1 : 0));
    }, 3000);
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl font-mono">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-emerald-500/10 rounded-lg text-emerald-500">
            <Activity size={20} />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-widest">Kerne_Live_Operations</h2>
            <p className="text-[10px] text-zinc-500">Global Protocol Status & Execution</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-3 py-1 bg-emerald-500/10 border border-emerald-500/30 rounded-full">
          <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
          <span className="text-[9px] text-emerald-500 font-bold uppercase">Production_Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">System_Uptime</p>
          <p className="text-lg font-bold text-white">{uptime}%</p>
          <p className="text-[10px] text-emerald-500 mt-1">Tier-1 Reliability</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Total_Trades</p>
          <p className="text-lg font-bold text-white">{totalTrades.toLocaleString()}</p>
          <p className="text-[10px] text-zinc-600 mt-1">Across 3 Exchanges</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Active_Nodes</p>
          <p className="text-lg font-bold text-white">14</p>
          <p className="text-[10px] text-zinc-600 mt-1">OES Verification</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Hedge_Efficiency</p>
          <p className="text-lg font-bold text-blue-400">99.82%</p>
          <p className="text-[10px] text-zinc-600 mt-1">Delta-Neutral Target</p>
        </div>
      </div>

      <div className="space-y-6">
        <div>
          <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-4">Global_Execution_Map</h3>
          <div className="h-48 bg-zinc-800/20 border border-zinc-800 rounded-lg flex items-center justify-center relative overflow-hidden">
            <Globe size={80} className="text-zinc-800 animate-spin-slow" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="grid grid-cols-3 gap-12">
                <div className="text-center">
                  <div className="w-2 h-2 bg-blue-500 rounded-full mx-auto mb-2 shadow-[0_0_10px_rgba(59,130,246,0.5)]" />
                  <span className="text-[8px] text-zinc-500 uppercase">NY_Node</span>
                </div>
                <div className="text-center">
                  <div className="w-2 h-2 bg-emerald-500 rounded-full mx-auto mb-2 shadow-[0_0_10px_rgba(16,185,129,0.5)]" />
                  <span className="text-[8px] text-zinc-500 uppercase">LDN_Node</span>
                </div>
                <div className="text-center">
                  <div className="w-2 h-2 bg-purple-500 rounded-full mx-auto mb-2 shadow-[0_0_10px_rgba(168,85,247,0.5)]" />
                  <span className="text-[8px] text-zinc-500 uppercase">TKO_Node</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div className="p-4 bg-zinc-800/30 border border-zinc-700 rounded-lg">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-zinc-300 mb-3 flex items-center gap-2">
              <Shield size={14} className="text-blue-400" />
              Security_Heartbeat
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Vault_Integrity</span>
                <span className="text-emerald-500 font-bold">SECURE</span>
              </div>
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Oracle_Latency</span>
                <span className="text-zinc-300">14ms</span>
              </div>
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Insurance_Fund</span>
                <span className="text-zinc-300">$245,000</span>
              </div>
            </div>
          </div>
          <div className="p-4 bg-zinc-800/30 border border-zinc-700 rounded-lg">
            <h4 className="text-[10px] font-bold uppercase tracking-widest text-zinc-300 mb-3 flex items-center gap-2">
              <CheckCircle2 size={14} className="text-emerald-400" />
              Genesis_Completion
            </h4>
            <div className="space-y-2">
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Phase_Status</span>
                <span className="text-emerald-500 font-bold uppercase">Finalized</span>
              </div>
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Total_Genesis_Yield</span>
                <span className="text-zinc-300">14.2% APY</span>
              </div>
              <div className="flex justify-between items-center text-[9px]">
                <span className="text-zinc-500 uppercase">Bonus_Distributed</span>
                <span className="text-zinc-300">100%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
