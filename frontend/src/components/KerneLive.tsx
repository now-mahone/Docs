// Created: 2026-01-06
'use client';

import React, { useState, useEffect } from 'react';
import { Activity, Globe, Shield, Zap, CheckCircle2 } from 'lucide-react';

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
    <div className="p-8 bg-white border border-[#f1f1ed] rounded-sm font-sans">
      <div className="flex justify-between items-center mb-10">
        <div className="flex items-center gap-4">
          <div className="p-3 bg-[#4c7be7]/5 rounded-sm text-[#4c7be7]">
            <Activity size={24} />
          </div>
          <div>
            <h2 className=" font-heading font-medium text-[#000000]">Live Operations</h2>
            <p className="text-xs font-bold text-zinc-400 uppercase tracking-tight">Global Protocol Status</p>
          </div>
        </div>
        <div className="flex items-center gap-2 px-4 py-1.5 bg-[#4c7be7]/5 border border-[#4c7be7]/10 rounded-full">
          <div className="w-1.5 h-1.5 bg-[#4c7be7] rounded-full" />
          <span className="text-xs text-[#4c7be7] font-bold">Production Active</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-10">
        <div className="p-5 bg-[#f9f9f4] border border-[#f1f1ed] rounded-sm">
          <p className="text-xs font-bold text-zinc-400 uppercase mb-1">System Uptime</p>
          <p className="text-xl font-heading font-medium text-[#000000]">{uptime}%</p>
          <p className="text-xs text-[#4c7be7] font-bold mt-1">Tier-1 Reliability</p>
        </div>
        <div className="p-5 bg-[#f9f9f4] border border-[#f1f1ed] rounded-sm">
          <p className="text-xs font-bold text-zinc-400 uppercase mb-1">Total Trades</p>
          <p className="text-xl font-heading font-medium text-[#000000]">{totalTrades.toLocaleString()}</p>
          <p className="text-xs text-zinc-500 font-bold mt-1">Across 3 Exchanges</p>
        </div>
        <div className="p-5 bg-[#f9f9f4] border border-[#f1f1ed] rounded-sm">
          <p className="text-xs font-bold text-zinc-400 uppercase mb-1">Active Nodes</p>
          <p className="text-xl font-heading font-medium text-[#000000]">14</p>
          <p className="text-xs text-zinc-500 font-bold mt-1">OES Verification</p>
        </div>
        <div className="p-5 bg-[#f9f9f4] border border-[#f1f1ed] rounded-sm">
          <p className="text-xs font-bold text-zinc-400 uppercase mb-1">Hedge Efficiency</p>
          <p className="text-xl font-heading font-medium text-[#4c7be7]">99.82%</p>
          <p className="text-xs text-zinc-500 font-bold mt-1">Delta-Neutral Target</p>
        </div>
      </div>

      <div className="space-y-8">
        <div>
          <h3 className=" font-bold uppercase tracking-widest text-zinc-400 mb-6">Global Execution Map</h3>
          <div className="h-56 bg-[#f9f9f4] border border-[#f1f1ed] rounded-sm flex items-center justify-center relative overflow-hidden">
            <Globe size={100} className="text-[#f1f1ed]" />
            <div className="absolute inset-0 flex items-center justify-center">
              <div className="grid grid-cols-3 gap-16">
                <div className="text-center">
                  <div className="w-2 h-2 bg-[#4c7be7] rounded-full mx-auto mb-3" />
                  <span className="text-xs font-bold text-[#000000] uppercase">NY Node</span>
                </div>
                <div className="text-center">
                  <div className="w-2 h-2 bg-[#4c7be7] rounded-full mx-auto mb-3" />
                  <span className="text-xs font-bold text-[#000000] uppercase">LDN Node</span>
                </div>
                <div className="text-center">
                  <div className="w-2 h-2 bg-[#4c7be7] rounded-full mx-auto mb-3" />
                  <span className="text-xs font-bold text-[#000000] uppercase">TKO Node</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="p-6 bg-white border border-[#f1f1ed] rounded-sm">
            <h4 className=" font-bold uppercase tracking-widest text-[#000000] mb-4 flex items-center gap-3">
              <Shield size={16} className="text-[#4c7be7]" />
              Security Heartbeat
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Vault Integrity</span>
                <span className="text-[#4c7be7] font-bold">SECURE</span>
              </div>
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Oracle Latency</span>
                <span className="text-[#000000] font-bold">14ms</span>
              </div>
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Insurance Fund</span>
                <span className="text-[#000000] font-bold">$245,000</span>
              </div>
            </div>
          </div>
          <div className="p-6 bg-white border border-[#f1f1ed] rounded-sm">
            <h4 className=" font-bold uppercase tracking-widest text-[#000000] mb-4 flex items-center gap-3">
              <CheckCircle2 size={16} className="text-[#4c7be7]" />
              Genesis Completion
            </h4>
            <div className="space-y-3">
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Phase Status</span>
                <span className="text-[#000000] font-bold uppercase">Finalized</span>
              </div>
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Total APY</span>
                <span className="text-[#000000] font-bold">18.4%</span>
              </div>
              <div className="flex justify-between items-center text-xs font-medium">
                <span className="text-zinc-500 uppercase tracking-tighter">Bonus Distributed</span>
                <span className="text-[#000000] font-bold">100%</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
