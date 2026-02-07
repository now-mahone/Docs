// Created: 2026-02-07
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';

export default function DocumentationPage() {
  // Once GitBook is deployed, replace this URL with the actual GitBook URL
  // e.g., 'https://kerne.gitbook.io/kerne' or your custom GitBook domain
  const gitbookUrl = null; // Set to GitBook URL when ready

  if (gitbookUrl) {
    return (
      <div className="min-h-screen bg-[#ffffff]">
        <Navbar />
        <iframe
          src={gitbookUrl}
          className="w-full border-0 pt-32"
          style={{ height: 'calc(100vh - 128px)' }}
          title="Kerne Documentation"
          allow="clipboard-write"
        />
      </div>
    );
  }

  // Fallback: render litepaper content directly until GitBook is deployed
  return (
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden">
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24">
        <section className="relative px-6 md:px-12 pt-32 pb-16 border-b border-[#000000] bg-white">
          <div className="max-w-7xl mx-auto h-full px-6 md:px-12">
            <h1 className="font-heading font-medium tracking-tight mb-4 text-[#000000]">
              Documentation
            </h1>
            <p className="text-s text-[#000000] font-medium uppercase tracking-widest leading-relaxed">
              KERNE PROTOCOL | LITEPAPER V1.0
            </p>
          </div>
        </section>

        <section className="py-24 bg-white border-b border-[#000000]">
          <div className="max-w-7xl mx-auto px-6 md:px-12 text-[#000000] font-medium leading-relaxed space-y-20">
            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">1. Abstract</h2>
              <p className="text-[#000000] mb-4 text-l">
                Kerne Protocol is a decentralized synthetic dollar and prime liquidity engine built on the Base network. By industrializing delta neutral hedging strategies, Kerne bridges the gap between high-fidelity institutional finance and the permissionless possibilities of decentralized finance (DeFi).
              </p>
              <p className="text-[#000000] text-l">
                Our core objective is to provide the most capital-efficient, low-risk infrastructure for the on-chain economy, centered around kUSD—a resilient, yield-bearing synthetic asset.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">2. The Delta-Neutral Mechanism</h2>
              <p className="text-[#000000] mb-12 text-l">
                Kerne eliminates market directional risk by meticulously balancing spot assets with equivalent perpetual short positions. This allows the protocol to capture two distinct yield streams simultaneously: base staking rewards from LSTs and funding rates from short positions on Tier-1 exchanges.
              </p>
              
              <div className="p-8 md:p-16 bg-[#ffffff] border border-[#000000] rounded-sm w-full shadow-none">
                <h4 className="font-bold text-[#000000] uppercase tracking-widest mb-12">Yield Composition Model</h4>
                <div className="space-y-16">
                  <div className="space-y-6">
                    <div className="h-3 bg-[#ffffff] rounded-full overflow-hidden">
                      <div className="h-full bg-[#000000] w-[25%] rounded-full"></div>
                    </div>
                    <div className="flex justify-between items-center text-l">
                      <span className="text-[#000000] font-medium">LST Rewards (3-4%)</span>
                      <span className="text-[#000000] font-medium tracking-tight">Base Yield</span>
                    </div>
                  </div>
                  <div className="space-y-6">
                    <div className="h-3 bg-[#ffffff] rounded-full overflow-hidden">
                      <div className="h-full bg-[#000000] w-[75%] rounded-full"></div>
                    </div>
                    <div className="flex justify-between items-center text-l">
                      <span className="text-[#000000] font-medium">Funding Rates (8-15%)</span>
                      <span className="text-[#000000] font-medium tracking-tight">Premium Yield</span>
                    </div>
                  </div>
                </div>
                <p className="mt-16 text-s text-[#000000] leading-relaxed">
                  * Historical simulations show an average combined APY of 12.4% during moderate market conditions.
                </p>
              </div>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">3. Real-time Proof of Solvency</h2>
              <p className="text-[#000000] mb-4 text-l">
                Traditional finance relies on periodic manual audits. Kerne introduces a block-by-block Proof of Solvency framework. Our hedging engine reconciles on-chain reserves with mirrored CEX balances every 4 hours.
              </p>
              <p className="text-[#000000] text-l">
                All data is accessible via public RPC endpoints, allowing institutional partners to monitor the protocol's collateralization ratio with sub-second precision.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">4. kUSD: The Synthetic Dollar</h2>
              <p className="text-[#000000] mb-4 text-l">
                kUSD is minted against the value of user collateral in the KerneVault. It provides a stable unit of account while allowing the underlying principal to continue generating delta neutral yield.
              </p>
              <p className="text-[#000000] text-l">
                The protocol maintains a strict over-collateralization ratio (typically 150%) and utilizes a multi-layered custody model with Tier-1 partners to ensure absolute principal protection.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">5. Recursive Leverage Engine</h2>
              <p className="text-[#000000] mb-4 text-l">
                For sophisticated allocators, Kerne offers a native "Folding" mechanism. This enables users to recursively deposit collateral and mint kUSD to buy more collateral, significantly magnifying the net delta neutral yield.
              </p>
              <p className="text-[#000000] text-l">
                The engine enforces a minimum health factor of 1.1x, providing a automated deleveraging buffer to protect the protocol during extreme volatility.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">6. Network Integration</h2>
              <p className="text-[#000000] mb-4 text-l">
                Operating natively on Base—Coinbase's Layer 2 network—Kerne achieves ultra-low latency execution and minimal gas overhead. This cost efficiency is passed directly to users, resulting in higher net APYs compared to Ethereum mainnet alternatives.
              </p>
              <p className="text-[#000000] text-l">
                Deep integration with Aerodrome liquidity pools ensures that kUSD maintains deep, efficient liquidity with minimal price impact for institutional-sized entries and exits.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">7. Institutional Compliance</h2>
              <p className="text-[#000000] mb-4 text-l">
                Kerne is designed with a "Whitelisting-First" architecture for institutional vaults. This allows organizations to maintain strict KYC/AML compliance while participating in permissionless yield generation.
              </p>
              <p className="text-[#000000] text-l">
                The protocol is compatible with Tier-1 institutional custodians, including Safe (formerly Gnosis Safe) and Fireblocks, ensuring multi-sig security for high-value treasuries.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">8. Risk Mitigation Pillars</h2>
              <p className="text-[#000000] mb-8 text-l">
                Safety is the foundation of Kerne. Our multi-layered architecture ensures mathematical proof of solvency through three core pillars: Oracle Guard monitoring, automated Insurance Fund reserves, and Hybrid Custody models.
              </p>
              <p className="text-l text-[#000000]">
                These components work in tandem to eliminate directional market risk while ensuring the synthetic dollar remains fully collateralized under all conditions.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">9. Results-Oriented Fees</h2>
              <p className="text-[#000000] mb-4 text-l">
                The protocol implements a performance-based fee model. A standard fee is applied only to the net yield generated by the strategy. There are no fixed management fees, subscription costs, or entry/exit penalties for primary users.
              </p>
              <p className="text-[#000000] text-l">
                 This ensures absolute alignment between the protocol's engineering objectives and the allocator's capital results.
              </p>
            </div>

            <div>
              <h2 className="font-heading font-medium text-[#000000] mb-6">10. Strategic Conclusion</h2>
              <p className="text-[#000000] mb-4 text-l">
                The Kerne Protocol represents a paradigm shift in how capital is managed on-chain. By removing the directional risks of crypto-volatility while maintaining the yields of the decentralized economy, we are building the liquid standard for the next generation of finance.
              </p>
              <p className="text-[#000000] text-l">
                The universal prime liquidity layer is now live on Base.
              </p>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}