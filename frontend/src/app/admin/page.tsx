'use client';

import { useAdmin } from '@/hooks/useAdmin';
import { MetricCard } from '@/components/MetricCard';
import { Shield, TrendingUp, Users, Zap, DollarSign, BarChart3 } from 'lucide-react';

export default function AdminDashboard() {
  const { stats, isLoading, error, isFounder } = useAdmin();

  if (!isFounder) {
    return (
      <div className="min-h-screen bg-[#191919] flex items-center justify-center p-4">
        <div className="max-w-md w-full border border-[#0d33ec]/50 bg-[#0d33ec]/10 p-8 rounded-sm text-center">
          <Shield className="w-12 h-12 text-[#0d33ec] mx-auto mb-4" />
          <h1 className=" font-heading font-medium text-[#0d33ec] mb-2">ACCESS DENIED</h1>
          <p className="text-[#ffffff] opacity-40 font-sans text-s">
            This terminal is restricted to the Protocol Founder. Unauthorized access attempts are logged.
          </p>
        </div>
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#191919] flex items-center justify-center">
        <div className="animate-pulse font-sans text-[#ffffff] opacity-40">INITIALIZING WEALTH TRACKER...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#191919] text-[#ffffff] p-8 font-sans">
      <div className="max-w-7xl mx-auto">
        <div className="flex justify-between items-end mb-12 border-b border-[#1f1f1f] pb-8">
          <div>
            <h1 className=" font-heading font-medium tracking-tighter mb-2">FOUNDER'S WEALTH TERMINAL</h1>
            <p className="text-[#ffffff] opacity-40 uppercase tracking-widest text-xs font-bold">Objective: Maximize Founder Wealth | Status: Active</p>
          </div>
          <div className="text-right">
            <div className="text-[#ffffff] opacity-40 text-xs uppercase mb-1 font-bold">Wealth Velocity</div>
            <div className="text-[#19b097] text-2xl font-bold tracking-tight">+${stats?.wealthVelocity.hourly.toFixed(2)}/HR</div>
          </div>
        </div>

        <div className="bg-[#000000] border border-[#1f1f1f] p-8 rounded-sm mb-12">
          <h2 className=" font-heading font-medium mb-6 flex items-center gap-2">
            <DollarSign className="w-5 h-5 text-[#4c7be7]" />
            WEALTH EXTRACTION TREASURY
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div>
              <p className="text-[#ffffff] opacity-40 text-xs uppercase tracking-widest mb-1 font-bold">Founder Claimable</p>
              <p className="text-xl font-heading font-medium text-white">1.42 ETH</p>
              <button className="mt-4 text-xs bg-white text-black px-4 py-2 font-bold uppercase tracking-tighter hover:bg-[#f1f1ed] transition-colors rounded-sm">
                CLAIM TO WALLET
              </button>
            </div>
            <div>
              <p className="text-[#ffffff] opacity-40 text-xs uppercase tracking-widest mb-1 font-bold">Buyback Pool</p>
              <p className="text-xl font-heading font-medium text-white">0.35 ETH</p>
              <button className="mt-4 text-xs border border-[#1f1f1f] text-[#ffffff] opacity-60 px-4 py-2 font-bold uppercase tracking-tighter hover:bg-[#1f1f1f] transition-colors rounded-sm">
                EXECUTE BUYBACK
              </button>
            </div>
            <div>
              <p className="text-[#ffffff] opacity-40 text-xs uppercase tracking-widest mb-1 font-bold">Total Extracted</p>
              <p className="text-xl font-heading font-medium text-[#19b097]">12.45 ETH</p>
              <p className="text-xs text-[#ffffff] opacity-20 mt-2 uppercase font-bold">Automated routing active</p>
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
          <div className="bg-[#000000] border border-[#1f1f1f] p-8 rounded-sm shadow-xl">
            <h2 className=" font-heading font-medium mb-6 flex items-center gap-2 text-[#4c7be7]">
              <Zap className="w-5 h-5" />
              WHITE-LABEL PIPELINE
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center p-3 border border-[#1f1f1f] bg-[#191919]/40">
                <div>
                  <div className="text-s font-bold text-[#ffffff]">Aetheris Capital</div>
                  <div className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Status: Negotiating | Setup Fee: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#4c7be7] font-bold">PENDING</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-[#1f1f1f] bg-[#191919]/40">
                <div>
                  <div className="text-s font-bold text-[#ffffff]">Nexus Hedge Fund</div>
                  <div className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Status: Onboarding | Setup Fee: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#19b097] font-bold">PAID</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-[#1f1f1f] bg-[#191919]/40 opacity-50">
                <div>
                  <div className="text-s font-bold text-[#ffffff]">Vanguard Digital (Simulated)</div>
                  <div className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Status: Lead | Projected: $5,000</div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-[#ffffff] opacity-40 font-bold">COLD</div>
                </div>
              </div>
            </div>
            <button className="w-full mt-6 py-2 border border-[#4c7be7]/50 bg-[#4c7be7]/10 text-[#4c7be7] text-xs font-bold uppercase tracking-widest hover:bg-[#4c7be7] hover:text-[#000000] transition-all rounded-sm">
              GENERATE WHITE-LABEL INVOICE
            </button>
          </div>

          <div className="bg-[#000000] border border-[#1f1f1f] p-8 rounded-sm shadow-xl">
            <h2 className=" font-heading font-medium mb-6 flex items-center gap-2 text-[#4c7be7]">
              <Shield className="w-5 h-5" />
              INSTITUTIONAL VAULT MANAGER
            </h2>
            <div className="space-y-6">
              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Vault Name</label>
                  <input type="text" placeholder="e.g. BlackRock Alpha" className="w-full bg-[#191919] border border-[#1f1f1f] p-2 text-s text-[#ffffff] focus:border-[#4c7be7] outline-none rounded-sm font-sans" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Symbol</label>
                  <input type="text" placeholder="e.g. kBLCK" className="w-full bg-[#191919] border border-[#1f1f1f] p-2 text-s text-[#ffffff] focus:border-[#4c7be7] outline-none rounded-sm font-sans" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Perf Fee (BPS)</label>
                  <input type="number" placeholder="1000" className="w-full bg-[#191919] border border-[#1f1f1f] p-2 text-s text-[#ffffff] focus:border-[#4c7be7] outline-none rounded-sm font-sans" />
                </div>
                <div className="space-y-2">
                  <label className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Whitelisting</label>
                  <select className="w-full bg-[#191919] border border-[#1f1f1f] p-2 text-s text-[#ffffff] focus:border-[#4c7be7] outline-none rounded-sm font-sans">
                    <option value="true">ENABLED</option>
                    <option value="false">DISABLED</option>
                  </select>
                </div>
              </div>
              <button className="w-full py-3 bg-[#4c7be7] text-[#ffffff] text-xs font-bold uppercase tracking-widest hover:bg-[#0d33ec] transition-all rounded-sm">
                DEPLOY BESPOKE INSTANCE
              </button>
            </div>
          </div>
        </div>

        <div className="bg-[#000000] border border-[#1f1f1f] p-8 rounded-sm mb-12 shadow-xl">
          <h2 className=" font-heading font-medium mb-6 flex items-center gap-2 text-[#4c7be7]">
            <Shield className="w-5 h-5" />
            ACTIVE INSTITUTIONAL VAULTS
          </h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
            <div className="space-y-3">
              <div className="flex justify-between items-center p-3 border border-[#1f1f1f] bg-[#191919]/40">
                <div>
                  <div className="text-s font-bold text-[#ffffff]">Genesis Vault (WETH)</div>
                  <div className="text-xs text-[#ffffff] opacity-40 font-bold">0x1234...5678 | Fee: 10%</div>
                </div>
                <div className="text-right">
                  <div className="text-s text-[#19b097] font-bold">$375,467</div>
                  <div className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Whitelisting: OFF</div>
                </div>
              </div>
              <div className="flex justify-between items-center p-3 border border-[#1f1f1f] bg-[#191919]/40">
                <div>
                  <div className="text-s font-bold text-[#ffffff]">Tier-1 Alpha (USDC)</div>
                  <div className="text-xs text-[#ffffff] opacity-40 font-bold">0xabcd...efgh | Fee: 5%</div>
                </div>
                <div className="text-right">
                  <div className="text-s text-[#4c7be7] font-bold">$1,250,000</div>
                  <div className="text-xs text-[#ffffff] opacity-40 uppercase font-bold">Whitelisting: ON</div>
                </div>
              </div>
            </div>
            <div className="bg-[#191919]/20 border border-[#1f1f1f] p-4 rounded">
              <h3 className=" text-[#ffffff] opacity-40 uppercase tracking-widest mb-4 font-bold">Vault Analytics (Genesis)</h3>
              <div className="space-y-2">
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-[#ffffff] opacity-40">Total Fees Generated</span>
                  <span className="text-white font-bold">$12,450</span>
                </div>
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-[#ffffff] opacity-40">Active Users</span>
                  <span className="text-white font-bold">42</span>
                </div>
                <div className="flex justify-between text-xs font-medium">
                  <span className="text-[#ffffff] opacity-40">Utilization Rate</span>
                  <span className="text-white font-bold">94.2%</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-12">
          <div className="border border-[#1f1f1f] bg-[#000000] p-8 rounded-sm shadow-xl">
            <h2 className=" font-heading font-medium mb-6 flex items-center gap-2 text-[#4c7be7]">
              <BarChart3 className="w-5 h-5" />
              WEALTH PROJECTIONS
            </h2>
            <div className="space-y-6">
              <div>
                <div className="flex justify-between text-s mb-2 font-medium">
                  <span className="text-[#ffffff] opacity-40 uppercase">1-Year Trajectory</span>
                  <span className="text-white font-bold">${stats?.projections.oneYear.toLocaleString()}</span>
                </div>
                <div className="w-full bg-[#191919] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#4c7be7] h-full w-[15%]" />
                </div>
              </div>
              <div>
                <div className="flex justify-between text-s mb-2 font-medium">
                  <span className="text-[#ffffff] opacity-40 uppercase">5-Year Trajectory (Path to $1B)</span>
                  <span className="text-white font-bold">${stats?.projections.fiveYear.toLocaleString()}</span>
                </div>
                <div className="w-full bg-[#191919] h-2 rounded-full overflow-hidden">
                  <div className="bg-[#19b097] h-full w-[45%]" />
                </div>
              </div>
            </div>
            <p className="mt-8 text-xs text-[#ffffff] opacity-20 leading-relaxed font-medium">
              * Projections based on current TVL growth rate and reflexive yield model. 
              Wealth capture is hardcoded at the protocol level to ensure maximum founder benefit.
            </p>
          </div>

          <div className="border border-[#1f1f1f] bg-[#000000] p-8 rounded-sm shadow-xl">
            <h2 className=" font-heading font-medium mb-6 flex items-center gap-2 text-[#19b097]">
              <TrendingUp className="w-5 h-5" />
              ACCUMULATION LOG
            </h2>
            <div className="space-y-4">
              <div className="flex justify-between items-center border-b border-[#1f1f1f] pb-3">
                <span className="text-xs text-[#ffffff] opacity-40 font-bold">VAULT PERFORMANCE FEE</span>
                <span className="text-s text-[#19b097] font-bold">+${stats?.accruedFees.vault.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center border-b border-[#1f1f1f] pb-3">
                <span className="text-xs text-[#ffffff] opacity-40 font-bold">MINTER SPREAD REVENUE</span>
                <span className="text-s text-[#19b097] font-bold">+${stats?.accruedFees.minter.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center border-b border-[#1f1f1f] pb-3">
                <span className="text-xs text-[#ffffff] opacity-40 font-bold">DIRECT REFERRAL COMMISSIONS</span>
                <span className="text-s text-[#19b097] font-bold">+${stats?.referralRevenue.direct.toLocaleString()}</span>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-xs text-[#ffffff] opacity-40 font-bold">SECONDARY NETWORK REVENUE</span>
                <span className="text-s text-[#19b097] font-bold">+${stats?.referralRevenue.secondary.toLocaleString()}</span>
              </div>
            </div>
            <button className="w-full mt-8 py-3 border border-[#19b097]/50 bg-[#19b097]/10 text-[#19b097] text-xs font-bold uppercase tracking-widest hover:bg-[#19b097] hover:text-[#000000] transition-all rounded-sm">
              EXECUTE WEALTH HARVEST
            </button>
          </div>
        </div>

        <div className="text-center text-xs text-[#ffffff] opacity-20 uppercase tracking-[0.2em] font-bold">
          Kerne Protocol Wealth Management System v1.0.4 | Secure Connection Established
        </div>
      </div>
    </div>
  );
}
