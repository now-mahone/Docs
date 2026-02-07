'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Shield, Lock, Terminal as TerminalIcon, ChevronRight } from 'lucide-react';

export default function AccessPage() {
  const [code, setCode] = useState('');
  const [status, setStatus] = useState<'idle' | 'verifying' | 'error' | 'success'>('idle');
  const [message, setMessage] = useState('');
  const router = useRouter();

  const handleVerify = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!code) return;

    setStatus('verifying');
    try {
      const res = await fetch('/api/access/verify', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code }),
      });

      if (res.ok) {
        setStatus('success');
        setMessage('ACCESS GRANTED. INITIALIZING TERMINAL...');
        setTimeout(() => {
          router.push('/terminal');
          router.refresh();
        }, 1500);
      } else {
        const data = await res.json();
        setStatus('error');
        setMessage(data.message || 'INVALID ACCESS CODE');
      }
    } catch (err) {
      setStatus('error');
      setMessage('CONNECTION ERROR');
    }
  };

  return (
    <div className="min-h-screen bg-[#191919] text-[#ffffff] font-sans flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 border border-[#1f1f1f] p-8 bg-[#000000] relative overflow-hidden rounded-sm shadow-2xl">
        {/* Decorative scanline effect */}
        <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(76,123,231,0.06),rgba(13,51,236,0.02),rgba(76,123,231,0.06))] z-10 bg-[length:100%_2px,3px_100%]" />
        
        <div className="text-center space-y-4 relative z-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-[#191919] border border-[#1f1f1f] mb-4">
            <Lock className="w-8 h-8 text-[#ffffff]/60" />
          </div>
          <h1 className=" font-heading font-medium tracking-tighter uppercase text-[#ffffff]">Genesis Access Required</h1>
          <p className="text-[#ffffff] opacity-60 text-s leading-relaxed font-medium">
            Kerne Protocol is currently in a private Genesis Phase. 
            Access is restricted to institutional partners and whitelisted whales.
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-6 relative z-20">
          <div className="space-y-2">
            <label className="text-xs uppercase tracking-[0.2em] text-[#ffffff] opacity-40 ml-1 font-bold">
              Enter Access Code
            </label>
            <div className="relative">
              <TerminalIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#ffffff]/40" />
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="KERNE-XXXX-XXXX"
                className="w-full bg-[#191919] border border-[#1f1f1f] py-3 pl-10 pr-4 text-s focus:outline-none focus:border-[#4c7be7] transition-colors placeholder:text-[#ffffff]/20 font-sans"
                autoFocus
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={status === 'verifying' || status === 'success'}
            className="w-full bg-[#ffffff] text-[#000000] py-3 text-s font-bold uppercase tracking-widest hover:bg-[#f1f1ed] transition-colors disabled:opacity-50 flex items-center justify-center gap-2 rounded-full"
          >
            {status === 'verifying' ? 'Verifying...' : 'Authenticate'}
            <ChevronRight className="w-4 h-4" />
          </button>

          {message && (
            <div className={`text-center text-xs uppercase tracking-widest font-bold ${
              status === 'error' ? 'text-[#0d33ec]' : 'text-[#19b097]'
            }`}>
              {message}
            </div>
          )}
        </form>

        <div className="pt-8 border-t border-[#1f1f1f] text-center relative z-20">
          <p className="text-xs text-[#ffffff] opacity-40 uppercase tracking-widest mb-4 font-bold">
            No access code?
          </p>
          <button 
            onClick={() => router.push('/institutional')}
            className="text-xs text-[#4c7be7] hover:text-[#0d33ec] uppercase tracking-widest underline underline-offset-4 font-bold transition-colors"
          >
            Request Institutional Onboarding
          </button>
        </div>
      </div>

      <div className="mt-8 flex items-center gap-4 text-[#ffffff] opacity-20 relative z-20">
        <Shield className="w-4 h-4" />
        <span className="text-xs uppercase tracking-[0.2em] font-bold">Secure Terminal v2.0.4</span>
      </div>
    </div>
  );
}
