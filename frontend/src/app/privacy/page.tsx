// Created: 2025-12-30
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Eye, Shield, Lock } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-background text-foreground font-sans selection:bg-emerald-500/30">
      {/* Navigation */}
      <nav className="flex justify-between items-center px-8 py-6 border-b border-border/50 backdrop-blur-md sticky top-0 z-50">
        <Link href="/" className="flex items-center gap-2 group">
          <ArrowLeft size={18} className="text-muted-foreground group-hover:text-foreground transition-colors" />
          <span className="text-xl font-bold tracking-tighter uppercase">Kerne</span>
        </Link>
        <div className="flex items-center gap-4">
          <div className="text-[10px] text-emerald-500 uppercase tracking-[0.2em] font-bold">
            Privacy_Protocol_v1.0
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
          Privacy <br />
          <span className="text-emerald-500">Policy.</span>
        </motion.h1>
        <motion.p 
          className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          Your privacy is paramount. We are committed to protecting your data and ensuring transparency in how we operate.
        </motion.p>
      </section>

      {/* Content */}
      <section className="px-8 py-20 max-w-3xl mx-auto">
        <motion.div className="prose prose-invert max-w-none space-y-12" variants={fadeInUp} initial="initial" whileInView="whileInView">
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Eye className="text-emerald-500" size={24} />
              1. Data Collection
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Kerne Protocol is a decentralized platform. We do not collect personal information such as names, email addresses, or physical locations. Our interface interacts directly with your self-custodial wallet.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Shield className="text-emerald-500" size={24} />
              2. On-Chain Data
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Please be aware that all transactions on the Base network are public. Your wallet address and transaction history are visible to anyone on the blockchain. This is a fundamental characteristic of decentralized finance.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Lock className="text-emerald-500" size={24} />
              3. Security Measures
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              We employ industry-standard security protocols to protect our interface and your interaction with the protocol. We never have access to your private keys or seed phrases.
            </p>
          </div>

          <div className="p-8 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl">
            <h3 className="text-lg font-bold uppercase mb-4 text-emerald-500">Commitment</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              We will never sell your data to third parties. Our goal is to provide a secure, private, and institutional-grade experience for all users.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-border/50">
        <Link href="/terms" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Terms of Service
        </Link>
        <Link href="/risk" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Cookie Policy
        </Link>
      </footer>
    </div>
  );
}
