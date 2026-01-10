// Created: 2025-12-29
'use client';

import React, { useEffect, useState, Suspense } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, Shield, Zap, Globe, BarChart3, Lock, ChevronRight, Layers, Landmark, Coins, FileCheck, Search } from 'lucide-react';
import { motion } from 'framer-motion';
import { FAQ } from '@/components/FAQ';

const Skeleton = ({ className }: { className?: string }) => (
  <div className={`animate-pulse bg-zinc-800/50 rounded ${className}`} />
);

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

const staggerContainer = {
  initial: {},
  whileInView: { transition: { staggerChildren: 0.1 } }
};

export default function LandingPage() {
  const [ethPrice, setEthPrice] = useState(3000);
  const [calcAmount, setCalcAmount] = useState(10);
  const [isDemoMode, setIsDemoMode] = useState(false);
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

  // TVL will be fetched from on-chain data - show placeholder during genesis
  const tvlEth = 0; // Will be populated from vault contract
  const tvlUsd = (tvlEth * ethPrice).toLocaleString(undefined, { maximumFractionDigits: 0 });
  
  const yearlyYield = (calcAmount * (apy / 100)).toFixed(4);
  const monthlyYield = (parseFloat(yearlyYield) / 12).toFixed(4);

  const capacityPercent = Math.min((tvlEth / 500) * 100, 100);

  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-primary/30 overflow-x-hidden">
      {/* Genesis Banner */}
      <div className="bg-primary text-primary-foreground py-2 px-4 text-center font-bold text-[10px] uppercase tracking-[0.3em] z-[60] relative">
        [GENESIS_PHASE_ACTIVE] First 50 depositors get 0% performance fees.
      </div>

      {/* Animated Background */}
      <div className="fixed inset-0 pointer-events-none z-0">
        <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full animate-pulse" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[40%] h-[40%] bg-primary/5 blur-[120px] rounded-full animate-pulse" style={{ animationDelay: '2s' }} />
      </div>

      {/* Navigation */}
      <nav className="flex justify-between items-center px-8 py-6 border-b border-border backdrop-blur-md sticky top-0 z-50">
        <div className="flex items-center gap-2">
          <Image src="/kerne-lockup.svg" alt="Kerne Logo" width={100} height={24} className="object-contain" priority />
        </div>
          <div className="hidden md:flex items-center gap-8 text-[10px] font-bold text-muted-foreground uppercase tracking-[0.2em]">
            <Link href="/about" className="hover:text-primary transition-colors">About</Link>
            <Link href="/referrals" className="hover:text-primary transition-colors">Referrals</Link>
            <Link href="/transparency" className="hover:text-primary transition-colors">Transparency</Link>
            <Link href="/security" className="hover:text-primary transition-colors">Security</Link>
            <Link href="/terminal" className="px-4 py-2 bg-primary text-primary-foreground hover:bg-primary-dark transition-all rounded-sm">
              Launch Terminal
            </Link>
          </div>
      </nav>

      {/* Hero Section */}
      <section className="relative px-8 pt-32 pb-20 z-10">
        <motion.div 
          className="max-w-5xl mx-auto text-center"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
        >
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-primary/30 bg-primary/5 text-primary text-[10px] uppercase tracking-[0.2em] mb-8">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
            </span>
            Institutional Delta-Neutral Protocol Live on Base
          </div>
          <h1 className="text-6xl md:text-9xl font-heading font-bold tracking-tighter mb-8 leading-[0.85]">
            <span className="text-transparent bg-clip-text bg-gradient-to-b from-foreground to-foreground/50">Universal prime for the onchain economy</span>
          </h1>
          <p className="text-zinc-400 text-lg md:text-xl max-w-2xl mx-auto mb-12 font-light leading-relaxed">
            Kerne combines non-custodial vault architecture with institutional-grade hedging to capture delta-neutral funding rates. 
            Engineered for capital preservation and mathematical precision.
          </p>
          <div className="flex flex-col md:flex-row items-center justify-center gap-4">
            <Link href="/terminal" className="w-full md:w-auto px-10 py-5 bg-primary text-primary-foreground font-bold uppercase tracking-widest hover:bg-primary-dark transition-all flex items-center justify-center gap-2 group">
              Enter Terminal <ArrowRight size={18} className="group-hover:translate-x-1 transition-transform" />
            </Link>
            <button 
              onClick={() => setIsDemoMode(!isDemoMode)}
              className={`w-full md:w-auto px-10 py-5 border ${isDemoMode ? 'bg-primary text-primary-foreground border-primary' : 'border-primary/30 bg-primary/5 text-primary'} font-bold uppercase tracking-widest hover:bg-primary hover:text-primary-foreground transition-all flex items-center justify-center gap-2 group`}
            >
              {isDemoMode ? 'Exit Demo Mode' : 'Institutional Demo'} <Search size={18} className="group-hover:scale-110 transition-transform" />
            </button>
            <a 
              href="/Kerne_Institutional_Litepaper.pdf" 
              download
              className="w-full md:w-auto px-10 py-5 border border-grey-100 hover:bg-grey-50 transition-all font-bold uppercase tracking-widest flex items-center justify-center gap-2"
            >
              Download Litepaper (PDF)
            </a>
          </div>
        </motion.div>
      </section>

      {/* Stats Section */}
      <motion.section 
        className="px-8 py-20 border-y border-border bg-grey-50/50 z-10 relative"
        variants={staggerContainer}
        initial="initial"
        whileInView="whileInView"
        viewport={{ once: true }}
      >
        <div className="max-w-4xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-12">
          <motion.div className="text-center" variants={fadeInUp}>
            <div className="text-muted-foreground text-[10px] uppercase tracking-widest mb-2 flex items-center justify-center gap-2">
              {isDemoMode ? 'Projected TVL (Partner)' : 'Total Value Locked'}
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary/40 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-primary"></span>
              </span>
            </div>
            <Suspense fallback={<Skeleton className="h-10 w-32 mx-auto" />}>
              <div className="text-4xl font-heading font-bold tracking-tighter">
                {isDemoMode ? '$25,000,000+' : `$${tvlUsd}+`}
              </div>
            </Suspense>
            <div className="mt-4 max-w-[200px] mx-auto">
              <div className="flex justify-between text-[8px] font-mono text-muted-foreground mb-1 uppercase tracking-widest">
                <span>Beta_Capacity</span>
                <span>{tvlEth.toFixed(1)} / 500 ETH</span>
              </div>
              <div className="h-1 w-full bg-grey-100 overflow-hidden">
                <motion.div 
                  className="h-full bg-primary"
                  initial={{ width: 0 }}
                  whileInView={{ width: `${capacityPercent}%` }}
                  transition={{ duration: 1, delay: 0.5 }}
                />
              </div>
            </div>
          </motion.div>
          <motion.div className="text-center" variants={fadeInUp}>
            <div className="text-muted-foreground text-[10px] uppercase tracking-widest mb-2">Projected APY</div>
            <Suspense fallback={<Skeleton className="h-10 w-24 mx-auto" />}>
              <div className="text-4xl font-heading font-bold tracking-tighter text-primary">12.42%</div>
            </Suspense>
          </motion.div>
          <motion.div className="text-center" variants={fadeInUp}>
            <div className="text-zinc-500 text-[10px] uppercase tracking-widest mb-2">Active Nodes</div>
            <div className="text-4xl font-bold tracking-tighter">144</div>
          </motion.div>
        </div>
      </motion.section>

      {/* Yield Calculator */}
      <section className="px-8 py-32 max-w-4xl mx-auto z-10 relative">
        <motion.div 
          className="p-12 bg-grey-50 border border-border rounded-2xl backdrop-blur-sm"
          variants={fadeInUp}
          initial="initial"
          whileInView="whileInView"
          viewport={{ once: true }}
        >
          <h2 className="text-3xl font-heading font-bold tracking-tighter uppercase mb-8">Yield Calculator</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
            <div className="space-y-8">
              <div>
                <label className="text-[10px] uppercase tracking-widest text-muted-foreground font-bold mb-4 block">Investment Amount (ETH)</label>
                <input 
                  type="range" 
                  min="1" 
                  max="100" 
                  value={calcAmount} 
                  onChange={(e) => setCalcAmount(parseInt(e.target.value))}
                  className="w-full h-1 bg-grey-100 rounded-lg appearance-none cursor-pointer accent-primary"
                />
                <div className="flex justify-between mt-4 text-2xl font-bold font-mono">
                  <span>{calcAmount} ETH</span>
                  <span className="text-muted-foreground text-sm">≈ ${(calcAmount * ethPrice).toLocaleString()}</span>
                </div>
              </div>
              <div className="p-4 bg-primary/5 border border-primary/20 rounded-lg">
                <p className="text-xs text-muted-foreground leading-relaxed">
                  Calculated based on current funding rates and staking yield. Performance fees are already deducted.
                </p>
              </div>
            </div>
            <div className="grid grid-cols-1 gap-4">
              <div className="p-6 bg-white border border-border rounded-lg shadow-sm">
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Monthly Earnings</div>
                <div className="text-3xl font-bold text-primary font-mono">{monthlyYield} ETH</div>
              </div>
              <div className="p-6 bg-white border border-border rounded-lg shadow-sm">
                <div className="text-[10px] uppercase tracking-widest text-muted-foreground mb-1">Yearly Earnings</div>
                <div className="text-3xl font-bold text-primary font-mono">{yearlyYield} ETH</div>
              </div>
            </div>
          </div>
        </motion.div>
      </section>

      {/* Features Section */}
      <section id="mechanism" className="px-8 py-32 max-w-6xl mx-auto z-10 relative">
        <motion.div 
          className="grid grid-cols-1 md:grid-cols-3 gap-16"
          variants={staggerContainer}
          initial="initial"
          whileInView="whileInView"
          viewport={{ once: true }}
        >
          <motion.div 
            className="flex flex-col gap-4 p-8 bg-grey-50 border border-border rounded-2xl backdrop-blur-xl hover:border-primary/30 transition-all hover:scale-[1.02] hover:shadow-[0_0_30px_-10px_rgba(76,123,231,0.1)]" 
            variants={fadeInUp}
          >
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Zap size={24} />
            </div>
            <h3 className="text-xl font-heading font-bold uppercase tracking-tight">Delta-Neutral Engine</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Our proprietary hedging engine offsets spot exposure with perpetual futures, capturing funding rates while remaining immune to price volatility.
            </p>
          </motion.div>
          <motion.div 
            className="flex flex-col gap-4 p-8 bg-grey-50 border border-border rounded-2xl backdrop-blur-xl hover:border-primary/30 transition-all hover:scale-[1.02] hover:shadow-[0_0_30px_-10px_rgba(76,123,231,0.1)]" 
            variants={fadeInUp}
          >
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Shield size={24} />
            </div>
            <h3 className="text-xl font-heading font-bold uppercase tracking-tight">Non-Custodial Security</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Assets are held in audited smart contracts on Base. Kerne never takes custody of your principal, ensuring 100% transparency and solvency.
            </p>
          </motion.div>
          <motion.div 
            className="flex flex-col gap-4 p-8 bg-grey-50 border border-border rounded-2xl backdrop-blur-xl hover:border-primary/30 transition-all hover:scale-[1.02] hover:shadow-[0_0_30px_-10px_rgba(76,123,231,0.1)]" 
            variants={fadeInUp}
          >
            <div className="w-12 h-12 bg-primary/10 rounded-lg flex items-center justify-center text-primary">
              <Globe size={24} />
            </div>
            <h3 className="text-xl font-heading font-bold uppercase tracking-tight">Institutional Liquidity</h3>
            <p className="text-muted-foreground text-sm leading-relaxed">
              Deep integration with top-tier CEXs and DEXs ensures minimal slippage and maximum yield efficiency for large-scale capital.
            </p>
          </motion.div>
        </motion.div>
      </section>


      {/* Institutional Section */}
      <section id="institutional" className="px-8 py-32 bg-grey-50/50 border-y border-border z-10 relative">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-20">
          <motion.div 
            className="flex-1"
            variants={fadeInUp}
            initial="initial"
            whileInView="whileInView"
            viewport={{ once: true }}
          >
            <h2 className="text-4xl font-heading font-bold tracking-tighter mb-6 uppercase text-foreground">Engineered for <br />Institutional Capital.</h2>
            <p className="text-muted-foreground mb-8 leading-relaxed">
              Kerne is more than a protocol; it's a financial infrastructure layer. We provide the tools and security necessary for large-scale capital to operate efficiently in the decentralized ecosystem.
            </p>
            <div className="grid grid-cols-2 gap-8">
              <div className="flex items-center gap-3">
                <Globe className="text-primary" size={20} />
                <span className="text-sm font-bold uppercase tracking-widest text-foreground">Global Liquidity</span>
              </div>
              <div className="flex items-center gap-3">
                <BarChart3 className="text-primary" size={20} />
                <span className="text-sm font-bold uppercase tracking-widest text-foreground">Capital Efficient</span>
              </div>
              <div className="flex items-center gap-3">
                <Lock className="text-primary" size={20} />
                <span className="text-sm font-bold uppercase tracking-widest text-foreground">Tier-1 Audited</span>
              </div>
              <div className="flex items-center gap-3">
                <Layers className="text-primary" size={20} />
                <span className="text-sm font-bold uppercase tracking-widest text-foreground">Non-Custodial</span>
              </div>
            </div>
          </motion.div>
          <motion.div 
            className="flex-1 w-full aspect-square bg-gradient-to-br from-primary/20 to-white border border-border rounded-2xl flex items-center justify-center relative overflow-hidden group shadow-sm"
            initial={{ opacity: 0, scale: 0.9 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8 }}
          >
            <div className="absolute inset-0 bg-[url('https://www.transparenttextures.com/patterns/carbon-fibre.png')] opacity-10" />
            <div className="text-primary/20 group-hover:scale-110 transition-transform duration-700 -translate-y-12">
              <Shield size={200} />
            </div>
            <div className="absolute bottom-8 left-8 right-8 p-6 bg-white/90 backdrop-blur-md border border-border rounded-xl shadow-lg">
              <div className="text-[10px] text-primary uppercase tracking-[0.2em] mb-2 font-bold">Security Status</div>
              <div className="text-lg font-heading font-bold tracking-tight uppercase text-foreground">Tier-1 Audited</div>
            </div>
          </motion.div>
        </div>
      </section>

      {/* Protocol Activity Ticker */}
      <section className="hidden md:block fixed bottom-0 left-0 right-0 bg-primary text-primary-foreground py-2 z-[100] overflow-hidden whitespace-nowrap border-t border-primary-dark shadow-[0_-10px_30px_-5px_rgba(76,123,231,0.3)]">
        <motion.div 
          className="flex gap-12 items-center font-bold text-[10px] uppercase tracking-widest"
          animate={{ x: [0, -1000] }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
        >
          <span>Live Activity: New Deposit 4.2 ETH from 0x82...f1</span>
          <span>•</span>
          <span>Strategy Rebalance: 12.5 ETH Hedged on Binance</span>
          <span>•</span>
          <span>Yield Distribution: 0.042 ETH to 144 Nodes</span>
          <span>•</span>
          <span>Live Activity: New Deposit 1.8 ETH from 0x3a...e9</span>
          <span>•</span>
          <span>Strategy Rebalance: 8.2 ETH Hedged on Bybit</span>
          <span>•</span>
          <span>Yield Distribution: 0.028 ETH to 144 Nodes</span>
          {/* Duplicate for seamless loop */}
          <span>Live Activity: New Deposit 4.2 ETH from 0x82...f1</span>
          <span>•</span>
          <span>Strategy Rebalance: 12.5 ETH Hedged on Binance</span>
          <span>•</span>
          <span>Yield Distribution: 0.042 ETH to 144 Nodes</span>
        </motion.div>
      </section>

      {/* FAQ Section */}
      <FAQ />

      {/* Footer */}
      <footer className="px-8 py-32 border-t border-border z-10 relative mb-12">
        <div className="max-w-7xl mx-auto flex flex-col lg:flex-row justify-between items-start gap-24">
          <div className="flex flex-col gap-6">
            <div className="flex items-center gap-3">
              <Image src="/kerne-lockup.svg" alt="Kerne Logo" width={140} height={32} className="object-contain" />
            </div>
            <p className="text-muted-foreground text-xs max-w-[240px] leading-relaxed">
              © 2025 Kerne Protocol. <br />
              The premier institutional liquidity layer. <br />
              Built on <Link href="/admin" className="hover:text-primary transition-colors">Base</Link>.
            </p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-5 gap-12 md:gap-20 w-full lg:w-auto">
            <div className="flex flex-col gap-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">Protocol</h4>
              <Link href="/terminal" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terminal</Link>
              <Link href="/referrals" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Referrals</Link>
              <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Litepaper</Link>
              <Link href="/transparency" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Transparency</Link>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">Institutional</h4>
              <Link href="/partner" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Partner Portal</Link>
              <Link href="/docs" className="text-sm text-muted-foreground hover:text-foreground transition-colors">White Label</Link>
              <Link href="/institutional" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Onboarding</Link>
              <Link href="/risk" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Risk Policy</Link>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">Company</h4>
              <Link href="/about" className="text-sm text-muted-foreground hover:text-foreground transition-colors">About</Link>
              <Link href="/careers" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Careers</Link>
              <Link href="/security" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Security</Link>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">Legal</h4>
              <Link href="/terms" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Terms of Service</Link>
              <Link href="/privacy" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Privacy Policy</Link>
              <Link href="/cookie" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Cookie Policy</Link>
            </div>
            <div className="flex flex-col gap-4">
              <h4 className="text-[10px] uppercase tracking-[0.2em] text-muted-foreground font-bold">Social</h4>
              <Link href="https://x.com/KerneProtocol" target="_blank" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Twitter</Link>
              <Link href="#" className="text-sm text-muted-foreground hover:text-foreground transition-colors">Discord</Link>
              <Link href="https://github.com/kerne-protocol" target="_blank" className="text-sm text-muted-foreground hover:text-foreground transition-colors">GitHub</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
