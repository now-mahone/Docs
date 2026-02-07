// Created: 2026-01-09
'use client';

import React, { useState, useEffect } from 'react';
import Image from 'next/image';

const ACCESS_CODE = '12321'; // Hardcoded for internal overhaul phase

export function AccessGate({ children }: { children: React.ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);
  const [code, setCode] = useState('');
  const [error, setError] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const auth = localStorage.getItem('kerne_access');
    if (auth === ACCESS_CODE) {
      setIsAuthenticated(true);
    }
    setIsLoading(false);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (code === ACCESS_CODE) {
      localStorage.setItem('kerne_access', code);
      setIsAuthenticated(true);
      setError(false);
    } else {
      setError(true);
      setCode('');
    }
  };

  if (isLoading) return <div className="min-h-screen bg-[#f9f9f4]" />;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#f9f9f4] flex flex-col items-center justify-center p-6 font-sans">
        <div className="w-full max-w-md space-y-10 text-center">
          <div className="flex justify-center mb-12">
            <Image src="/kerne-lockup.svg" alt="Kerne Logo" width={180} height={40} priority />
          </div>
          
          <div className="space-y-3">
            <h1 className=" font-heading font-medium tracking-tight text-[#000000]">
              Institutional access
            </h1>
            <p className="text-[#1f1f1f] font-medium text-s leading-relaxed">
              The Kerne infrastructure is currently undergoing a scheduled architectural upgrade. Please enter your terminal access code to proceed.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-12 space-y-6">
            <div className="relative">
              <input
                type="password"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Terminal Access Code"
                className={`w-full px-6 py-5 bg-[#f1f1ed] border ${error ? 'border-[#0d33ec]' : 'border-[#f1f1ed]'} rounded-sm focus:outline-none focus:ring-2 focus:ring-[#4c7be7]/20 transition-all text-center font-mono tracking-[0.5em] text-l font-bold text-[#000000]`}
                autoFocus
              />
              {error && (
                <p className="absolute -bottom-8 left-0 right-0 text-xs text-[#0d33ec] font-bold uppercase tracking-tight">
                  Invalid authentication code. Please verify credentials.
                </p>
              )}
            </div>
            
            <button
              type="submit"
              className="w-full py-5 bg-[#4c7be7] text-[#f9f9f4] font-bold rounded-sm hover:bg-[#0d33ec] transition-all transform active:scale-[0.98] text-s tracking-tight uppercase"
            >
              Authenticate Session
            </button>
          </form>

          <div className="pt-12 flex flex-col items-center gap-4">
             <div className="h-1.5 w-1.5 rounded-full bg-[#4c7be7]" />
             <p className="text-xs text-zinc-400 font-bold uppercase tracking-widest leading-relaxed">
               Verified Cryptographic Transmission <br />
               © 2026 Kerne Protocol
             </p>
          </div>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
