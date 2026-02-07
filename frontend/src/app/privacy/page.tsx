// Created: 2025-12-30 | Updated for Consistency: 2026-01-13 | Monochrome: 2026-01-22
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';

export default function PrivacyPolicy() {
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
              Privacy Policy
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
              <h2 className="font-heading font-medium text-[#000000] mb-6">1. Privacy Philosophy</h2>
              <p className="text-[#000000] mb-4">
                Kerne Protocol is built on the principles of decentralization, anonymity, and data sovereignty. We believe that financial privacy is a fundamental human right. Our interface is designed to provide institutional-grade access to the protocol without compromising your personal identity.
              </p>
              <p className="text-[#000000]">
                This document outlines our commitment to your privacy and the limited technical data processed when you interact with our decentralized application (dApp).
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">2. Data Non-Collection</h2>
              <p className="text-[#000000] mb-4">
                Kerne Protocol does not collect, store, or process any Personally Identifiable Information (PII). This includes:
              </p>
              <ul className="list-disc list-inside text-[#000000] space-y-2 ml-4">
                <li>Your name or physical address.</li>
                <li>Your email address or phone number.</li>
                <li>Your IP address (which is anonymized at the edge).</li>
                <li>Government-issued identification numbers.</li>
              </ul>
              <p className="text-[#000000] mt-4">
                Your primary identifier is your self-custodial wallet address. This address is public on the Base network by design.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">3. Public Ledger Transparency</h2>
              <p className="text-[#000000] mb-4">
                By interacting with Kerne Protocol, you acknowledge that all transactions—including deposits, minting kUSD, and withdrawals—are recorded on the Base blockchain. Blockchains are public ledgers that are immutable and transparent.
              </p>
              <p className="text-[#000000]">
                Anyone with access to the Base network can view your transaction history, balance, and protocol interactions associated with your public wallet address.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">4. Processing of Technical Data</h2>
              <p className="text-[#000000] mb-4">
                To provide a high-performance interface and prevent adversarial attacks, our infrastructure may process transitory technical data. This includes:
              </p>
              <ul className="list-disc list-inside text-[#000000] space-y-2 ml-4">
                <li>Usage Statistics: Anonymized interaction data (buttons clicked, pages viewed) used to refine the protocol UI.</li>
                <li>RPC Calls: Data sent between your wallet and the blockchain nodes. We recommend using privacy-focused RPC providers.</li>
                <li>Wallet Metadata: Information provided by wallet connectors (e.g., WalletConnect, RainbowKit) to manage connection states.</li>
              </ul>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">5. Third-Party Services</h2>
              <p className="text-[#000000] mb-4">
                Our interface utilizes industry-standard libraries and infrastructure providers. These third parties include:
              </p>
              <ul className="list-disc list-inside text-[#000000] space-y-2 ml-4">
                <li>Hosting Providers: (e.g., Vercel) to deliver the frontend interface.</li>
                <li>Analytics: (e.g., Cloudflare) for DDOS protection and traffic routing.</li>
                <li>Wallet Service Providers: To enable secure connection to your self-custodial assets.</li>
              </ul>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">6. Your Rights</h2>
              <p className="text-[#000000]">
                Because we do not store your data, we cannot "delete" it upon request. Your data sovereignty is absolute because you control your private keys. To cease sharing data with the Protocol, simply disconnect your wallet and stop accessing the Site.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">7. Cookie Policy</h2>
              <p className="text-[#000000] mb-4">
                Our website uses minimal cookies to ensure functionality and enhance user experience. These include:
              </p>
              <ul className="list-disc list-inside text-[#000000] space-y-2 ml-4">
                <li>Essential Cookies: Required for website security and wallet session persistence.</li>
                <li>Preference Cookies: Store your interface preferences and terminal settings.</li>
                <li>Analytics Cookies: Privacy-preserving, anonymized data used solely to improve the institutional user experience.</li>
              </ul>
              <p className="text-[#000000] mt-4">
                You may configure your browser to block or alert you about cookies, though some site features may not function correctly. These cookies do not store personally identifiable information (PII).
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
