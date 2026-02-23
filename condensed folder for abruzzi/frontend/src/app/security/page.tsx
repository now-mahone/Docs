// Created: 2025-12-30
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Shield, Lock, Eye, CheckCircle, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function SecurityPage() {
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
            Security_Protocol_v1.0
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
          Security <br />
          <span className="text-blue-500">First.</span>
        </motion.h1>
        <motion.p 
          className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Institutional-grade security is the foundation of Kerne Protocol. We employ multi-layered defense strategies to protect user capital.
        </motion.p>
      </section>

      {/* Content */}
      <section className="px-8 py-20 max-w-3xl mx-auto">
        <motion.div className="prose prose-invert max-w-none space-y-12" variants={fadeInUp} initial="initial" whileInView="whileInView">
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <CheckCircle className="text-blue-500" size={24} />
              1. Smart Contract Audits
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Our core contracts are built using OpenZeppelin's industry-standard libraries and undergo rigorous internal and external security reviews. We prioritize mathematical precision and storage safety.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Lock className="text-blue-500" size={24} />
              2. Delta-Neutral Hedging
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              By maintaining a delta-neutral position across LST collateral and CEX-based shorts, we mitigate directional market risk. Our hedging engine is monitored 24/7 with automated circuit breakers.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Shield className="text-blue-500" size={24} />
              3. Proof of Solvency
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              We provide real-time transparency through our Solvency Dashboard, allowing anyone to verify the protocol's backing and collateralization ratios at any time.
            </p>
          </div>

          <div className="p-8 bg-blue-500/5 border border-blue-500/20 rounded-2xl">
            <h3 className="text-lg font-bold uppercase mb-4 text-blue-500 flex items-center gap-2">
              <AlertTriangle size={20} />
              Risk Management
            </h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              While we strive for absolute security, DeFi involves inherent risks. We maintain an Insurance Fund to provide an additional layer of protection against unforeseen events.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-border/50">
        <Link href="/about" className="text-blue-500 font-bold uppercase tracking-widest hover:underline mx-4">
          About Us
        </Link>
        <Link href="/terminal" className="text-blue-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Launch Terminal
        </Link>
      </footer>
    </div>
  );
}
