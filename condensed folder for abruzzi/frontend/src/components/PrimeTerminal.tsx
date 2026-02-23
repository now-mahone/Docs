// Created: 2026-01-06
'use client';

import React, { useState } from 'react';
import { TrendingUp, Shield, Zap, BarChart3 } from 'lucide-react';

export default function PrimeTerminal() {
  const [allocation, setAllocation] = useState('100.00');
  
  return (
    <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-sm font-mono">
      <div className="flex justify-between items-center mb-6">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-blue-500/10 rounded-sm text-blue-500">
            <Shield size={20} />
          </div>
          <div>
            <h2 className=" font-bold uppercase tracking-widest">Kerne_Prime_Terminal</h2>
            <p className="text-xs text-zinc-500">Institutional Brokerage & Execution</p>
          </div>
        </div>
        <div className="text-right">
          <span className="text-xs text-zinc-500 uppercase">Status: </span>
          <span className="text-xs text-emerald-500 uppercase font-bold">Connected_to_CEX</span>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-sm">
          <p className="text-xs text-zinc-500 uppercase mb-1">Prime_AUM</p>
          <p className="text-l font-bold text-white">42.069 ETH</p>
          <p className="text-xs text-zinc-600 mt-1">≈ $126,207.00</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-sm">
          <p className="text-xs text-zinc-500 uppercase mb-1">Active_Hedge</p>
          <p className="text-l font-bold text-emerald-500">-42.00 ETH</p>
          <p className="text-xs text-zinc-600 mt-1">Delta: 0.069 ETH</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-sm">
          <p className="text-xs text-zinc-500 uppercase mb-1">Prime_Fee</p>
          <p className="text-l font-bold text-blue-400">0.50%</p>
          <p className="text-xs text-zinc-600 mt-1">Annual SaaS Model</p>
        </div>
      </div>

      <div className="space-y-4">
        <div className="p-4 bg-zinc-800/30 border border-zinc-700 rounded-sm">
          <div className="flex justify-between items-center mb-4">
            <h3 className=" font-bold uppercase tracking-widest text-zinc-300">Allocation_Control</h3>
            <span className="text-xs text-zinc-500">Max: 124.489 ETH</span>
          </div>
          <div className="flex gap-4">
            <input 
              type="number" 
              value={allocation}
              onChange={(e) => setAllocation(e.target.value)}
              className="flex-1 bg-black border border-zinc-700 p-2 text-xs text-white focus:outline-none focus:border-blue-500"
            />
            <button className="px-4 py-2 bg-blue-600 text-white text-xs font-bold uppercase hover:bg-blue-500 transition-colors">
              ALLOCATE_TO_PRIME
            </button>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          <button className="p-3 bg-zinc-800/50 border border-zinc-700 rounded-sm text-xs font-bold uppercase text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all flex items-center justify-center gap-2">
            <BarChart3 size={14} />
            View_Execution_Logs
          </button>
          <button className="p-3 bg-zinc-800/50 border border-zinc-700 rounded-sm text-xs font-bold uppercase text-zinc-400 hover:text-white hover:bg-zinc-800 transition-all flex items-center justify-center gap-2">
            <TrendingUp size={14} />
            Hedge_Analytics
          </button>
        </div>
      </div>
    </div>
  );
}
