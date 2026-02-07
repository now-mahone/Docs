// Created: 2026-01-14
'use client';

import React from 'react';
import Link from 'next/link';
import Image from 'next/image';

export default function Footer() {
  return (
    <footer className="py-32 bg-gradient-to-b from-[#000000] to-[#000000] text-[#ffffff] border-t border-[#000000/10]">
      <div className="max-w-7xl mx-auto px-6 md:px-12 flex flex-col items-center">
        <div className="grid grid-cols-1 lg:grid-cols-7 gap-8 w-full text-left">
          <div className="col-span-1 lg:col-span-3 flex flex-col justify-between">
            <div>
              <div className="mb-8 flex items-center">
                <Image src="/kerne-k-000.svg" alt="Kerne" width={20} height={20} className="brightness-0 invert" />
              </div>
              <p className="text-[#ffffff] font-medium max-w-sm mb-0">
                Kerne is building the prime liquidity layer for the onchain economy, where yield is engineered, not speculated.
              </p>
            </div>
          </div>
          <div className="flex flex-col gap-6">
            <h5 className="text-s font-bold tracking-tight text-[#ffffff] font-heading">Protocol</h5>
            <a href="/terminal" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Terminal</a>
            <Link href="/litepaper" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Documentation</Link>
          </div>
          <div className="flex flex-col gap-6">
            <h5 className="text-s font-bold tracking-tight text-[#ffffff] font-heading">Institutional</h5>
            <Link href="/about" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">About</Link>
            <Link href="/transparency" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Transparency</Link>
            <Link href="/institutional" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Onboarding</Link>
          </div>
          <div className="flex flex-col gap-6">
            <h5 className="text-s font-bold tracking-tight text-[#ffffff] font-heading">Socials</h5>
            <a href="https://x.com/KerneProtocol" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">X / Twitter</a>
            <a href="https://farcaster.xyz/kerne" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Farcaster</a>
            <a href="https://github.com/kerne-protocol" target="_blank" rel="noopener noreferrer" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">GitHub</a>
          </div>
          <div className="flex flex-col gap-6">
            <h5 className="text-s font-bold tracking-tight text-[#ffffff] font-heading">Legal</h5>
            <Link href="/privacy" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Privacy Policy</Link>
            <Link href="/terms" className="text-[#ffffff] font-medium hover:text-[#000000/10] transition-colors text-s">Terms of Service</Link>
          </div>
        </div>
        <div className="mt-24 pt-12 border-t border-white/10 flex flex-col sm:flex-row justify-between items-center gap-6 w-full">
          <div className="text-[#ffffff] text-xs font-medium tracking-tight text-center sm:text-left">
            © 2026 Kerne Protocol. All rights reserved. Built on Base.
          </div>
        </div>
      </div>
    </footer>
  );
}
