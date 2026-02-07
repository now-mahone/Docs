// Created: 2026-01-22
// Kerne Explained Section Component
'use client';

import React from 'react';
import Image from 'next/image';

export default function KerneExplained() {
  return (
    <section className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
      <div className="max-w-7xl mx-auto px-6 md:px-12">
        <div className="flex flex-col items-center text-center mb-16">
          <h2 className="font-heading font-medium tracking-tight text-[#000000] mb-8">
            Three Steps to Delta Neutral Yield
          </h2>
          <p className="text-[#000000] max-w-2xl font-medium">
            A step by step breakdown of how Kerne's delta neutral infrastructure generates stable yield while eliminating market risk.
          </p>
        </div>

        {/* Card Container */}
        <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
          {/* Top Section with h3 and small text */}
          <div className="mb-12">
          <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">
            The mechanisms of delta neutral yield
          </h3>
          <p className="text-m text-[#d4dce1] font-medium">
            Autonomous hedging of spot ETH holdings with perpetual futures to capture base funding rates while maintaining zero directional market exposure.
          </p>
        </div>

        {/* Three Main Cards with Images */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          {/* Card 1 */}
          <div className="rounded-sm overflow-hidden border border-[#444a4f] flex flex-col h-full">
            <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
              <Image src="/images/Kerne-Deposit.png" alt="Deposit" fill className="object-cover" />
            </div>
            <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] flex-grow">
              <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Step 1: Deposit</h3>
              <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                Users deposit ETH into Kerne's noncustodial smart contracts. Your principal remains fully backed by liquid staking tokens on Base.
              </p>
            </div>
          </div>

          {/* Card 2 */}
          <div className="rounded-sm overflow-hidden border border-[#444a4f] flex flex-col h-full">
            <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
              <Image src="/images/Kerne-Hedge.png" alt="Hedge" fill className="object-cover" />
            </div>
            <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] flex-grow">
              <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Step 2: Hedge</h3>
              <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                Our autonomous hedging engine opens equal sized short positions on perpetual futures markets, neutralizing price exposure completely.
              </p>
            </div>
          </div>

          {/* Card 3 */}
          <div className="rounded-sm overflow-hidden border border-[#444a4f] flex flex-col h-full">
            <div className="aspect-square flex items-center justify-center relative border-b border-[#444a4f]">
              <Image src="/images/Kerne-Earn.png" alt="Earn" fill className="object-cover" />
            </div>
            <div className="p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] flex-grow">
              <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">Step 3: Earn</h3>
              <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
                You earn yield from perpetual funding rates and LST staking rewards, autocompounded and distributed as vault share appreciation.
              </p>
            </div>
          </div>
        </div>

        {/* Bottom h3 and small text */}
        <div className="mb-12">
          <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">
            Why institutions choose Kerne
          </h3>
          <p className="text-m text-[#d4dce1] font-medium">
            Institutional capital allocators require mathematical precision, real time transparency, and automated risk management at scale. Built natively on Base, Kerne delivers ultra low gas costs and near instant execution speed critical for high frequency rebalancing. Your principal remains 100% noncustodial through audited smart contracts. You retain complete control of your assets at all times, eliminating counterparty risk entirely.
          </p>
        </div>

        {/* Four Smaller Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* Small Card 1 */}
          <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] p-6">
            <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-2">Real Time Verification</div>
            <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
              All protocol backing is verifiable onchain in real time.
            </p>
          </div>

          {/* Small Card 2 */}
          <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] p-6">
            <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-2">Zero Counterparty Risk</div>
            <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
              Noncustodial architecture means you maintain complete control of your principal.
            </p>
          </div>

          {/* Small Card 3 */}
          <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] p-6">
            <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-2">Automated Execution</div>
            <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
              High frequency rebalancing ensures precise delta neutral positioning 24/7.
            </p>
          </div>

          {/* Small Card 4 */}
          <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] p-6">
            <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-2">Audited Infrastructure</div>
            <p className="text-s text-[#d4dce1] font-medium leading-relaxed">
              Battle tested smart contracts reviewed by leading security firms.
            </p>
          </div>
        </div>
        </div>
      </div>
    </section>
  );
}
