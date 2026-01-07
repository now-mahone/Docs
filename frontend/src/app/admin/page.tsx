'use client';

import { useAdmin } from '@/hooks/useAdmin';
import { MetricCard } from '@/components/MetricCard';
import { Shield, TrendingUp, Users, Zap, DollarSign, BarChart3 } from 'lucide-react';

export default function AdminDashboard() {
  const { stats, isLoading, error, isFounder } = useAdmin();

  if (!isFounder) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center p-4">
        <div className="max-w-md w-full border border-red-900/50 bg-red-950/10 p-8 rounded-lg text-center">
          <Shield className="w-12 h-12 text-red-500 mx-auto mb-4" />
          <h1 className="text-2xl font-mono text-red-500 mb-2">ACCESS DENIED</h1>
          <p className="text-zinc-500 font-mono text-sm">
            This terminal is restricted to the Protocol Founder. Unauthorized access attempts are logged.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-black flex items-center justify-center">
        <div className="animate-pulse font-mono text-zinc-500">INITIALIZING WEALTH TRACKER...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white p-8 font-mono">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-end mb-12 border-b border-zinc-800 pb-8">
          <div>
            <h1 className="text-4xl font-bold tracking-tighter mb-2">FOUNDER'S WEALTH TERMINAL</h1>
            <p className="text-zinc-500 uppercase tracking-widest text-xs">Objective: Maximize Founder Wealth | Status: Active</p>
          </div>
          <div className="text-right">
            <div className="text-zinc-500 text-xs uppercase mb-1">Wealth Velocity</div>
            <div className="text-green-500 text-2xl font-bold">+${stats?.wealthVelocity.hourly.toFixed(2)}/HR</div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-lg mb-12">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-yellow-500" />
            WEALTH EXTRACTION TREASURY
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <p className="text-zinc-500 text-xs uppercase tracking-widest mb-1">Founder Claimable</p>
              <p className="text-3xl font-mono text-white">1.42 ETH</p>
              <button className="mt-4 text-[10px] bg-white text-black px-4 py-2 font-bold uppercase tracking-tighter hover:bg-zinc-200 transition-colors">
                CLAIM TO WALLET
              </button>
            </div>
            <div>
              <p className="text-zinc-500 text-xs uppercase tracking-widest mb-1">Buyback Pool</p>
              <p className="text-3xl font-mono text-white">0.35 ETH</p>
              <button className="mt-4 text-[10px] border border-zinc-700 text-zinc-300 px-4 py-2 font-bold uppercase tracking-tighter hover:bg-zinc-800 transition-colors">
                EXECUTE BUYBACK
              </button>
            </div>
            <div>
              <p className="text-zinc-500 text-xs uppercase tracking-widest mb-1">Total Extracted</p>
              <p className="text-3xl font-mono text-green-500">12.45 ETH</p>
              <p className="text-[10px] text-zinc-600 mt-2 uppercase">Automated routing active</p>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-12">
          <MetricCard
            label="Total Accrued Fees"
            value={`$${stats?.accruedFees.total.toLocaleString()}`}
            trend="up"
            subValue="Real-time capture"
          />
          <MetricCard
            label="Referral Revenue"
            value={`$${stats?.referralRevenue.total.toLocaleString()}`}
            trend="up"
            subValue="Network effect active"
          />
          <MetricCard
            label="Buyback Impact"
            value={`+${((stats?.buybackImpact.priceFloorIncrease || 0) * 100).toFixed(1)}%`}
            trend="up"
            subValue="KERNE price floor"
          />
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-lg">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-purple-400">
              <Zap className="w-5 h-5" />
              WHITE-LABEL PIPELINE
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 border border-zinc-800 bg-black/40">
                <div>
                  <div className="text-sm font-bold">Aetheris Capital</div>
                  <div className="text-[10px] text-zinc-500 uppercase">Status: Negotiating | Setup Fee: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-yellow-500 font-bold">PENDING</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-zinc-800 bg-black/40">
                <div>
                  <div className="text-sm font-bold">Nexus Hedge Fund</div>
                  <div className="text-[10px] text-zinc-500 uppercase">Status: Onboarding | Setup Fee: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-green-500 font-bold">PAID</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-zinc-800 bg-black/40 opacity-50">
                <div>
                  <div className="text-sm font-bold">Vanguard Digital (Simulated)</div>
                  <div className="text-[10px] text-zinc-500 uppercase">Status: Lead | Projected: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-zinc-500 font-bold">COLD</div>
                </div>
              </div>
            </div>
            <button className="w-full mt-6 py-2 border border-purple-500/50 bg-purple-500/10 text-purple-500 text-[10px] font-bold uppercase tracking-widest hover:bg-purple-500 hover:text-black transition-all">
              GENERATE WHITE-LABEL INVOICE
            </button>
          </div>

          <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-lg">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-blue-400">
              <Shield className="w-5 h-5" />
              INSTITUTIONAL VAULT MANAGER
            </h2>
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-[10px] text-zinc-500 uppercase">Vault Name</label>
                  <input type="text" placeholder="e.g. BlackRock Alpha" className="w-full bg-black border border-zinc-800 p-2 text-sm font-mono focus:border-blue-500 outline-none" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] text-zinc-500 uppercase">Symbol</label>
                  <input type="text" placeholder="e.g. kBLCK" className="w-full bg-black border border-zinc-800 p-2 text-sm font-mono focus:border-blue-500 outline-none" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] text-zinc-500 uppercase">Perf Fee (BPS)</label>
                  <input type="number" placeholder="1000" className="w-full bg-black border border-zinc-800 p-2 text-sm font-mono focus:border-blue-500 outline-none" />
                </div>
                <div className="space-y-2">
                  <label className="text-[10px] text-zinc-500 uppercase">Whitelisting</label>
                  <select className="w-full bg-black border border-zinc-800 p-2 text-sm font-mono focus:border-blue-500 outline-none">
                    <option value="true">ENABLED</option>
                    <option value="false">DISABLED</option>
                  </select>
                </div>
              </div>
              <button className="w-full py-3 bg-blue-600 text-white text-xs font-bold uppercase tracking-widest hover:bg-blue-500 transition-all">
                DEPLOY BESPOKE INSTANCE
              </button>
            </div>
          </div>
        </div>

        <div className="bg-zinc-900/50 border border-zinc-800 p-8 rounded-lg mb-12">
          <h2 className="text-xl font-bold mb-6 flex items-center gap-2 text-blue-400">
            <Shield className="w-5 h-5" />
            ACTIVE INSTITUTIONAL VAULTS
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 border border-zinc-800 bg-black/40">
                <div>
                  <div className="text-sm font-bold">Genesis Vault (WETH)</div>
                  <div className="text-[10px] text-zinc-500">0x1234...5678 | Fee: 10%</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-green-500 font-bold">$375,467</div>
                  <div className="text-[10px] text-zinc-500 uppercase">Whitelisting: OFF</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-zinc-800 bg-black/40">
                <div>
                  <div className="text-sm font-bold">Tier-1 Alpha (USDC)</div>
                  <div className="text-[10px] text-zinc-500">0xabcd...efgh | Fee: 5%</div>
                </div>
                <div className="text-right">
                  <div className="text-sm text-blue-500 font-bold">$1,250,000</div>
                  <div className="text-[10px] text-zinc-500 uppercase">Whitelisting: ON</div>
                </div>
              </div>
            </div>
            <div className="bg-black/20 border border-zinc-800/50 p-4 rounded">
              <h3 className="text-[10px] text-zinc-500 uppercase tracking-widest mb-4">Vault Analytics (Genesis)</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">Total Fees Generated</span>
                  <span className="text-white font-bold">$12,450</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">Active Users</span>
                  <span className="text-white font-bold">42</span>
                </div>
                <div className="flex justify-between text-xs">
                  <span className="text-zinc-500">Utilization Rate</span>
                  <span className="text-white font-bold">94.2%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <div className="border border-zinc-800 bg-zinc-900/20 p-8 rounded-lg">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-blue-500" />
              WEALTH PROJECTIONS
            </h2>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-zinc-500 uppercase">1-Year Trajectory</span>
                  <span className="text-white font-bold">${stats?.projections.oneYear.toLocaleString()}</span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-blue-500 h-full w-[15%]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-sm mb-2">
                  <span className="text-zinc-500 uppercase">5-Year Trajectory (Path to $1B)</span>
                  <span className="text-white font-bold">${stats?.projections.fiveYear.toLocaleString()}</span>
                </div>
                <div className="w-full bg-zinc-800 h-2 rounded-full overflow-hidden">
                  <div className="bg-green-500 h-full w-[45%]" />
                </div>
              </div>
            </div>
            <p className="mt-8 text-xs text-zinc-600 leading-relaxed">
              * Projections based on current TVL growth rate and reflexive yield model. 
              Wealth capture is hardcoded at the protocol level to ensure maximum founder benefit.
            </p>
          </div>

          <div className="border border-zinc-800 bg-zinc-900/20 p-8 rounded-lg">
            <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-green-500" />
              ACCUMULATION LOG
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-zinc-800/50 pb-3">
                <span className="text-xs text-zinc-500">VAULT PERFORMANCE FEE</span>
                <span className="text-sm text-green-400">+${stats?.accruedFees.vault.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center border-b border-zinc-800/50 pb-3">
                <span className="text-xs text-zinc-500">MINTER SPREAD REVENUE</span>
                <span className="text-sm text-green-400">+${stats?.accruedFees.minter.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center border-b border-zinc-800/50 pb-3">
                <span className="text-xs text-zinc-500">DIRECT REFERRAL COMMISSIONS</span>
                <span className="text-sm text-green-400">+${stats?.referralRevenue.direct.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-zinc-500">SECONDARY NETWORK REVENUE</span>
                <span className="text-sm text-green-400">+${stats?.referralRevenue.secondary.toLocaleString()}</span>
              </div>
            </div>
            <button className="w-full mt-8 py-3 border border-green-500/50 bg-green-500/10 text-green-500 text-xs font-bold uppercase tracking-widest hover:bg-green-500 hover:text-black transition-all">
              EXECUTE WEALTH HARVEST
            </button>
          </div>
        </div>

        <div className="text-center text-[10px] text-zinc-700 uppercase tracking-[0.2em]">
          Kerne Protocol Wealth Management System v1.0.4 | Secure Connection Established
        </div>
      </div>
    </div>
  );
}
