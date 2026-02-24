// Created: 2026-02-24
'use client';

import React from 'react';
import Link from 'next/link';

export default function GenesisBanner() {
  return (
    <div className="fixed top-0 left-0 right-0 z-[150] bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] animate-mesh">
      <div className="max-w-7xl mx-auto px-6 py-3 flex items-center justify-center text-center">
        <p className="text-s font-bold text-[#000000]">
          <span className="hidden sm:inline">Genesis Phase Active: </span>
          <span className="font-bold">0% Performance Fee</span>
          <span className="hidden md:inline"> for deposits under $100k TVL</span>
          <span className="mx-2">•</span>
          <Link href="/terminal" className="underline hover:no-underline">
            Deposit Now
          </Link>
        </p>
      </div>
    </div>
  );
}
