'use client';

import { useState } from 'react';
import { useReferrals } from '@/hooks/useReferrals';
import { MetricCard } from './MetricCard';
import { Users, Link as LinkIcon, TrendingUp, Wallet, Copy, Check, Twitter, Send } from 'lucide-react';

export function ReferralInterface() {
  const { stats, loading, error, claimCommissions } = useReferrals();
  const [copied, setCopied] = useState(false);
  const [claiming, setClaiming] = useState(false);

  const copyToClipboard = () => {
    if (stats?.link) {
      navigator.clipboard.writeText(stats.link);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const shareOnTwitter = () => {
    const text = `I'm earning institutional-grade yield on Kerne Protocol. Join the flywheel and start earning ETH commissions: ${stats?.link}`;
    window.open(`https://twitter.com/intent/tweet?text=${encodeURIComponent(text)}`, '_blank');
  };

  const shareOnTelegram = () => {
    const text = `Join Kerne Protocol and earn ETH commissions: ${stats?.link}`;
    window.open(`https://t.me/share/url?url=${encodeURIComponent(stats?.link || '')}&text=${encodeURIComponent(text)}`, '_blank');
  };

  const handleClaim = async () => {
    setClaiming(true);
    try {
      await claimCommissions();
    } finally {
      setClaiming(false);
    }
  };

  if (loading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 animate-pulse">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="h-32 bg-zinc-900/50 rounded-xl border border-zinc-800" />
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-6 bg-red-900/20 border border-red-900/50 rounded-xl text-red-400">
        Error loading referral data: {error}
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Referral Link Section */}
      <div className="p-8 bg-zinc-900/50 border border-zinc-800 rounded-2xl backdrop-blur-sm relative overflow-hidden group">
        <div className="absolute top-0 right-0 p-4 opacity-10 group-hover:opacity-20 transition-opacity">
          <LinkIcon size={120} />
        </div>
        
        <div className="relative z-10 space-y-4">
          <div>
            <h2 className="text-2xl font-bold text-white mb-2">Your Referral Flywheel</h2>
            <p className="text-zinc-400 max-w-2xl">
              Earn 10% of the performance fees from your direct referrals and 5% from their referrals. 
              Commissions are paid in real-time as yield is harvested.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row gap-4 items-center">
            <div className="w-full bg-black border border-zinc-800 rounded-xl px-4 py-3 font-mono text-sm text-zinc-300 flex items-center justify-between">
              <span className="truncate mr-4">{stats?.link || 'Connect wallet to generate link'}</span>
              <button 
                onClick={copyToClipboard}
                className="p-2 hover:bg-zinc-800 rounded-lg transition-colors text-zinc-400 hover:text-white"
              >
                {copied ? <Check size={18} className="text-green-500" /> : <Copy size={18} />}
              </button>
            </div>
            <button 
              onClick={copyToClipboard}
              className="w-full sm:w-auto px-8 py-3 bg-white text-black font-bold rounded-xl hover:bg-zinc-200 transition-all active:scale-95 whitespace-nowrap"
            >
              Copy Link
            </button>
            <div className="flex gap-2">
              <button 
                onClick={shareOnTwitter}
                className="p-3 bg-[#1DA1F2]/10 text-[#1DA1F2] border border-[#1DA1F2]/20 rounded-xl hover:bg-[#1DA1F2]/20 transition-all"
                title="Share on Twitter"
              >
                <Twitter size={20} />
              </button>
              <button 
                onClick={shareOnTelegram}
                className="p-3 bg-[#0088cc]/10 text-[#0088cc] border border-[#0088cc]/20 rounded-xl hover:bg-[#0088cc]/20 transition-all"
                title="Share on Telegram"
              >
                <Send size={20} />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <MetricCard
          label="Total Referrals"
          value={stats?.referrals.toString() || '0'}
          subValue="Direct & Indirect"
        />
        <MetricCard
          label="Referral Volume"
          value={stats?.totalVolume || '0.00 ETH'}
          subValue="Total TVL Referred"
        />
        <div className="relative group">
          <MetricCard
            label="Pending Commissions"
            value={stats?.pendingCommissions || '0.0000 ETH'}
            subValue="Accrued this period"
          />
          {stats && parseFloat(stats.pendingCommissions) > 0 && (
            <button 
              onClick={handleClaim}
              disabled={claiming}
              className="absolute top-2 right-2 px-3 py-1 bg-green-500 text-black text-[10px] font-bold rounded-md hover:bg-green-400 transition-all disabled:opacity-50"
            >
              {claiming ? 'CLAIMING...' : 'CLAIM'}
            </button>
          )}
        </div>
        <MetricCard
          label="Wealth Velocity"
          value={stats?.wealthVelocity || '0.00%'}
          subValue="Growth rate of network"
        />
      </div>

      {/* Tier Info */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 p-6 bg-zinc-900/30 border border-zinc-800/50 rounded-xl">
          <h3 className="text-lg font-bold text-white mb-4">Commission Structure</h3>
          <div className="space-y-4">
            <div className="flex items-center justify-between p-4 bg-black/40 rounded-lg border border-zinc-800/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-blue-500/10 flex items-center justify-center text-blue-400 font-bold">1</div>
                <div>
                  <div className="text-white font-medium">Tier 1 (Direct)</div>
                  <div className="text-xs text-zinc-500">Users who use your link</div>
                </div>
              </div>
              <div className="text-xl font-bold text-blue-400">10%</div>
            </div>
            <div className="flex items-center justify-between p-4 bg-black/40 rounded-lg border border-zinc-800/30">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-purple-500/10 flex items-center justify-center text-purple-400 font-bold">2</div>
                <div>
                  <div className="text-white font-medium">Tier 2 (Indirect)</div>
                  <div className="text-xs text-zinc-500">Users referred by your Tier 1</div>
                </div>
              </div>
              <div className="text-xl font-bold text-purple-400">5%</div>
            </div>
          </div>
        </div>

        <div className="p-6 bg-zinc-900/30 border border-zinc-800/50 rounded-xl flex flex-col justify-center items-center text-center h-fit sticky top-24">
          <div className="w-16 h-16 rounded-full bg-zinc-800 flex items-center justify-center mb-4">
            <TrendingUp size={32} className="text-zinc-500" />
          </div>
          <h3 className="text-lg font-bold text-white mb-2">Current Tier</h3>
          <div className="text-2xl font-black text-white tracking-tighter mb-1">
            {stats?.tier || 'GENESIS'}
          </div>
          <p className="text-xs text-zinc-500 uppercase tracking-widest">Protocol Partner</p>
        </div>
      </div>
    </div>
  );
}
