'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Globe, BarChart3, ArrowRight, CheckCircle2, FileText } from 'lucide-react';
import { toast } from 'sonner';

export default function InstitutionalPage() {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const data = Object.fromEntries(formData.entries());

    try {
      const response = await fetch('/api/institutional/onboard', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data),
      });

      if (response.ok) {
        setSubmitted(true);
        toast.success('Application submitted successfully.');
      } else {
        toast.error('Failed to submit application.');
      }
    } catch (err) {
      toast.error('An error occurred.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <main className="min-h-screen bg-black pt-24 pb-12 px-4 sm:px-6 lg:px-8 selection:bg-emerald-500/30 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-16 items-center">
          {/* Left Column: Value Prop */}
          <div className="space-y-12">
            <div className="space-y-6">
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full border border-emerald-500/30 bg-emerald-500/5 text-emerald-500 text-[10px] uppercase tracking-[0.2em]">
                <Shield size={12} />
                Institutional Grade Infrastructure
              </div>
              <h1 className="text-5xl md:text-7xl font-black text-white tracking-tighter uppercase leading-[0.9]">
                The Gateway to <br />
                <span className="text-zinc-500">Billion-Dollar</span> <br />
                Liquidity.
              </h1>
              <p className="text-zinc-400 text-lg max-w-xl leading-relaxed">
                Kerne provides hedge funds, family offices, and corporate treasuries with a non-custodial, delta-neutral yield layer. 
                Engineered for capital preservation and high-velocity wealth accumulation.
              </p>
              <div className="flex gap-4">
                <a 
                  href="/docs/institutional_onboarding.md" 
                  download
                  className="inline-flex items-center gap-2 px-6 py-3 bg-zinc-900 border border-zinc-800 text-white text-xs font-bold uppercase tracking-widest hover:bg-zinc-800 transition-all rounded-lg"
                >
                  <FileText size={14} />
                  Download Protocol
                </a>
              </div>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-8">
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-500">
                  <Lock size={20} />
                </div>
                <h3 className="text-white font-bold uppercase tracking-tight">Whitelisted Access</h3>
                <p className="text-zinc-500 text-sm">Direct-to-vault whitelisting for verified institutional partners.</p>
              </div>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-500">
                  <BarChart3 size={20} />
                </div>
                <h3 className="text-white font-bold uppercase tracking-tight">Custom Tiers</h3>
                <p className="text-zinc-500 text-sm">Bespoke fee structures and dedicated liquidity buffers for $1M+ positions.</p>
              </div>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-500">
                  <Globe size={20} />
                </div>
                <h3 className="text-white font-bold uppercase tracking-tight">Global Compliance</h3>
                <p className="text-zinc-500 text-sm">KYC/AML integrated onboarding via Tier-1 compliance partners.</p>
              </div>
              <div className="space-y-3">
                <div className="w-10 h-10 rounded-lg bg-zinc-900 border border-zinc-800 flex items-center justify-center text-emerald-500">
                  <FileText size={20} />
                </div>
                <h3 className="text-white font-bold uppercase tracking-tight">Reporting API</h3>
                <p className="text-zinc-500 text-sm">Programmatic access to real-time solvency and performance metrics.</p>
              </div>
            </div>
          </div>

          {/* Right Column: Onboarding Form */}
          <div className="relative">
            <div className="absolute inset-0 bg-emerald-500/5 blur-[100px] rounded-full pointer-events-none" />
            
            <div className="relative bg-zinc-900/50 border border-zinc-800 p-8 md:p-12 rounded-3xl backdrop-blur-xl">
              {submitted ? (
                <motion.div 
                  initial={{ opacity: 0, scale: 0.9 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="text-center space-y-6 py-12"
                >
                  <div className="w-20 h-20 bg-emerald-500/10 rounded-full flex items-center justify-center text-emerald-500 mx-auto">
                    <CheckCircle2 size={40} />
                  </div>
                  <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-white uppercase tracking-tight">Application Received</h2>
                    <p className="text-zinc-400">Our institutional desk will review your credentials and contact you within 24 hours.</p>
                  </div>
                  <button 
                    onClick={() => setSubmitted(false)}
                    className="text-emerald-500 text-sm font-bold uppercase tracking-widest hover:text-emerald-400 transition-colors"
                  >
                    Submit another application
                  </button>
                </motion.div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="space-y-2">
                    <h2 className="text-2xl font-bold text-white uppercase tracking-tight">Institutional Onboarding</h2>
                    <p className="text-zinc-500 text-sm">Complete the form below to initiate the whitelisting process.</p>
                  </div>

                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-1">
                        <label className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Full Name</label>
                        <input 
                          required
                          name="name"
                          type="text" 
                          className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 text-white focus:border-emerald-500/50 outline-none transition-colors"
                          placeholder="John Doe"
                        />
                      </div>
                      <div className="space-y-1">
                        <label className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Work Email</label>
                        <input 
                          required
                          name="email"
                          type="email" 
                          className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 text-white focus:border-emerald-500/50 outline-none transition-colors"
                          placeholder="john@firm.com"
                        />
                      </div>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Organization</label>
                      <input 
                        required
                        name="organization"
                        type="text" 
                        className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 text-white focus:border-emerald-500/50 outline-none transition-colors"
                        placeholder="Hedge Fund / Family Office"
                      />
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Target Allocation (USD)</label>
                      <select 
                        required
                        name="volume"
                        className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 text-white focus:border-emerald-500/50 outline-none transition-colors appearance-none"
                      >
                        <option value="">Select Range</option>
                        <option value="1M-5M">$1M - $5M</option>
                        <option value="5M-25M">$5M - $25M</option>
                        <option value="25M-100M">$25M - $100M</option>
                        <option value="100M+">$100M+</option>
                      </select>
                    </div>

                    <div className="space-y-1">
                      <label className="text-[10px] uppercase tracking-widest text-zinc-500 font-bold">Wallet Address (Optional)</label>
                      <input 
                        name="address"
                        type="text" 
                        className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 text-white focus:border-emerald-500/50 outline-none transition-colors font-mono text-xs"
                        placeholder="0x..."
                      />
                    </div>
                  </div>

                  <button 
                    disabled={loading}
                    type="submit"
                    className="w-full py-4 bg-white text-black font-black uppercase tracking-[0.2em] rounded-xl hover:bg-emerald-500 transition-all active:scale-[0.98] flex items-center justify-center gap-2 disabled:opacity-50"
                  >
                    {loading ? 'Processing...' : 'Initiate Onboarding'}
                    {!loading && <ArrowRight size={18} />}
                  </button>

                  <p className="text-[8px] text-zinc-600 text-center uppercase tracking-widest">
                    By submitting, you agree to our Institutional Terms of Service and Privacy Policy.
                  </p>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </main>
  );
}
