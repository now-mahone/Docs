// Created: 2026-01-06
'use client';

import React from 'react';
import { Gift, TrendingUp, Users, ArrowUpRight } from 'lucide-react';

export default function EcosystemFund() {
  const grants = [
    { id: 1, recipient: 'Aerodrome_LP_Incentives', amount: '50,000 KERNE', status: 'Active', progress: 45 },
    { id: 2, recipient: 'Institutional_Onboarding_Grant', amount: '25,000 KERNE', status: 'Pending', progress: 0 },
    { id: 3, recipient: 'Security_Audit_Fund', amount: '100,000 KERNE', status: 'Completed', progress: 100 },
  ];

  return (
    <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-xl font-mono">
      <div className="flex justify-between items-center mb-8">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-purple-500/10 rounded-lg text-purple-500">
            <Gift size={20} />
          </div>
          <div>
            <h2 className="text-sm font-bold uppercase tracking-widest">Ecosystem_Fund_Dashboard</h2>
            <p className="text-[10px] text-zinc-500">Grant Management & Revenue Sharing</p>
          </div>
        </div>
        <button className="px-4 py-2 bg-purple-600 text-white text-[10px] font-bold uppercase hover:bg-purple-500 transition-colors flex items-center gap-2">
          APPLY_FOR_GRANT
          <ArrowUpRight size={14} />
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Total_Fund_Size</p>
          <p className="text-lg font-bold text-white">1,000,000 KERNE</p>
          <p className="text-[10px] text-zinc-600 mt-1">10% of Total Supply</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Revenue_Shared</p>
          <p className="text-lg font-bold text-emerald-500">$12,450.00</p>
          <p className="text-[10px] text-zinc-600 mt-1">Last 30 Days</p>
        </div>
        <div className="p-4 bg-black/40 border border-zinc-800 rounded-lg">
          <p className="text-[10px] text-zinc-500 uppercase mb-1">Active_Grants</p>
          <p className="text-lg font-bold text-purple-400">12</p>
          <p className="text-[10px] text-zinc-600 mt-1">Across 4 Chains</p>
        </div>
      </div>

      <div className="space-y-4">
        <h3 className="text-[10px] font-bold uppercase tracking-widest text-zinc-400 mb-4">Recent_Grants</h3>
        {grants.map((grant) => (
          <div key={grant.id} className="p-4 bg-zinc-800/30 border border-zinc-700 rounded-lg">
            <div className="flex justify-between items-center mb-3">
              <span className="text-[11px] text-white font-bold">{grant.recipient}</span>
              <span className={`text-[9px] px-2 py-0.5 rounded uppercase font-bold ${
                grant.status === 'Active' ? 'bg-emerald-500/10 text-emerald-500' : 
                grant.status === 'Completed' ? 'bg-blue-500/10 text-blue-500' : 'bg-zinc-500/10 text-zinc-500'
              }`}>
                {grant.status}
              </span>
            </div>
            <div className="flex justify-between items-center text-[10px] text-zinc-500 mb-2">
              <span>Allocation: {grant.amount}</span>
              <span>{grant.progress}% Vested</span>
            </div>
            <div className="w-full h-1 bg-zinc-800 rounded-full overflow-hidden">
              <div 
                className="h-full bg-purple-500 transition-all duration-500" 
                style={{ width: `${grant.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
