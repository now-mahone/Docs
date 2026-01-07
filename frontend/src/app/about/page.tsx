// Created: 2025-12-30
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Target, Users, Zap, Shield, Globe, Code } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-blue-500/30">
      {/* Navigation */}
      <nav className="flex justify-between items-center px-8 py-6 border-b border-border/50 backdrop-blur-md sticky top-0 z-50">
        <Link href="/" className="flex items-center gap-2 group">
          <ArrowLeft size={18} className="text-muted-foreground group-hover:text-foreground transition-colors" />
          <span className="text-xl font-bold tracking-tighter uppercase">Kerne</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="text-[10px] text-blue-500 uppercase tracking-[0.2em] font-bold">
            About_Protocol_v1.0
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
          Institutional <br />
          <span className="text-blue-500">Gravity.</span>
        </motion.h1>
        <motion.p 
          className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Kerne Protocol is engineering the next generation of delta-neutral stablecoins, combining institutional-grade hedging with decentralized accessibility.
        </motion.p>
      </section>

      {/* Mission */}
      <section className="px-8 py-20 max-w-5xl mx-auto grid grid-cols-1 md:grid-cols-2 gap-12 items-center border-y border-border/50">
        <motion.div variants={fadeInUp} initial="initial" whileInView="whileInView">
          <h2 className="text-3xl font-bold uppercase tracking-tight mb-6">Our Mission</h2>
          <p className="text-muted-foreground leading-relaxed mb-6">
            Our mission is to provide a stable, high-yield synthetic dollar that remains resilient in all market conditions. By leveraging Ethereum LSTs and sophisticated hedging strategies, we create a product that bridges the gap between traditional finance and DeFi.
          </p>
          <div className="flex items-center gap-4">
            <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500">
              <Target size={24} />
            </div>
            <div>
              <div className="font-bold uppercase text-sm">Precision</div>
              <div className="text-xs text-muted-foreground">Mathematical accuracy in every trade.</div>
            </div>
          </div>
        </motion.div>
        <motion.div 
          className="grid grid-cols-2 gap-4"
          variants={fadeInUp}
          initial="initial"
          whileInView="whileInView"
        >
          <div className="p-6 bg-zinc-900/50 border border-border/50 rounded-2xl">
            <Zap className="text-blue-500 mb-4" size={24} />
            <div className="text-2xl font-bold mb-1">24/7</div>
            <div className="text-xs text-muted-foreground uppercase">Automated Hedging</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-border/50 rounded-2xl">
            <Shield className="text-blue-500 mb-4" size={24} />
            <div className="text-2xl font-bold mb-1">100%</div>
            <div className="text-xs text-muted-foreground uppercase">Collateralized</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-border/50 rounded-2xl">
            <Globe className="text-blue-500 mb-4" size={24} />
            <div className="text-2xl font-bold mb-1">Global</div>
            <div className="text-xs text-muted-foreground uppercase">Accessibility</div>
          </div>
          <div className="p-6 bg-zinc-900/50 border border-border/50 rounded-2xl">
            <Code className="text-blue-500 mb-4" size={24} />
            <div className="text-2xl font-bold mb-1">Proprietary</div>
            <div className="text-xs text-muted-foreground uppercase">Engine Core</div>
          </div>
        </motion.div>
      </section>

      {/* Team/Values */}
      <section className="px-8 py-20 max-w-3xl mx-auto text-center">
        <h2 className="text-3xl font-bold uppercase tracking-tight mb-12">Core Values</h2>
        <div className="space-y-8 text-left">
          <div className="p-8 bg-blue-500/5 border border-blue-500/20 rounded-2xl">
            <h3 className="text-xl font-bold uppercase mb-2 text-blue-500">Transparency</h3>
            <p className="text-muted-foreground leading-relaxed">
              Every position, every hedge, and every dollar of collateral is verifiable on-chain or through our proof-of-solvency dashboard.
            </p>
          </div>
          <div className="p-8 bg-blue-500/5 border border-blue-500/20 rounded-2xl">
            <h3 className="text-xl font-bold uppercase mb-2 text-blue-500">Security</h3>
            <p className="text-muted-foreground leading-relaxed">
              We prioritize the safety of user funds above all else, employing rigorous audits and automated risk management systems.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-border/50">
        <Link href="/security" className="text-blue-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Security
        </Link>
        <Link href="/terminal" className="text-blue-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Launch Terminal
        </Link>
      </footer>
    </div>
  );
}
