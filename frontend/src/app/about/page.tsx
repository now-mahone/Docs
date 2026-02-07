// Created: 2025-12-30 | Updated for Consistency: 2026-01-12 | Consolidated Security: 2026-01-13 | Monochrome: 2026-01-22
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowLeft, Target, Zap, Shield, Globe, Code, ArrowRight, Database, Cpu, Lock, Activity, Landmark, Network, Wallet, Eye, CheckCircle } from 'lucide-react';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';

function PillButton({ href, children, className = "", variant = "primary" }: { href: string; children: React.ReactNode; className?: string; variant?: "primary" | "secondary" | "outline" }) {
  const baseStyles = "relative px-10 font-bold rounded-sm transition-all flex items-center justify-center text-s border-none outline-none shadow-none group h-12";
  
  const variants = {
    primary: "bg-[#000000] text-[#ffffff] hover:bg-[#000000]",
    secondary: "bg-[#000000] text-[#ffffff] hover:bg-[#000000]",
    outline: "bg-transparent border border-[#000000] text-[#000000] hover:bg-[#000000]"
  };

  return (
    <Link href={href} className={`${baseStyles} ${variants[variant as keyof typeof variants]} ${className}`}>
      {children}
    </Link>
  );
}

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden">
      {/* Background patterns inspired by Morpho/Ironfish */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24">
        {/* Hero + Mission Combined Section */}
        <section className="pt-24 md:pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Hero Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-24">
              <h1 className="font-heading font-medium tracking-tight leading-[0.95] text-[#000000] mb-6 text-center">
                Prime liquidity<br />
                infrastructure.
              </h1>
              <p className="text-l md:text-l text-[#000000] max-w-2xl mx-auto font-medium leading-relaxed">
                Kerne builds the universal liquidity layer for the onchain economy, combining mathematical precision with capital efficiency.
              </p>
            </div>

            {/* Large Card Container */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
              {/* Mission Card */}
              <div className="w-full rounded-sm overflow-hidden mb-16 border border-[#444a4f]">
                <div className="grid grid-cols-1 lg:grid-cols-2">
                  {/* Left Side: Background Image with Icon, Header, Descriptor */}
                  <div className="p-8 md:p-12 flex flex-col items-start justify-center relative border-b lg:border-b-0 lg:border-r border-[#444a4f]" style={{
                    backgroundImage: 'url(/images/Kerne-Scale.png)',
                    backgroundSize: 'cover',
                    backgroundPosition: 'center'
                  }}>
                    <div className="w-12 h-12 bg-transparent rounded-full border border-[#37d097] flex items-center justify-center text-[#ffffff] mb-8">
                      <Target size={24} />
                    </div>
                    <h3 className="font-heading font-medium tracking-tight text-[#ffffff] mb-6">Why we exist</h3>
                    <p className="text-m text-[#d4dce1] font-medium leading-relaxed">
                      We are building the most capital efficient delta neutral infrastructure in DeFi.
                    </p>
                  </div>

                  {/* Right Side: Mission Statement, Link to Litepaper */}
                  <div className="p-8 md:p-12 flex flex-col justify-center bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]">
                    <p className="text-m text-[#d4dce1] font-medium leading-relaxed mb-8">
                      Kerne represents a fundamental shift in how institutional capital accesses sustainable yield in DeFi. We believe the future of finance requires infrastructure that can generate returns without relying on token emissions, unsustainable APYs, or speculative mechanisms.
                    </p>
                    <Link 
                      href="/documentation"
                      className="inline-flex items-center gap-2 text-m text-[#ffffff] font-bold hover:underline transition-all"
                    >
                      Read Documentation
                      <ArrowRight size={20} />
                    </Link>
                  </div>
                </div>
              </div>

              {/* Institutional Pillars Header */}
              <div className="mb-12">
                <h3 className="font-heading font-medium tracking-tight text-[#ffffff] mb-4">
                  Institutional pillars
                </h3>
                <p className="text-m text-[#d4dce1] font-medium leading-relaxed">
                  Three core pillars defining our commitment to institutional grade infrastructure.
                </p>
              </div>

              {/* Three Pillar Cards */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {/* Pillar D: Market Agnostic Yield */}
                <div className="rounded-sm overflow-hidden border border-[#444a4f]">
                  <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
                    <Image src="/images/Kerne-Pillar-D.png" alt="Market Agnostic Yield" fill className="object-cover" />
                  </div>
                  <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]">
                    <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Market Agnostic Yield</h3>
                    <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                      Kerne utilizes proprietary delta neutral engines to capture funding rates without market directional risk. Our infrastructure transforms volatility into consistent capital efficiency across all cycles.
                    </p>
                  </div>
                </div>

                {/* Pillar C: Verifiable Solvency */}
                <div className="rounded-sm overflow-hidden border border-[#444a4f]">
                  <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
                    <Image src="/images/Kerne-Pillar-C.png" alt="Verifiable Solvency" fill className="object-cover" />
                  </div>
                  <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]">
                    <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Verifiable Solvency</h3>
                    <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                      Every asset, position, and hedge is auditable in real time. We replace legacy black box models with deep onchain provenance, providing absolute block by block transparency.
                    </p>
                  </div>
                </div>

                {/* Pillar I: Engineered Reliability */}
                <div className="rounded-sm overflow-hidden border border-[#444a4f]">
                  <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
                    <Image src="/images/Kerne-Pillar-I.png" alt="Engineered Reliability" fill className="object-cover" />
                  </div>
                  <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000]">
                    <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Engineered Reliability</h3>
                    <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                      Built for demanding institutional portfolios, Kerne integrates multilayered risk management with battle tested architecture to ensure absolute principal protection and execution rigor.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Security Architecture Section */}
        <section className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-16">
              <h2 className="font-heading font-medium tracking-tight text-[#000000] mb-8">
                Security Architecture
              </h2>
              <p className="text-m text-[#000000] max-w-2xl font-medium">
                Engineered for the most demanding capital allocators, Kerne combines absolute transparency with autonomous risk management.
              </p>
            </div>

            {/* Card Container */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <CheckCircle size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Smart Contract Integrity</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Every line of core code is built on OpenZeppelin's audited framework. We prioritize noncustodial logic and mathematical determinism to ensure user principal remains protected and reachable.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Lock size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Dynamic Circuit Breakers</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Our autonomous hedging engine operates with 24/7 monitoring. Automated circuit breakers instantly deleverage positions in the event of extreme market volatility or LST/ETH decoupling.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Eye size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Real Time Solvency</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Unlike traditional finance, Kerne offers absolute transparency. All protocol backing is verifiable onchain, providing institutions with immediate assurance of asset quality.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Shield size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Risk Mitigation Fund</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    We maintain an active Insurance Fund that captures a portion of protocol revenue to protect against potential CEX counterparty risks and tail end events.
                  </p>
                </div>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}