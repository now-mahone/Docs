"use client";

// Created: 2026-01-13
import React, { useState, useEffect } from 'react';

export default function SolverDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [recent, setRecent] = useState<any[]>([]);

  useEffect(() => {
    // In production, this would fetch from the analytics_api.py
    // For now, we simulate the data
    setStats({
      total_intents: 142,
      successful_hedges: 137,
      win_rate: "96.48%",
      total_profit_bps: "712.40",
      daily_target_status: "ON_TRACK"
    });
    setRecent([
      { timestamp: Date.now(), venue: "CowSwap", coin: "ETH", amount: 1.5, profit_bps: 5.2, status: "HEDGED" },
      { timestamp: Date.now() - 10000, venue: "UniswapX", coin: "ETH", amount: 0.8, profit_bps: 4.8, status: "HEDGED" }
    ]);
  }, []);

  return (
    <div className="min-h-screen bg-black text-white p-8 font-mono">
      <div className="max-w-6xl mx-auto">
        <header className="mb-12 border-b border-zinc-800 pb-8">
          <h1 className="text-4xl font-bold mb-2 tracking-tighter text-green-500">KERNE SOLVER TERMINAL</h1>
          <p className="text-zinc-400">Real-time Intent Extraction Metrics</p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-12">
          <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg">
            <div className="text-zinc-500 text-xs mb-1">TOTAL INTENTS</div>
            <div className="text-3xl font-bold">{stats?.total_intents}</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg">
            <div className="text-zinc-500 text-xs mb-1">WIN RATE</div>
            <div className="text-3xl font-bold text-green-500">{stats?.win_rate}</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg">
            <div className="text-zinc-500 text-xs mb-1">TOTAL PROFIT (BPS)</div>
            <div className="text-3xl font-bold text-blue-500">{stats?.total_profit_bps}</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-zinc-800 rounded-lg">
            <div className="text-zinc-500 text-xs mb-1">TARGET STATUS</div>
            <div className="text-3xl font-bold text-yellow-500">{stats?.daily_target_status}</div>
          </div>
        </div>

        <div className="bg-zinc-900/30 border border-zinc-800 rounded-lg overflow-hidden">
          <div className="p-4 border-b border-zinc-800 bg-zinc-900/50 font-bold">RECENT EXTRACTIONS</div>
          <table className="w-full text-left text-sm">
            <thead>
              <tr className="text-zinc-500 border-b border-zinc-800">
                <th className="p-4">VENUE</th>
                <th className="p-4">COIN</th>
                <th className="p-4">AMOUNT</th>
                <th className="p-4">PROFIT (BPS)</th>
                <th className="p-4">STATUS</th>
              </tr>
            </thead>
            <tbody>
              {recent.map((trade, i) => (
                <tr key={i} className="border-b border-zinc-800/50 hover:bg-white/5">
                  <td className="p-4">{trade.venue}</td>
                  <td className="p-4">{trade.coin}</td>
                  <td className="p-4">{trade.amount} ETH</td>
                  <td className="p-4 text-blue-400">+{trade.profit_bps}</td>
                  <td className="p-4 text-green-500">{trade.status}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
