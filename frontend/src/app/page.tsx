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
              Institutional Standard for Onchain Liquidity
            </motion.div>
            
            <motion.h1 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2, duration: 0.8 }}
              className="text-7xl md:text-[140px] font-heading font-bold tracking-[-0.05em] leading-[0.85] text-zinc-900 mb-12"
            >
              The future of<br />
              <span className="text-primary italic">onchain yield.</span>
            </motion.h1>

            <motion.p 
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3, duration: 0.8 }}
              className="text-lg md:text-xl text-zinc-500 max-w-2xl mx-auto mb-16 font-medium leading-relaxed"
            >
              Earn yield on ETH without worrying about price swings. Kerne's vaults are hedged automatically, you just deposit and watch it grow.
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
                  <div className="text-xl font-bold font-heading">20.4% APY</div>
                </div>
              </div>
            </motion.div>
          </motion.div>
        </section>

        {/* Yield Calculator Section */}
        <section className="px-6 py-48 bg-white border-y border-zinc-100">
          <div className="max-w-5xl mx-auto">
            <div className="text-center mb-24">
              <h2 className="text-4xl md:text-6xl font-heading font-bold tracking-tighter mb-6 uppercase">Yield calculator to see the onchain difference</h2>
              <p className="text-zinc-500 font-medium">Calculated based on current funding rates and staking yield. Performance fees are already deducted.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-12 items-center">
              <div className="p-12 bg-zinc-50 rounded-3xl border border-zinc-100">
                <div className="mb-8">
                  <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400 block mb-4">Investment Amount ETH</label>
                  <div className="text-5xl font-bold font-heading">10 ETH</div>
                  <div className="text-xl text-zinc-400 mt-2 font-medium">= $30,160</div>
                </div>
                <div className="space-y-6 pt-8 border-t border-zinc-200">
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500 font-medium">ETH Funding Rate</span>
                    <span className="font-bold text-emerald-500">0.0342 (Positive)</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-zinc-500 font-medium">wsETH APY</span>
                    <span className="font-bold text-zinc-900">3.21% (Lido Data)</span>
                  </div>
                </div>
              </div>
              <div className="space-y-8">
                <div className="p-8 bg-primary/5 rounded-2xl border border-primary/10">
                  <div className="text-[11px] font-bold uppercase tracking-widest text-primary mb-2">Monthly Earnings</div>
                  <div className="text-4xl font-bold font-heading text-primary">$512.72</div>
                </div>
                <div className="p-8 bg-zinc-900 rounded-2xl border border-zinc-800">
                  <div className="text-[11px] font-bold uppercase tracking-widest text-zinc-400 mb-2">Yearly Earnings</div>
                  <div className="text-4xl font-bold font-heading text-white">$6,152.64</div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Backtested Performance Section */}
        <section className="px-6 py-48 bg-zinc-50">
          <div className="max-w-7xl mx-auto">
            <div className="flex flex-col lg:flex-row gap-24 items-center">
              <div className="flex-1">
                <h2 className="text-5xl md:text-7xl font-heading font-bold tracking-tighter mb-8 leading-[0.9] uppercase">
                  Backtested<br />
                  performance.
                </h2>
                <p className="text-lg text-zinc-500 font-medium leading-relaxed mb-12">
                  Historical simulation showing Kerne's delta neutral strategy vs ETH buy and hold volatility.
                </p>
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-8">
                  <div>
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">Avg Daily Yield</div>
                    <div className="text-3xl font-bold font-heading">0.047%</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">Max Drawdown</div>
                    <div className="text-3xl font-bold font-heading">6.8%</div>
                  </div>
                  <div>
                    <div className="text-[10px] font-bold text-zinc-400 uppercase tracking-widest mb-2">Positive Days%</div>
                    <div className="text-3xl font-bold font-heading">65.2%</div>
                  </div>
                </div>
              </div>
              <div className="flex-1 w-full">
                <div className="aspect-[4/3] bg-white rounded-3xl border border-zinc-200 p-8 flex flex-col">
                  <div className="flex justify-between items-center mb-8">
                    <div className="text-xs font-bold uppercase tracking-widest text-zinc-400">Simulated Performance Comparison</div>
                  </div>
                  <div className="flex-1 flex items-center justify-center text-zinc-300 font-bold uppercase tracking-widest text-xs border border-dashed border-zinc-100 rounded-xl">
                    [ETH Funding Rate History vs ETH Buy and Hold]
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Kerne Explained Section */}
        <section className="px-6 py-48 bg-white">
          <div className="max-w-7xl mx-auto">
            <div className="text-center max-w-3xl mx-auto mb-32">
              <h2 className="text-5xl md:text-7xl font-heading font-bold tracking-tighter mb-8 uppercase">Kerne explained</h2>
              <p className="text-lg text-zinc-500 font-medium leading-relaxed">
                A step by step breakdown of how Kerne's delta neutral infrastructure generates stable yield while eliminating market risk.
              </p>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-12">
              <div className="space-y-8">
                <div className="w-16 h-16 bg-zinc-900 text-white rounded-2xl flex items-center justify-center text-2xl font-bold font-heading">01</div>
                <h3 className="text-2xl font-heading font-bold uppercase tracking-tight">Deposit</h3>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  Users deposit ETH into Kerne's non custodial smart contracts. Your principal remains fully backed by liquid staking tokens on Base.
                </p>
              </div>
              <div className="space-y-8">
                <div className="w-16 h-16 bg-zinc-900 text-white rounded-2xl flex items-center justify-center text-2xl font-bold font-heading">02</div>
                <h3 className="text-2xl font-heading font-bold uppercase tracking-tight">Hedge</h3>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  Our autonomous hedging engine opens equal sized short positions on perpetual futures markets, neutralizing price exposure.
                </p>
              </div>
              <div className="space-y-8">
                <div className="w-16 h-16 bg-zinc-900 text-white rounded-2xl flex items-center justify-center text-2xl font-bold font-heading">03</div>
                <h3 className="text-2xl font-heading font-bold uppercase tracking-tight">Earn</h3>
                <p className="text-zinc-500 leading-relaxed font-medium">
                  You earn yield from perpetual funding rates and LST staking rewards, auto compounded and distributed as vault share appreciation.
                </p>
              </div>
            </div>

            <div className="mt-32 p-12 bg-zinc-50 rounded-[40px] border border-zinc-100">
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-24 items-center">
                <div>
                  <h3 className="text-3xl md:text-5xl font-heading font-bold tracking-tighter mb-8 uppercase">Why institutions choose Kerne</h3>
                  <p className="text-zinc-500 leading-relaxed font-medium mb-8">
                    Institutional capital allocators require mathematical precision, real time transparency, and automated risk management at scale. Built natively on Base, Kerne delivers ultra low gas costs and near instant execution speed critical for high frequency rebalancing. Your principal remains 100% non custodial through audited smart contracts you retain complete control of your assets at all times, eliminating counterparty risk entirely.
                  </p>
                </div>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-primary uppercase tracking-widest">Real-Time Verification</div>
                    <p className="text-sm text-zinc-600 font-medium leading-relaxed">Continuous onchain solvency proofs ensure 1:1 asset backing at all times.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-primary uppercase tracking-widest">Zero Counterparty Risk</div>
                    <p className="text-sm text-zinc-600 font-medium leading-relaxed">Non custodial architecture means you maintain complete control of your principal.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-primary uppercase tracking-widest">Automated Execution</div>
                    <p className="text-sm text-zinc-600 font-medium leading-relaxed">High frequency rebalancing ensures precise delta neutral positioning 24/7.</p>
                  </div>
                  <div className="space-y-4">
                    <div className="text-[10px] font-bold text-primary uppercase tracking-widest">Audited Infrastructure</div>
                    <p className="text-sm text-zinc-600 font-medium leading-relaxed">Battle tested smart contracts reviewed by leading security firms.</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Institutional Reliability Section */}
        <section className="px-6 py-48 bg-zinc-900 text-white">
          <div className="max-w-7xl mx-auto">
            <div className="max-w-3xl mb-24">
              <h2 className="text-5xl md:text-7xl font-heading font-bold tracking-tighter mb-8 uppercase">Institutional reliability</h2>
              <p className="text-xl text-zinc-400 font-medium leading-relaxed">
                Engineered for the most demanding capital allocators, Kerne combines absolute transparency with autonomous risk management.
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
              <div className="p-12 bg-white/5 rounded-3xl border border-white/10 hover:bg-white/10 transition-all">
                <h3 className="text-2xl font-heading font-bold mb-6 uppercase tracking-tight">Real time Solvency</h3>
                <p className="text-zinc-400 leading-relaxed font-medium">
                  Continuous onchain verification of protocol assets. Institutional partners can audit Kerne's balance sheet in real time, ensuring 1:1 backing of all synthetic assets with verifiable LST collateral.
                </p>
              </div>
              <div className="p-12 bg-white/5 rounded-3xl border border-white/10 hover:bg-white/10 transition-all">
                <h3 className="text-2xl font-heading font-bold mb-6 uppercase tracking-tight">Automated Hedging</h3>
                <p className="text-zinc-400 leading-relaxed font-medium">
                  Proprietary delta neutral engine that autonomously manages market exposure. Our infrastructure captures funding rates while eliminating directional risk through high frequency algorithmic precision.
                </p>
              </div>
              <div className="p-12 bg-white/5 rounded-3xl border border-white/10 hover:bg-white/10 transition-all">
                <h3 className="text-2xl font-heading font-bold mb-6 uppercase tracking-tight">Tier 1 Custody</h3>
                <p className="text-zinc-400 leading-relaxed font-medium">
                  Designed for integration with multi sig safe architectures and institutional custodians. Kerne maintains non custodial principles while providing the technical scaffolding required by the world's largest funds.
                </p>
              </div>
              <div className="p-12 bg-white/5 rounded-3xl border border-white/10 hover:bg-white/10 transition-all">
                <h3 className="text-2xl font-heading font-bold mb-6 uppercase tracking-tight">Audited Infrastructure</h3>
                <p className="text-zinc-400 leading-relaxed font-medium">
                  Battle tested smart contracts audited by industry leading security firms. We prioritize mathematical correctness and formal verification to maintain the standard for onchain security.
                </p>
              </div>
            </div>
          </div>
        </section>

        {/* Ecosystem Infrastructure Section */}
        <section className="px-6 py-48 bg-white">
          <div className="max-w-7xl mx-auto text-center">
            <h2 className="text-[11px] font-bold uppercase tracking-[0.3em] text-zinc-400 mb-16">Ecosystem infrastructure</h2>
            <div className="flex flex-wrap justify-center items-center gap-12 md:gap-24 opacity-50">
              <Image src="/base-logo.svg" alt="Base" width={120} height={40} className="grayscale" />
              <Image src="/hyperliquid-logo.svg" alt="Hyperliquid" width={160} height={40} className="grayscale" />
              <Image src="/cowdao-logo.svg" alt="CoW DAO" width={120} height={40} className="grayscale" />
              <Image src="/aerodrome-logo.svg" alt="Aerodrome" width={160} height={40} className="grayscale" />
            </div>
          </div>
        </section>

        {/* Join the Genesis Epoch Section */}
        <section className="px-6 py-48 bg-primary text-white overflow-hidden relative">
          <div className="absolute inset-0 opacity-10 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-white via-transparent to-transparent" />
          <div className="max-w-5xl mx-auto text-center relative z-10">
            <h2 className="text-5xl md:text-8xl font-heading font-bold tracking-tighter mb-12 uppercase">Join the genesis epoch</h2>
            <p className="text-xl md:text-2xl text-white/80 font-medium max-w-2xl mx-auto mb-16 leading-relaxed">
              Early depositors secure the highest allocation of Quanta points. Connect your wallet and start earning delta neutral yield today.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <Link href="/terminal" className="w-full sm:w-auto px-12 py-6 bg-white text-primary font-bold uppercase tracking-wider rounded-2xl hover:bg-zinc-50 transition-all shadow-2xl shadow-black/20">
                Connect Wallet
              </Link>
              <Link href="/institutional" className="w-full sm:w-auto px-12 py-6 border border-white/30 text-white font-bold uppercase
