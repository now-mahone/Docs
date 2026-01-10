// Created: 2025-12-29
'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, Shield, Zap, Globe, BarChart3, Lock, ChevronRight, Layers, Landmark, Coins, FileCheck, Search, Activity, Cpu, Database, Network } from 'lucide-react';
import { motion, useScroll, useTransform } from 'framer-motion';
import { FAQ } from '@/components/FAQ';

const fadeInUp = {
  initial: { opacity: 0, y: 30 },
  animate: { opacity: 1, y: 0 },
  transition: { duration: 0.8, ease: [0.16, 1, 0.3, 1] }
};

const staggerContainer = {
  initial: {},
  animate: { transition: { staggerChildren: 0.1 } }
};

export default function LandingPage() {
  const [ethPrice, setEthPrice] = useState(3000);
  const [calcAmount, setCalcAmount] = useState(10);
  const apy = 12.42;

  useEffect(() => {
    const fetchPrice = async () => {
      try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT');
        const data = await res.json();
        setEthPrice(parseFloat(data.price));
      } catch (e) {
        console.error("Failed to fetch ETH price", e);
      }
    };
    fetchPrice();
  }, []);

  const tvlEth = 0;
  const tvlUsd = (tvlEth * ethPrice).toLocaleString(undefined, { maximumFractionDigits: 0 });
  const yearlyYield = (calcAmount * (apy / 100)).toFixed(4);
  const monthlyYield = (parseFloat(yearlyYield) / 12).toFixed(4);

  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.95]);

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans selection:bg-primary/20 overflow-x-hidden">
      {/* Background patterns inspired by Morpho/Ironfish */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none">
        <div className="absolute inset-0 bg-[radial-gradient(#4c7be7_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      {/* Modern Minimal Navigation */}
      <nav className="fixed top-0 left-0 right-0 h-20 border-b border-zinc-100 bg-white/80 backdrop-blur-xl z-[100] transition-all">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <div className="flex items-center gap-12">
            <Link href="/" className="flex items-center">
              <Image src="/kerne-lockup.svg" alt="Kerne" width={110} height={24} priority />
            </Link>
            <div className="hidden lg:flex items-center gap-8 text-[11px] font-bold uppercase tracking-wider text-zinc-500">
              <Link href="/about" className="hover:text-primary transition-colors">Protocol</Link>
              <Link href="/referrals" className="hover:text-primary transition-colors">Ecosystem</Link>
              <Link href="/security" className="hover:text-primary transition-colors">Security</Link>
              <Link href="/transparency" className="hover:text-primary transition-colors">Proof of Solvency</Link>
            </div>
          </div>
          <div className="flex items-center gap-4">
            <Link href="/terminal" className="hidden sm:flex px-6 py-2.5 bg-primary text-white text-[11px] font-bold uppercase tracking-wider rounded-full hover:bg-primary-dark transition-all shadow-lg shadow-primary/20">
              Launch App
            </Link>
          </div>
        </div>
      </nav>

      <main className="relative z-10 pt-20">
        {/* Massive Hero Section inspired by Cursor/Morpho */}
        <section className="relative px-6 pt-32 pb-64 overflow-hidden">
          <motion.div 
            className="max-w-5xl mx-auto text-center relative z-20"
            style={{ opacity, scale }}
          >
            <motion.div 
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.5 }}
              className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-zinc-100 bg-zinc-50 text-[11px] font-bold text-zinc-500 uppercase tracking-widest mb-12"
            >
              <span className="flex h-2 w-2 rounded-full bg-primary" />
              Institutional Standard for On-Chain Liquidity
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.8 }}
              className="text-7xl md:text-[140px] font-heading font-bold tracking-[-0.05em] leading-[0.85] text-zinc-900 mb-12"
            >
              Universal prime<br />
              <span className="text-primary italic">liquidity layer.</span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto mb-16 font-medium leading-relaxed"
            >
              Kerne engineers capital-efficient, delta-neutral infrastructure for the onchain economy. 
              Institutional-grade yield through mathematical precision.
            </motion.p>

            <motion.div 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.4, duration: 0.8 }}
              className="flex flex-col sm:flex-row items-center justify-center gap-6"
            >
              <Link href="/terminal" className="w-full sm:w-auto px-10 py-5 bg-zinc-900 text-white font-bold uppercase tracking-wider rounded-xl hover:bg-zinc-800 transition-all flex items-center justify-center gap-3">
                Deposit Now <ArrowRight size={18} />
              </Link>
              <a href="/Kerne_Institutional_Litepaper.pdf" className="w-full sm:w-auto px-10 py-5 border border-zinc-200 text-zinc-900 font-bold uppercase tracking-wider rounded-xl hover:bg-zinc-50 transition-all">
                Read Documentation
              </a>
            </motion.div>
          </motion.div>

          {/* Abstract Product Surface inspired by Morpho */}
          <motion.div 
            initial={{ opacity: 0, y: 100 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.6, duration: 1 }}
            className="max-w-6xl mx-auto mt-32 relative"
          >
            <div className="aspect-[16/9] w-full rounded-3xl bg-zinc-50 border border-zinc-100 shadow-[0_40px_100px_-20px_rgba(0,0,0,0.1)] overflow-hidden p-4">
              <div className="w-full h-full rounded-2xl bg-white border border-zinc-100 flex items-center justify-center text-zinc-300 font-bold uppercase tracking-widest text-xs">
                 [Terminal_Preview_Interface]
              </div>
            </div>
            {/* Morpho-style floating cards */}
            <motion.div 
              animate={{ y: [0, -10, 0] }}
              transition={{ duration: 4, repeat: Infinity, ease: "easeInOut" }}
              className="absolute -right-8 top-1/4 p-6 bg-white border border-zinc-100 rounded-2xl shadow-2xl z-30 hidden lg:block"
            >
              <div className="flex items-center gap-4 mb-4">
                <div className="w-10 h-10 bg-primary/10 rounded-full flex items-center justify-center text-primary">
                  <BarChart3 size={20} />
                </div>
                <div>
                  <div className="text-[10px] font-bold text-zinc-400 uppercase">Live Yield</div>
                  <div className="text-xl font-bold font-heading">12.42% APY</div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* Core Pillars Section inspired by Ironfish */}
        <section className="px-6 py-48 bg-zinc-50 border-y border-zinc-100">
          <div className="max-w-7xl mx-auto">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
              <motion.div {...fadeInUp} className="p-12 bg-white rounded-3xl border border-zinc-200/50 hover:border-primary/50 transition-all group">
                <Activity className="text-primary mb-8" size={32} />
                <h3 className="text-2xl font-heading font-bold mb-4 tracking-tight uppercase">Delta-Neutral</h3>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  Autonomous hedging of spot exposure with perpetual futures to capture base funding rates.
                </p>
              </motion.div>
              <motion.div {...fadeInUp} className="p-12 bg-white rounded-3xl border border-zinc-200/50 hover:border-primary/50 transition-all group">
                <Shield className="text-primary mb-8" size={32} />
                <h4 className="text-2xl font-heading font-bold mb-4 tracking-tight uppercase">Non-Custodial</h4>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  Trustless vault architecture audited on Base. Users retain 100% control of principal.
                </p>
              </motion.div>
              <motion.div {...fadeInUp} className="p-12 bg-white rounded-3xl border border-zinc-200/50 hover:border-primary/50 transition-all group">
                <Network className="text-primary mb-8" size={32} />
                <h4 className="text-2xl font-heading font-bold mb-4 tracking-tight uppercase">Base-Native</h4>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  Deeply integrated into the Base economy for maximum performance and cost efficiency.
                </p>
              </motion.div>
            </div>
          </div>
        </section>

        {/* Institutional Proof by Ironfish Style */}
        <section className="px-6 py-48">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-24 items-center">
              <div className="flex-1">
                <h2 className="text-5xl md:text-7xl font-heading font-bold tracking-tighter mb-8 leading-[0.9] uppercase">
                  Engineered for<br />
                  Institutional<br />
                  <span className="text-primary italic">reliability.</span>
                </h2>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8 mt-16 font-bold uppercase tracking-widest text-[11px] text-zinc-500">
                  <div className="flex items-center gap-4 border-b border-zinc-100 pb-4">
                    <Database size={16} className="text-primary" />
                    Real-Time Solvency
                  </div>
                  <div className="flex items-center gap-4 border-b border-zinc-100 pb-4">
                    <Cpu size={16} className="text-primary" />
                    Automated Hedging
                  </div>
                  <div className="flex items-center gap-4 border-b border-zinc-100 pb-4">
                    <Landmark size={16} className="text-primary" />
                    Tier-1 Custody Compatible
                  </div>
                  <div className="flex items-center gap-4 border-b border-zinc-100 pb-4">
                    <Lock size={16} className="text-primary" />
                    Audited Infrastructure
                  </div>
                </div>
              </div>
              <div className="flex-1 w-full">
                <div className="grid grid-cols-2 gap-4">
                  <div className="aspect-square bg-zinc-50 rounded-2xl border border-zinc-100 flex items-center justify-center">
                    <Image src="/base-logo.svg" alt="Base" width={60} height={60} className="grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all" />
                  </div>
                  <div className="aspect-square bg-zinc-50 rounded-2xl border border-zinc-100 flex items-center justify-center">
                    <Image src="/binance-logo.svg" alt="Binance" width={60} height={60} className="grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all" />
                  </div>
                  <div className="aspect-square bg-zinc-50 rounded-2xl border border-zinc-100 flex items-center justify-center">
                    <Image src="/openzeppelin-logo.svg" alt="OpenZeppelin" width={60} height={60} className="grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all" />
                  </div>
                  <div className="aspect-square bg-zinc-50 rounded-2xl border border-zinc-100 flex items-center justify-center">
                    <Image src="/trailofbits-logo.svg" alt="Trail of Bits" width={60} height={60} className="grayscale opacity-40 hover:grayscale-0 hover:opacity-100 transition-all" />
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <FAQ />

      <footer className="px-6 py-48 border-t border-zinc-100 bg-white">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-24">
            <div className="col-span-1 lg:col-span-2">
              <Image src="/kerne-lockup.svg" alt="Kerne" width={140} height={32} className="mb-8" />
              <p className="text-zinc-500 font-medium max-w-sm mb-12">
                Kerne Protocol defines the next generation of capital-efficient, on-chain financial infrastructure. 
                Built for institutional scale on Base.
              </p>
              <div className="flex gap-6">
                <Link href="https://x.com/KerneProtocol" className="text-zinc-400 hover:text-primary transition-colors">X / Twitter</Link>
                <Link href="https://github.com/kerne-protocol" className="text-zinc-400 hover:text-primary transition-colors">GitHub</Link>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-12">
              <div className="flex flex-col gap-6">
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">Protocol</h5>
                <Link href="/terminal" className="text-zinc-600 font-medium hover:text-primary transition-colors">Terminal</Link>
                <Link href="/about" className="text-zinc-600 font-medium hover:text-primary transition-colors">Litepaper</Link>
                <Link href="/referrals" className="text-zinc-600 font-medium hover:text-primary transition-colors">Referrals</Link>
              </div>
              <div className="flex flex-col gap-6">
                <h5 className="text-[11px] font-bold uppercase tracking-wider text-zinc-400">Institutional</h5>
                <Link href="/transparency" className="text-zinc-600 font-medium hover:text-primary transition-colors">Transparency</Link>
                <Link href="/risk" className="text-zinc-600 font-medium hover:text-primary transition-colors">Risk Policy</Link>
                <Link href="/security" className="text-zinc-600 font-medium hover:text-primary transition-colors">Security</Link>
              </div>
            </div>
          </div>
          <div className="mt-24 pt-12 border-t border-zinc-100 flex flex-col sm:flex-row justify-between items-center gap-6">
            <div className="text-zinc-400 text-xs font-medium tracking-tight">
              © 2026 Kerne Protocol. All rights reserved. Built on Base.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
