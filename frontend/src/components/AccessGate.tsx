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

  if (isLoading) return <div className="min-h-screen bg-white" />;

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen bg-[#f9f9f4] flex flex-col items-center justify-center p-6 font-sans">
        <div className="w-full max-w-md space-y-8 text-center">
          <div className="flex justify-center mb-8">
            <Image src="/kerne-lockup.svg" alt="Kerne Logo" width={180} height={40} priority />
          </div>
          
          <div className="space-y-2">
            <h1 className="text-2xl font-heading font-bold tracking-tight text-[#191919]">
              Institutional Access Only
            </h1>
            <p className="text-sm text-zinc-500">
              The platform is currently undergoing a scheduled architectural upgrade. Please enter your access code to proceed.
            </p>
          </div>

          <form onSubmit={handleSubmit} className="mt-8 space-y-4">
            <div className="relative">
              <input
                type="password"
                value={code}
                onChange={(e) => setCode(e.target.value)}
                placeholder="Enter Access Code"
                className={`w-full px-4 py-4 bg-white border ${error ? 'border-red-500' : 'border-zinc-200'} rounded-xl shadow-sm focus:outline-none focus:ring-2 focus:ring-[#4c7be7]/20 transition-all text-center font-mono tracking-widest`}
                autoFocus
              />
              {error && (
                <p className="absolute -bottom-6 left-0 right-0 text-[10px] text-red-500 font-bold uppercase tracking-tight">
                  Invalid Access Code. Please try again.
                </p>
              )}
            </div>
            
            <button
              type="submit"
              className="w-full py-4 bg-[#4c7be7] text-white font-heading font-bold rounded-xl shadow-md hover:bg-[#0d33ec] transition-all transform active:scale-[0.98]"
            >
              AUTHENTICATE
            </button>
          </form>

          <p className="pt-8 text-[10px] text-zinc-400 uppercase tracking-widest">
            © 2026 Kerne Protocol. Secure Transmission Active.
          </p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
