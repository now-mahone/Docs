// Created: 2025-12-30 | Updated for Consistency: 2026-01-13 | Monochrome: 2026-01-22
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';

export default function TermsOfService() {
  return (
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden">
      {/* Background patterns */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24">
        {/* Simple Header */}
        <section className="relative px-6 md:px-12 pt-32 pb-16 border-b border-[#000000] bg-white">
          <div className="max-w-7xl mx-auto h-full px-6 md:px-12">
            <h1 className="font-heading font-medium tracking-tight mb-4 text-[#000000]">
              Terms of Service
            </h1>
            <p className="text-s text-[#000000] font-medium uppercase tracking-widest leading-relaxed">
              Last Updated: January 13, 2026
            </p>
          </div>
        </section>

        {/* Content Section */}
        <section className="py-24 bg-white">
          <div className="max-w-7xl mx-auto px-6 md:px-12 text-[#000000] font-medium leading-relaxed space-y-12">
            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">1. Protocol Acceptance</h2>
              <p className="text-[#000000] mb-4">
                By accessing or using the Kerne Protocol interface (the "Site") and the associated decentralized smart contracts, you acknowledge that you have read, understood, and agreed to be bound by these Terms of Service. If you do not agree to these terms, you must immediately cease all use of the Site and the Protocol.
              </p>
              <p className="text-[#000000]">
                Kerne Protocol is a suite of autonomous smart contracts deployed on the Base network. The interface provided via this Site is merely one method of interacting with the underlying decentralized infrastructure.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">2. Eligibility and Responsibility</h2>
              <p className="text-[#000000] mb-4">
                You represent and warrant that you are of legal age to form a binding contract and are not prohibited from using the Protocol under any applicable laws. You are solely responsible for ensuring that your use of the Protocol complies with the laws of your jurisdiction.
              </p>
              <p className="text-[#000000]">
                You represent that you have sufficient technical knowledge to understand the risks associated with cryptographic systems, decentralized finance (DeFi), and the specific mechanisms of the Kerne synthetic asset engine.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">3. No Financial Advice</h2>
              <p className="text-[#000000] mb-4">
                Kerne Protocol and its contributors do not provide financial, investment, legal, or tax advice. All information provided on the Site is for informational purposes only. The yield projections and historical data presented are estimates and simulations; they do not guarantee future performance.
              </p>
              <p className="text-[#000000]">
                You acknowledge that you are acting on your own volition and are responsible for your own investment decisions.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">4. Risk of Loss</h2>
              <p className="text-[#000000] mb-4">
                The use of Kerne Protocol involves significant risk, including the potential for complete loss of capital.
              </p>
              <p className="text-[#000000] mb-4">
                 Risk vectors include, but are not limited to: smart contract vulnerabilities, Oracle failures, liquidation events due to collateral ratio drops, LST/ETH depegging, and Centralized Exchange (CEX) counterparty risk where hedging positions are maintained.
              </p>
              <p className="text-[#000000]">
                Kerne utilizes an autonomous hedging engine. While designed with multiple circuit-breakers, extreme market conditions or unprecedented volatility may lead to cascading system failures.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">5. Performance Fees</h2>
              <p className="text-[#000000] mb-4">
                Kerne Protocol applies a performance fee (typically 20%) on generated yield. This fee is automatically captured by the smart contracts and used for protocol sustainability, insurance fund growth, and developer incentives.
              </p>
              <p className="text-[#000000]">
                 Fees are subject to change via governed protocol parameters. Kerne does not charge management fees or entry/exit fees on the standard vault architecture.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">6. Disclaimer of Warranties</h2>
              <p className="text-[#000000] mb-4">
                The site and the protocol are provided on an "as is" and "as available" basis. Kerne Protocol expressly disclaims all warranties of any kind, whether express or implied, including but not limited to the implied warranties of merchantability, fitness for a particular purpose, and non-infringement.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">7. Limitation of Liability</h2>
              <p className="text-[#000000]">
                In no event shall Kerne Protocol, its contributors, or its affiliates be liable for any indirect, incidental, special, consequential, or punitive damages, or any loss of profits or revenue, whether incurred directly or indirectly, or any loss of data, use, goodwill, or other intangible losses, resulting from your access to or use of (or inability to access or use) the protocol.
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
