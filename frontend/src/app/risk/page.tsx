// Created: 2026-01-06
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, ShieldAlert, ShieldCheck, TrendingDown, ZapOff } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function RiskPolicyPage() {
  return (
    <div className="min-h-screen bg-black text-white font-sans selection:bg-emerald-500/30">
      {/* Navigation */}
      <nav className="flex justify-between items-center px-8 py-6 border-b border-zinc-800/50 backdrop-blur-md sticky top-0 z-50">
        <Link href="/" className="flex items-center gap-2 group">
          <ArrowLeft size={18} className="text-zinc-400 group-hover:text-white transition-colors" />
          <span className="text-xl font-bold tracking-tighter uppercase">Kerne</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="text-[10px] text-emerald-500 uppercase tracking-[0.2em] font-bold">
            Risk_Policy_v1.0
          </div>
        </div>
      </nav>

      {/* Hero */}
      <section className="px-8 pt-24 pb-16 max-w-4xl mx-auto text-center">
        <motion.h1 
          className="text-5xl md:text-7xl font-bold tracking-tighter mb-6 uppercase"
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
        >
          Risk <br />
          <span className="text-emerald-500">Management.</span>
        </motion.h1>
        <motion.p 
          className="text-zinc-400 text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Institutional-grade safety modules designed to protect capital through mathematical precision and automated circuit breakers.
        </motion.p>
      </section>

      {/* Content */}
      <section className="px-8 py-20 max-w-3xl mx-auto">
        <motion.div className="space-y-12" variants={fadeInUp} initial="initial" whileInView="whileInView">
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <ShieldCheck className="text-emerald-500" size={24} />
              1. Collateral Health
            </h2>
            <p className="text-zinc-400 leading-relaxed mb-4">
              The system maintains a target Collateral Ratio (CR) of 130%. Automated liquidation logic triggers at 115% to restore system health.
            </p>
            <ul className="text-sm text-zinc-500 space-y-2 list-disc pl-5">
              <li>Target CR: 130%</li>
              <li>Soft Liquidation: 115% (Partial Unwind)</li>
              <li>Hard Liquidation: 105% (Emergency Halt)</li>
            </ul>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <TrendingDown className="text-emerald-500" size={24} />
              2. Depeg Protection
            </h2>
            <p className="text-zinc-400 leading-relaxed">
              Our "Oracle Guard" monitors the exchange rate between LSTs and ETH. Any deviation greater than 2.0% from the 24h moving average triggers an immediate pause on vault interactions to prevent toxic arbitrage.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <ZapOff className="text-emerald-500" size={24} />
              3. Funding Rate Risk
            </h2>
            <p className="text-zinc-400 leading-relaxed">
              To prevent capital bleed, the protocol monitors the 3-day SMA of ETH-PERP funding rates. If the SMA turns negative, the strategy enters "Idle Mode," closing short positions until positive funding returns.
            </p>
          </div>

          <div className="p-8 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl">
            <h3 className="text-lg font-bold uppercase mb-4 text-emerald-500 flex items-center gap-2">
              <ShieldAlert size={20} />
              Institutional Buffer
            </h3>
            <p className="text-sm text-zinc-400 leading-relaxed">
              A 10% withdrawal buffer is maintained on-chain at all times to ensure instant liquidity for users, while the remaining 90% is deployed in delta-neutral strategies across top-tier CEXs.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-zinc-800/50">
        <Link href="/terminal" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Terminal
        </Link>
        <Link href="/transparency" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Transparency
        </Link>
      </footer>
    </div>
  );
}
