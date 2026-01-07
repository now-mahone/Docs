// Created: 2025-12-29
'use client';

import React from 'react';
import Link from 'next/link';
import { ArrowLeft, Briefcase, Code, LineChart, ShieldCheck, Globe } from 'lucide-react';
import { motion } from 'framer-motion';

const jobs = [
  {
    title: "Senior Smart Contract Engineer",
    location: "Calgary / Remote",
    type: "Full-time",
    icon: <Code size={20} />,
    description: "Lead the development of our delta-neutral vault architectures and kUSD stability modules."
  },
  {
    title: "Quantitative Strategist",
    location: "Calgary / Remote",
    type: "Full-time",
    icon: <LineChart size={20} />,
    description: "Design and optimize hedging algorithms across multiple CEXs to maximize protocol yield."
  },
  {
    title: "Institutional Relations Manager",
    location: "New York",
    type: "Full-time",
    icon: <Briefcase size={20} />,
    description: "Manage onboarding and bespoke vault deployments for Tier-1 institutional partners."
  },
  {
    title: "Security & Risk Analyst",
    location: "Calgary / Remote",
    type: "Full-time",
    icon: <ShieldCheck size={20} />,
    description: "Oversee protocol solvency monitoring and automated circuit breaker systems."
  }
];

const fadeInUp = {
  initial: { opacity: 0, y: 20 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true },
  transition: { duration: 0.6 }
};

export default function CareersPage() {
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
            Careers_Portal_v1.0
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
          Capital <br />
          <span className="text-blue-500">Engineering.</span>
        </motion.h1>
        <motion.p 
          className="text-muted-foreground text-lg leading-relaxed max-w-2xl mx-auto"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ delay: 0.2 }}
        >
          We are building the future of institutional DeFi. Join a team of world-class engineers and strategists dedicated to financial precision.
        </motion.p>
      </section>

      {/* Culture */}
      <section className="px-8 py-20 max-w-5xl mx-auto border-y border-border/50">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-12">
          <motion.div variants={fadeInUp} initial="initial" whileInView="whileInView">
            <h3 className="text-lg font-bold uppercase mb-4">Excellence</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              We don't settle for "good enough." Every line of code and every strategy is refined for maximum performance and security.
            </p>
          </motion.div>
          <motion.div variants={fadeInUp} initial="initial" whileInView="whileInView" transition={{ delay: 0.1 }}>
            <h3 className="text-lg font-bold uppercase mb-4">Autonomy</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              We hire experts and give them the freedom to lead. We value results over bureaucracy and impact over activity.
            </p>
          </motion.div>
          <motion.div variants={fadeInUp} initial="initial" whileInView="whileInView" transition={{ delay: 0.2 }}>
            <h3 className="text-lg font-bold uppercase mb-4">Innovation</h3>
            <p className="text-sm text-muted-foreground leading-relaxed">
              We are solving the hardest problems in synthetic assets. We encourage bold ideas and rapid experimentation.
            </p>
          </motion.div>
        </div>
      </section>

      {/* Open Positions */}
      <section className="px-8 py-24 max-w-5xl mx-auto">
        <h2 className="text-3xl font-bold uppercase tracking-tight mb-12 text-center">Open Positions</h2>
        <div className="grid grid-cols-1 gap-4">
          {jobs.map((job, index) => (
            <motion.div 
              key={index}
              className="p-8 bg-zinc-900/50 border border-border/50 rounded-2xl hover:border-blue-500/50 transition-all group cursor-pointer"
              variants={fadeInUp}
              initial="initial"
              whileInView="whileInView"
              transition={{ delay: index * 0.1 }}
            >
              <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
                <div className="flex items-center gap-4">
                  <div className="p-3 bg-blue-500/10 rounded-xl text-blue-500 group-hover:bg-blue-500 group-hover:text-white transition-colors">
                    {job.icon}
                  </div>
                  <div>
                    <h3 className="text-xl font-bold uppercase tracking-tight">{job.title}</h3>
                    <div className="flex items-center gap-3 mt-1">
                      <span className="text-[10px] text-muted-foreground uppercase tracking-widest flex items-center gap-1">
                        <Globe size={10} /> {job.location}
                      </span>
                      <span className="text-[10px] text-blue-500 uppercase tracking-widest font-bold">
                        {job.type}
                      </span>
                    </div>
                  </div>
                </div>
                <button className="px-6 py-2 border border-border group-hover:border-blue-500 group-hover:text-blue-500 text-xs font-bold uppercase tracking-widest transition-all">
                  Apply Now
                </button>
              </div>
              <p className="mt-6 text-sm text-muted-foreground leading-relaxed max-w-2xl">
                {job.description}
              </p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Footer */}
      <footer className="px-8 py-20 text-center border-t border-border/50">
        <p className="text-muted-foreground text-xs uppercase tracking-[0.2em] mb-8">
          Kerne Protocol is an equal opportunity employer.
        </p>
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
