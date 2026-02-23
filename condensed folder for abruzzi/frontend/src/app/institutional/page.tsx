// Created: 2026-01-04 | Monochrome: 2026-01-22
'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import { Shield, Lock, Globe, BarChart3, ArrowRight, CheckCircle2, FileText, Wallet } from 'lucide-react';
import { toast } from 'sonner';
import Link from 'next/link';
import Image from 'next/image';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import TypedHeading from '@/components/TypedHeading';

export default function InstitutionalPage() {
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [volume, setVolume] = useState('');

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setLoading(true);
    
    const formData = new FormData(e.currentTarget);
    const data = Object.fromEntries(formData.entries());
    data.volume = volume;

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
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden flex flex-col">
      {/* Background patterns */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24 flex-grow">
        {/* Hero + Content Combined Section */}
        <section className="pt-24 md:pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            {/* Hero Header and Subtext */}
            <div className="flex flex-col items-center text-center mb-24">
              <h1 className="font-heading font-medium text-[#000000] tracking-tight leading-[0.95] mb-6">
                Yield engineering for <br />
                institutional capital.
              </h1>
              <p className="text-[#000000] text-l md:text-l font-medium max-w-2xl mx-auto leading-relaxed">
                Kerne provides family offices and institutional treasuries with a noncustodial, delta neutral yield environment engineered for capital preservation.
              </p>
            </div>

            {/* Card Container wrapping all content */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
              {/* Features Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] space-y-4 shadow-none">
                  <div className="w-12 h-12 rounded-full border border-[#37d097] bg-transparent flex items-center justify-center text-[#ffffff]">
                    <Lock size={24} />
                  </div>
                  <h3 className="text-[#ffffff] font-heading font-medium">Whitelisted Access</h3>
                  <p className="text-[#d4dce1] font-medium text-s leading-relaxed">Direct to vault whitelisting for verified institutional partners and sub accounts.</p>
                </div>
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] space-y-4 shadow-none">
                  <div className="w-12 h-12 rounded-full border border-[#37d097] bg-transparent flex items-center justify-center text-[#ffffff]">
                    <BarChart3 size={24} />
                  </div>
                  <h3 className="text-[#ffffff] font-heading font-medium">Bespoke Tiers</h3>
                  <p className="text-[#d4dce1] font-medium text-s leading-relaxed">Custom fee structures and dedicated liquidity buffers for allocation exceeding 500 ETH.</p>
                </div>
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] space-y-4 shadow-none">
                  <div className="w-12 h-12 rounded-full border border-[#37d097] bg-transparent flex items-center justify-center text-[#ffffff]">
                    <Globe size={24} />
                  </div>
                  <h3 className="text-[#ffffff] font-heading font-medium">Primary Custody</h3>
                  <p className="text-[#d4dce1] font-medium text-s leading-relaxed">Full compatibility with Tier 1 custody solutions including Safe, Fireblocks, and Copper.</p>
                </div>
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] space-y-4 shadow-none">
                  <div className="w-12 h-12 rounded-full border border-[#37d097] bg-transparent flex items-center justify-center text-[#ffffff]">
                    <CheckCircle2 size={24} />
                  </div>
                  <h3 className="text-[#ffffff] font-heading font-medium">Reporting API</h3>
                  <p className="text-[#d4dce1] font-medium text-s leading-relaxed">Real time programmatic access to solvency metrics for internal risk accounting.</p>
                </div>
              </div>

              {/* Full-width Onboarding Form */}
              <div className="relative bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] p-8 md:p-24 rounded-sm border border-[#444a4f] shadow-none overflow-hidden">
                {submitted ? (
                  <motion.div 
                    initial={{ opacity: 0, scale: 0.9 }}
                    animate={{ opacity: 1, scale: 1 }}
                    className="text-center space-y-6 py-12"
                  >
                    <div className="w-24 h-24 bg-transparent rounded-full flex items-center justify-center text-[#37d097] mx-auto border border-[#37d097]">
                      <CheckCircle2 size={48} />
                    </div>
                    <div className="space-y-2">
                      <h2 className="font-heading font-medium text-[#ffffff]">Request received</h2>
                      <p className="text-[#d4dce1] font-medium">Our institutional desk will contact you via your work email within 24 hours.</p>
                    </div>
                    <button 
                      onClick={() => setSubmitted(false)}
                      className="text-[#ffffff] text-s font-bold hover:text-[#37d097] transition-colors px-6 py-3 rounded-full bg-transparent border border-[#ffffff]"
                    >
                      Submit another request
                    </button>
                  </motion.div>
                ) : (
                  <form onSubmit={handleSubmit} className="space-y-20">
                      <div className="space-y-4">
                        <TypedHeading className="font-heading font-medium text-[#ffffff] tracking-tight text-center">
                          Institutional Onboarding
                        </TypedHeading>
                        <p className="text-[#d4dce1] font-medium text-center text-l">Initiate the whitelisting process by completing the brief below.</p>
                      </div>

                    <div className="space-y-10 max-w-4xl mx-auto">
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                        <div className="space-y-3">
                          <label className="text-s font-medium text-[#aab9be] tracking-tight block mb-2">Name</label>
                          <input 
                            required
                            name="name"
                            type="text" 
                            className="w-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be]"
                            placeholder="Institutional Lead"
                          />
                        </div>
                        <div className="space-y-3">
                          <label className="text-s font-medium text-[#aab9be] tracking-tight block mb-2">Work Email</label>
                          <input 
                            required
                            name="email"
                            type="email" 
                            className="w-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be]"
                            placeholder="lead@firm.com"
                          />
                        </div>
                      </div>

                      <div className="space-y-3">
                        <label className="text-s font-medium text-[#aab9be] tracking-tight block mb-2">Organization</label>
                        <input 
                          required
                          name="organization"
                          type="text" 
                          className="w-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be]"
                          placeholder="Hedge Fund / Family Office / Treasury"
                        />
                      </div>

                      <div className="space-y-3">
                        <label className="text-s font-medium text-[#aab9be] tracking-tight block mb-2">Anticipated Allocation (ETH)</label>
                        <div className="flex flex-wrap items-center justify-between w-full pt-2">
                          {[
                            { id: '100-500', label: '100 - 500 ETH' },
                            { id: '500-2500', label: '500 - 2,500 ETH' },
                            { id: '2500-10000', label: '2,500 - 10,000 ETH' },
                            { id: '10000+', label: '10,000+ ETH' },
                          ].map((option) => (
                            <div 
                              key={option.id} 
                              className="flex items-center gap-3 cursor-pointer group"
                              onClick={() => setVolume(option.id)}
                            >
                              <div className={`w-5 h-5 rounded-full border-2 flex items-center justify-center transition-all ${
                                volume === option.id 
                                  ? 'border-[#37d097]' 
                                  : 'border-[#aab9be] group-hover:border-[#37d097]'
                              }`}>
                                {volume === option.id && (
                                  <div className="w-2.5 h-2.5 rounded-full bg-[#37d097]" />
                                )}
                              </div>
                              <span className={`text-s font-medium transition-colors ${
                                volume === option.id ? 'text-[#ffffff]' : 'text-[#aab9be]'
                              }`}>
                                {option.label}
                              </span>
                            </div>
                          ))}
                        </div>
                      </div>

                      <button 
                        disabled={loading}
                        type="submit"
                        className="w-full h-12 bg-gradient-to-r from-[#19b097] to-[#37d097] text-[#ffffff] font-bold rounded-sm transition-all flex items-center justify-center disabled:opacity-50 shadow-none text-s animate-gradient cursor-pointer disabled:cursor-not-allowed"
                      >
                        {loading ? 'Processing...' : 'Initiate Whitelisting'}
                      </button>

                      <p className="text-xs text-[#aab9be] text-center font-medium leading-relaxed">
                        By submitting, institutional partners acknowledge the risk policies and <br />
                        on-chain transparency requirements of the Kerne Protocol.
                      </p>
                    </div>
                  </form>
                )}
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}
