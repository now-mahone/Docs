// Created: 2025-12-30
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Cookie, ShieldCheck, Settings } from 'lucide-react';
import { motion } from 'framer-motion';

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function CookiePage() {
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
            Cookie_Protocol_v1.0
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
          Cookie <br />
          <span className="text-emerald-500">Policy.</span>
        </motion.h1>
        <motion.p 
          className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          We use cookies to enhance your experience and ensure the security of the Kerne Protocol interface.
        </motion.p>
      </section>

      {/* Content */}
      <section className="px-8 py-20 max-w-3xl mx-auto">
        <motion.div className="prose prose-invert max-w-none space-y-12" variants={fadeInUp} initial="initial" whileInView="whileInView">
          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <ShieldCheck className="text-emerald-500" size={24} />
              1. Essential Cookies
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              These cookies are necessary for the website to function and cannot be switched off. They are usually only set in response to actions made by you which amount to a request for services, such as setting your privacy preferences or logging in via your wallet.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Settings className="text-emerald-500" size={24} />
              2. Preference Cookies
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              Preference cookies enable the website to remember information that changes the way the website behaves or looks, like your preferred theme (Light/Dark mode) or your last used terminal settings.
            </p>
          </div>

          <div>
            <h2 className="text-2xl font-bold uppercase tracking-tight mb-4 flex items-center gap-3">
              <Cookie className="text-emerald-500" size={24} />
              3. Analytics Cookies
            </h2>
            <p className="text-muted-foreground leading-relaxed">
              We use privacy-preserving analytics to understand how users interact with our interface. This data is anonymized and used solely to improve the protocol's user experience. We do not share this data with third-party advertisers.
            </p>
          </div>

          <div className="p-8 bg-emerald-500/5 border border-emerald-500/20 rounded-2xl">
            <h3 className="text-lg font-bold uppercase mb-4 text-emerald-500">Your Choice</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              You can set your browser to block or alert you about these cookies, but some parts of the site will not then work. These cookies do not store any personally identifiable information.
            </p>
          </div>
        </motion.div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-border/50">
        <Link href="/terms" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Terms of Service
        </Link>
        <Link href="/privacy" className="text-emerald-500 font-bold uppercase tracking-widest hover:underline mx-4">
          Privacy Policy
        </Link>
      </footer>
    </div>
  );
}
