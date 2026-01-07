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
    <div className="min-h-screen bg-black text-white font-mono flex flex-col items-center justify-center p-4">
      <div className="max-w-md w-full space-y-8 border border-zinc-800 p-8 bg-zinc-950/50 backdrop-blur-xl relative overflow-hidden">
        {/* Decorative scanline effect */}
        <div className="absolute inset-0 pointer-events-none bg-[linear-gradient(rgba(18,16,16,0)_50%,rgba(0,0,0,0.25)_50%),linear-gradient(90deg,rgba(255,0,0,0.06),rgba(0,255,0,0.02),rgba(0,0,255,0.06))] z-10 bg-[length:100%_2px,3px_100%]" />
        
        <div className="text-center space-y-4 relative z-20">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-zinc-900 border border-zinc-800 mb-4">
            <Lock className="w-8 h-8 text-zinc-400" />
          </div>
          <h1 className="text-2xl font-bold tracking-tighter uppercase">Genesis Access Required</h1>
          <p className="text-zinc-500 text-sm leading-relaxed">
            Kerne Protocol is currently in a private Genesis Phase. 
            Access is restricted to institutional partners and whitelisted whales.
          </p>
        </div>

        <form onSubmit={handleVerify} className="space-y-6 relative z-20">
          <div className="space-y-2">
            <label className="text-[10px] uppercase tracking-[0.2em] text-zinc-500 ml-1">
              Enter Access Code
            </label>
            <div className="relative">
              <TerminalIcon className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-zinc-600" />
              <input
                type="text"
                value={code}
                onChange={(e) => setCode(e.target.value.toUpperCase())}
                placeholder="KERNE-XXXX-XXXX"
                className="w-full bg-black border border-zinc-800 py-3 pl-10 pr-4 text-sm focus:outline-none focus:border-white transition-colors placeholder:text-zinc-800"
                autoFocus
              />
            </div>
          </div>

          <button
            type="submit"
            disabled={status === 'verifying' || status === 'success'}
            className="w-full bg-white text-black py-3 text-sm font-bold uppercase tracking-widest hover:bg-zinc-200 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
          >
            {status === 'verifying' ? 'Verifying...' : 'Authenticate'}
            <ChevronRight className="w-4 h-4" />
          </button>

          {message && (
            <div className={`text-center text-[10px] uppercase tracking-widest ${
              status === 'error' ? 'text-red-500' : 'text-emerald-500'
            }`}>
              {message}
            </div>
          )}
        </form>

        <div className="pt-8 border-t border-zinc-900 text-center relative z-20">
          <p className="text-[10px] text-zinc-600 uppercase tracking-widest mb-4">
            No access code?
          </p>
          <button 
            onClick={() => router.push('/institutional')}
            className="text-[10px] text-zinc-400 hover:text-white uppercase tracking-widest underline underline-offset-4"
          >
            Request Institutional Onboarding
          </button>
        </div>
      </div>

      <div className="mt-8 flex items-center gap-4 text-zinc-800 relative z-20">
        <Shield className="w-4 h-4" />
        <span className="text-[10px] uppercase tracking-[0.3em]">Secure Terminal v2.0.4</span>
      </div>
    </div>
  );
}
