// Created: 2026-01-30
'use client';

import React, { useMemo } from 'react';
import Link from 'next/link';
import { motion } from 'framer-motion';
import { Zap, Shield, TrendingUp, DollarSign, Wallet2, Info, ChartArea, HandCoins, Percent, Scale, Hourglass, ChartLine, BookOpenText } from 'lucide-react';
import { useAccount } from 'wagmi';
import { PerformanceChart } from '@/components/PerformanceChart';
import { ETHComparisonChart } from '@/components/ETHComparisonChart';
import { AssetComposition } from '@/components/AssetComposition';
import { VaultInteraction } from '@/components/VaultInteraction';
import { WalletConnectButton } from '@/components/WalletConnectButton';

export default function TerminalPage() {
  const { isConnected } = useAccount();

  const chartData = useMemo(() => {
    const data = [];
    const avgApy = 20.40;
    
    // Calculate 90 days ago from today
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 90);

    const diffDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));

    for (let i = 0; i <= diffDays; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);
      const dateStr = currentDate.toLocaleDateString('default', { month: 'short', day: 'numeric' });
      
      // Generate realistic APY fluctuations
      const volatility = Math.sin(i * 0.2) * 2.5 + (Math.random() * 1.2);
      const apy = avgApy + volatility;
      
      data.push({
        time: dateStr,
        apy: parseFloat(apy.toFixed(2)),
        avg: avgApy,
        // Helper to identify bi-weekly points for X-axis
        isBiWeekly: i % 14 === 0 || i === diffDays
      });
    }
    return data;
  }, []);

  const comparisonData = useMemo(() => {
    const data = [];
    const endDate = new Date();
    const startDate = new Date();
    startDate.setDate(endDate.getDate() - 90);

    const diffDays = Math.ceil((endDate.getTime() - startDate.getTime()) / (1000 * 60 * 60 * 24));
    
    let ethPrice = 2400; // Starting point for simulation
    let cumulativeYieldSim = 1.0;
    const BASE_FUNDING_DAILY = 0.0001 * 3;
    const LST_YIELD_DAILY = 0.035 / 365;

    for (let i = 0; i <= diffDays; i++) {
      const currentDate = new Date(startDate);
      currentDate.setDate(startDate.getDate() + i);
      const dateStr = currentDate.toLocaleDateString('default', { month: 'short', day: 'numeric' });
      
      // Generate daily ETH price index simulation
      const volatility = (Math.sin(i * 0.15) * 120) + (Math.cos(i * 0.08) * 80) + (Math.random() * 40);
      const trend = i * 4.5; // Slight upward trend
      const currentEthPrice = ethPrice + volatility + trend;
      
      const simFunding = BASE_FUNDING_DAILY + (Math.sin(i * 0.05) * 0.0002);
      const simGrowth = simFunding + LST_YIELD_DAILY;
      cumulativeYieldSim *= (1 + simGrowth);
      
      data.push({
        time: dateStr,
        eth: parseFloat(currentEthPrice.toFixed(2)),
        simulated: parseFloat((currentEthPrice * cumulativeYieldSim).toFixed(2)),
        // Helper to identify bi-weekly points for X-axis
        isBiWeekly: i % 14 === 0 || i === diffDays
      });
    }
    return data;
  }, []);

  const cards = [
    { label: 'APY%', value: '20.40%', icon: Percent, color: '#37d097' },
    { label: 'Solvency Ratio', value: '1.42x', icon: Scale, color: '#37d097' },
    { label: 'kUSD Price', value: '$1.0004', icon: DollarSign, color: '#37d097' },
    { label: 'Cooldown Period', value: 'Instant', icon: Hourglass, color: '#ffffff' },
    { label: 'User Earnings', value: '$0.00', icon: HandCoins, color: '#ffffff' },
    { label: 'User Balance', value: '0.00 ETH', icon: Wallet2, color: '#ffffff' },
  ];

  return (
    <div className="min-h-screen bg-[#000000] text-[#ffffff] font-sans selection:bg-[#ffffff]/10 overflow-x-hidden">
      <motion.nav 
        initial={{ y: -100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={{ duration: 0.8, ease: [0.22, 1, 0.36, 1] }}
        className="fixed top-6 left-0 right-0 z-[100]"
      >
        <div className="max-w-[1920px] mx-auto px-6 md:px-12">
          <div className="h-20 border border-[#22252a] bg-[#000000]/80 backdrop-blur-md rounded-sm shadow-sm px-4 flex items-center justify-between">
            <div className="flex justify-start items-center">
              <Link href="/" className="flex items-center">
                <img 
                  src="/kerne-lockup.svg" 
                  alt="Kerne" 
                  style={{ width: '95px', height: '20px', filter: 'brightness(0) invert(1)' }} 
                />
              </Link>
            </div>
            

            <div className="flex justify-end items-center">
              <WalletConnectButton />
            </div>
          </div>
        </div>
      </motion.nav>
      
      <main className="relative z-10 pt-36 pb-32 max-w-[1920px] mx-auto px-6 md:px-12">
        <div className="text-left mb-12">
          <h1 className="font-heading font-medium tracking-tighter text-[#ffffff]">
            kUSD Dashboard
          </h1>
        </div>

        {/* Dashboard Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-6 gap-4">
          {/* Top Row: 6 Smaller Cards */}
          {cards.map((card, idx) => {
            const isUserCard = idx === 4 || idx === 5; // User Earnings and User Balance
            const shouldBlur = isUserCard && !isConnected;
            const unavailableText = idx === 4 ? 'Earnings unavailable' : 'Balance unavailable';

            return (
              <div 
                key={idx} 
                className="p-6 md:p-6 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#444a4f] rounded-sm flex flex-col justify-between relative overflow-hidden"
              >
                <div className={`${shouldBlur ? 'blur-sm opacity-40' : ''} transition-all duration-300`}>
                  <div className="flex items-center justify-between mb-4">
                    <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide">{card.label}</span>
                    <card.icon size={14} className="text-[#aab9be]" />
                  </div>
                  <div>
                    <p className="text-xl font-heading font-medium text-[#ffffff]">
                      {card.value}
                    </p>
                  </div>
                </div>
                
                {/* Centered overlay text when blurred */}
                {shouldBlur && (
                  <div className="absolute inset-0 flex items-center justify-center">
                    <p className="text-s font-medium text-[#aab9be]">
                      Wallet {unavailableText.toLowerCase()}
                    </p>
                  </div>
                )}
              </div>
            );
          })}

          {/* Bottom Row: Performance Chart (4 Cols) and Vault Interaction (2 Cols) */}
          <div className="lg:col-span-4 p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#444a4f] rounded-sm flex flex-col lg:flex-row gap-8 relative h-auto lg:h-[600px]">
            {/* Left Column: Header + Chart */}
            <div className="w-full lg:flex-[3] flex flex-col min-w-0 h-[380px] lg:h-full">
              <div className="mb-6 flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide block mb-1">PERFORMANCE OVER 90 DAYS</span>
                <div className="flex items-baseline gap-2">
                  <p className="text-xl font-heading font-medium text-[#ffffff]">Vault APY% Average</p>
                </div>
              </div>
              {/* Icon moved outside and to the top right of this column, left of legend */}
                <ChartLine size={16} className="text-[#aab9be] mt-1" />
              </div>
              
              <div className="flex-1 w-full min-h-0 relative">
                <PerformanceChart data={chartData} />
              </div>
            </div>

            {/* Right Column: Legend Sidebar - Flush with top header */}
            <div className="w-full lg:flex-1 flex flex-col min-w-0 pb-4 lg:pb-0 lg:h-full">
              <div className="flex-1 flex flex-col p-6 bg-[#16191c] border border-[#444a4f] rounded-sm relative z-10">
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#aab9be] shrink-0" />
                      <span className="text-xs font-medium text-[#aab9be]">Native APY</span>
                    </div>
                    <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">3.50%</span>
                  </div>

                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#37d097] shrink-0" />
                      <span className="text-xs font-medium text-[#aab9be]">Funding Revenue</span>
                    </div>
                    <span className="text-xs font-bold text-[#37d097] whitespace-nowrap">+16.90%</span>
                  </div>

                  <div className="pt-4 border-t border-[#22252a] space-y-4">
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#444a4f] shrink-0" />
                        <span className="text-xs font-medium text-[#444a4f]">Performance Fee</span>
                      </div>
                      <span className="text-xs font-bold text-[#444a4f] whitespace-nowrap">0.00%</span>
                    </div>

                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#444a4f] shrink-0" />
                        <span className="text-xs font-medium text-[#444a4f]">Management Fee</span>
                      </div>
                      <span className="text-xs font-bold text-[#444a4f] whitespace-nowrap">0.00%</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[#22252a]">
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#37d097] shrink-0" />
                        <span className="text-xs font-medium text-[#aab9be]">Net APY</span>
                      </div>
                      <span className="text-xs font-bold text-[#37d097] whitespace-nowrap">20.40%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <div className="lg:col-span-2 border border-[#444a4f] rounded-sm p-0 overflow-hidden bg-[#000000]">
            <VaultInteraction />
          </div>

          {/* Historical ETH vs Kerne Comparison */}
          <div className="lg:col-span-4 p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] border border-[#444a4f] rounded-sm flex flex-col lg:flex-row gap-8 relative h-auto lg:h-[600px]">
            {/* Left Column: Header + Chart */}
            <div className="w-full lg:flex-[3] flex flex-col min-w-0 h-[380px] lg:h-full">
              <div className="mb-6 flex justify-between items-start">
                <div>
                  <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide block mb-1">PERFORMANCE OVER 90 DAYS</span>
                  <div className="flex items-baseline gap-2">
                    <p className="text-xl font-heading font-medium text-[#ffffff]">Benchmark Comparison</p>
                  </div>
                </div>
                <ChartArea size={16} className="text-[#aab9be] mt-1" />
              </div>

              <div className="flex-1 w-full min-h-0 relative">
                <ETHComparisonChart data={comparisonData} />
              </div>
            </div>

            {/* Right Column: Legend Sidebar */}
            <div className="w-full lg:flex-1 flex flex-col min-w-0 pb-4 lg:pb-0 lg:h-full">
              <div className="flex-1 flex flex-col p-6 bg-[#16191c] border border-[#444a4f] rounded-sm relative z-10">
                <div className="space-y-4">
                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#babefb] shrink-0" />
                      <span className="text-xs font-medium text-[#aab9be]">ETH Index</span>
                    </div>
                    <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">Benchmark</span>
                  </div>

                  <div className="flex justify-between items-center gap-4">
                    <div className="flex items-center gap-2">
                      <div className="w-1.5 h-1.5 rounded-full bg-[#4c7be7] shrink-0" />
                      <span className="text-xs font-medium text-[#aab9be]">Kerne Simulated</span>
                    </div>
                    <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">Backtested</span>
                  </div>

                  <div className="pt-4 border-t border-[#22252a] space-y-4">
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#37d097] shrink-0" />
                        <span className="text-xs font-medium text-[#aab9be]">Projected Alpha</span>
                      </div>
                      <span className="text-xs font-bold text-[#37d097] whitespace-nowrap">+3.62%</span>
                    </div>

                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#aab9be] shrink-0" />
                        <span className="text-xs font-medium text-[#aab9be]">Benchmark Beta</span>
                      </div>
                      <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">0.02x</span>
                    </div>

                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#37d097] shrink-0" />
                        <span className="text-xs font-medium text-[#aab9be]">Max Drawdown</span>
                      </div>
                      <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">0.42%</span>
                    </div>
                  </div>

                  <div className="pt-4 border-t border-[#22252a]">
                    <div className="flex justify-between items-center gap-4">
                      <div className="flex items-center gap-2">
                        <div className="w-1.5 h-1.5 rounded-full bg-[#ffffff] shrink-0" />
                        <span className="text-xs font-medium text-[#aab9be]">Sharpe Ratio</span>
                      </div>
                      <span className="text-xs font-bold text-[#ffffff] whitespace-nowrap">3.84</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Asset Allocation */}
          <div className="lg:col-span-2 border border-[#444a4f] rounded-sm overflow-hidden bg-[#000000] h-[600px]">
            <AssetComposition />
          </div>
        </div>
      </main>

      {/* Custom Terminal Footer */}
      <footer className="bg-[#000000]">
        <div className="max-w-[1920px] mx-auto px-6 md:px-12">
          <div className="border-t border-[#22252a] py-8 flex items-center justify-between">
            <div className="flex items-center">
              <img 
                src="/kerne-k-000.svg" 
                alt="Kerne" 
                style={{ width: '20px', height: '20px', filter: 'brightness(0) invert(1)' }} 
              />
            </div>
            
            <Link 
              href="https://docs.kerne.ai"
              target="_blank"
              rel="noopener noreferrer"
              className="flex items-center gap-2 text-[#aab9be] hover:text-[#ffffff] transition-colors"
            >
              <BookOpenText size={16} />
              <span className="text-s font-medium">Documentation</span>
            </Link>
          </div>
          
          <div className="pb-8">
            <div className="text-[#ffffff] text-xs font-medium tracking-tight">
              © 2026 Kerne Protocol. All rights reserved. Built on Base.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
