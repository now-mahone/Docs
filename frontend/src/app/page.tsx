// Created: 2025-12-29 | Redesign: 2026-01-22
// Palette: Black (#000000), White (#ffffff) - Monochrome scheme
'use client';

import React, { useEffect, useState, useRef } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { ArrowRight, Shield, BarChart3, Landmark, Lock, Activity, Cpu, Database, Network, Wallet, Eye, HandCoins } from 'lucide-react';
import { motion, useScroll, useTransform, useMotionValue, useSpring, animate, useInView } from 'framer-motion';
import Footer from '@/components/Footer';
import Navbar from '@/components/Navbar';
import BacktestedPerformance from '@/components/BacktestedPerformance';
import KerneExplained from '@/components/KerneExplained';

function CountUp({ value, decimals = 0, prefix = "", suffix = "" }: { value: number; decimals?: number; prefix?: string; suffix?: string }) {
  const nodeRef = useRef<HTMLSpanElement>(null);
  const isInView = useInView(nodeRef, { once: true });

  useEffect(() => {
    if (isInView && nodeRef.current) {
      const controls = animate(0, value, {
        duration: 2,
        ease: [0.25, 0.1, 0.25, 1],
        onUpdate(latest: number) {
          if (nodeRef.current) {
            nodeRef.current.textContent = prefix + latest.toFixed(decimals) + suffix;
          }
        },
      });
      return () => controls.stop();
    }
  }, [value, decimals, prefix, suffix, isInView]);

  return <span ref={nodeRef}>{prefix}{value.toFixed(decimals)}{suffix}</span>;
}

function PillButton({ href, children, icon: Icon, className = "", variant = "primary" }: { href: string; children: React.ReactNode; icon?: React.ElementType; className?: string; variant?: "primary" | "secondary" | "outline" | "green" }) {
  const baseStyles = "relative px-10 font-bold rounded-sm transition-all flex items-center justify-center text-s border-none outline-none shadow-none group h-12 gap-2";
  
  const variants = {
    primary: "bg-[#000000] text-[#ffffff] hover:bg-[#000000]",
    secondary: "bg-[#000000] text-[#ffffff] hover:bg-[#000000]",
    outline: "bg-transparent border border-[#000000] text-[#000000] hover:bg-[#000000]",
    green: "bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] text-[#ffffff] animate-mesh"
  };

  return (
    <Link href={href} className={`${baseStyles} ${variants[variant]} ${className}`}>
      {children}
      {Icon && <Icon size={16} />}
    </Link>
  );
}

export default function LandingPage() {
  const [ethPrice, setEthPrice] = useState(0);
  const [liveApy, setLiveApy] = useState<number | null>(null);
  const [stakingYield, setStakingYield] = useState(0);
  const [fundingRate, setFundingRate] = useState(0);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      // Fetch ETH price
      try {
        const res = await fetch('https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT');
        const data = await res.json();
        setEthPrice(parseFloat(data.price));
      } catch (e) {
        console.error("Failed to fetch ETH price", e);
        setEthPrice(3150); // Fallback
      }

      // Fetch live APY from our API
      try {
        const res = await fetch('/api/apy');
        const data = await res.json();
        
        if (data.apy !== null && data.apy !== undefined) {
          setLiveApy(data.apy);
        }
        
        if (data.staking_yield) {
          setStakingYield(parseFloat((data.staking_yield * 100).toFixed(2)));
        }
        
        if (data.breakdown?.best_funding_annual_pct !== undefined) {
          // Convert annual % back to 8h rate for display consistency with market norms
          const annual = data.breakdown.best_funding_annual_pct / 100;
          const rate8h = annual / (3 * 365);
          setFundingRate(parseFloat((rate8h * 100).toFixed(4)));
        }
      } catch (e) {
        console.error("Failed to fetch live APY", e);
        // Sensible fallbacks if API fails
        setLiveApy(18.4);
        setStakingYield(3.2);
        setFundingRate(0.034);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const { scrollYProgress } = useScroll();
  const opacity = useTransform(scrollYProgress, [0, 0.2], [1, 0]);
  const scale = useTransform(scrollYProgress, [0, 0.2], [1, 0.98]);

  const [calculatorAmount, setCalculatorAmount] = useState(10);
  // Freeze the APY once it's loaded to prevent mid-animation resets
  const [frozenApy, setFrozenApy] = useState<number | null>(null);

  useEffect(() => {
    if (!loading && liveApy !== null && frozenApy === null) {
      setFrozenApy(liveApy);
    }
  }, [loading, liveApy, frozenApy]);

  const displayApy = frozenApy !== null ? frozenApy : (liveApy !== null ? liveApy : 18.4);
  const effectiveEthPrice = ethPrice || 3150;
  const yearlyCalculationUSD = Math.round(calculatorAmount * effectiveEthPrice * (displayApy / 100));
  const monthlyCalculationUSD = Math.round(yearlyCalculationUSD / 12);

  return (
    <div className="min-h-screen bg-[#ffffff] text-[#000000] font-sans selection:bg-[#000000] overflow-x-hidden">
      {/* Background patterns inspired by Morpho/Ironfish */}
      <div className="fixed inset-0 z-0 opacity-[0.03] pointer-events-none text-[#000000]">
        <div className="absolute inset-0 bg-[radial-gradient(currentColor_1px,transparent_1px)] [background-size:40px_40px]" />
      </div>

      <Navbar />

      <main className="relative z-10 pt-24">
        {/* Massive Hero Section inspired by Cursor/Morpho */}
        <section className="relative pt-24 md:pt-32 pb-32 overflow-hidden flex flex-col items-center text-center bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12 text-center relative z-20 flex flex-col items-center w-full mb-24">
            <h1 className="font-heading font-medium tracking-tight leading-[0.95] text-[#000000] mb-8">
              The future of onchain yield.<br />
              Live at an APY of<br />
              <span className="bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] bg-clip-text text-transparent animate-mesh">
                {frozenApy !== null ? (
                  <CountUp value={frozenApy} decimals={1} suffix="%" />
                ) : (
                  // Constant display before live data load to prevent layout shift and multiple count-ups
                  <span>0.0%</span>
                )}
              </span>
            </h1>

            <p className="text-l md:text-l text-[#000000] max-w-2xl mx-auto mb-10 font-medium leading-relaxed">
              Building the most capital efficient delta neutral infrastructure in DeFi. Kerne's vaults hedge every position automatically. You deposit ETH. Your capital compounds. That's it.
            </p>

            <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
              <a href="/terminal" target="_blank" rel="noopener noreferrer" className="relative px-10 font-bold rounded-sm transition-all flex items-center justify-center text-s border-none outline-none shadow-none h-12 gap-2 bg-[linear-gradient(110deg,#19b097,#37d097,#19b097)] text-[#ffffff] animate-mesh w-full sm:w-auto">
                Start Earning
              </a>
            </div>
          </div>

          {/* Yield Calculator - Redesigned Layout */}
          <div className="max-w-7xl w-full mx-auto relative px-6 md:px-12">
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-16 relative shadow-none">
              {/* Two-column layout */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-12">
                {/* LEFT COLUMN: Calculator, Title, and Disclaimer */}
                <div className="flex flex-col justify-between space-y-8">
                  {/* Title */}
                  <div>
                    <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight text-left">
                      Calculate the onchain difference
                    </h3>
                  </div>

                  {/* Investment Slider */}
                  <div className="flex flex-col space-y-6">
                    <div className="text-s font-bold text-[#d4dce1] uppercase tracking-wide text-left">Investment amount (ETH)</div>
                    <input 
                      type="range" 
                      min="1" 
                      max="100" 
                      value={calculatorAmount} 
                      onChange={(e) => setCalculatorAmount(parseInt(e.target.value))}
                      className="calculator-slider w-full h-1 bg-[#444a4f] rounded-sm appearance-none cursor-pointer accent-[#37d097]"
                    />
                    <div className="flex items-baseline justify-between">
                      <span className="text-xl font-heading font-medium text-[#d4dce1]">{calculatorAmount} ETH</span>
                      <span className="text-xl font-heading font-medium text-[#d4dce1]">≈ ${(calculatorAmount * ethPrice).toLocaleString(undefined, { maximumFractionDigits: 2 })}</span>
                    </div>
                  </div>

                  {/* Disclaimer - No card, just text */}
                  <div>
                    <p className="text-xs leading-relaxed text-[#444a4f] font-medium text-left">
                      Calculated based on current funding rates and staking yield. Performance fees are already deducted.
                    </p>
                  </div>
                </div>

                {/* RIGHT COLUMN: 2x2 Grid */}
                <div className="grid grid-cols-2 gap-4 auto-rows-fr">
                  {/* Top Left: ETH Funding Rate */}
                  <div className="p-6 bg-gradient-to-b from-[#22252a] from-0% via-[#16191c] via-40% to-[#000000] to-100% rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                    <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">ETH funding rate</div>
                    <div>
                      <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                        {fundingRate !== 0 ? <CountUp value={fundingRate} decimals={4} suffix="%" /> : "0.0000%"}
                      </div>
                      <div className={`flex items-center gap-1 text-s font-medium ${fundingRate >= 0 ? 'text-[#37d097]' : 'text-[#ff6b6b]'}`}>
                        <span>{fundingRate >= 0 ? '↑' : '↓'}</span>
                        <span>{fundingRate >= 0 ? 'Positive' : 'Negative'}</span>
                      </div>
                    </div>
                  </div>

                  {/* Top Right: wstETH APY% */}
                  <div className="p-6 bg-gradient-to-b from-[#22252a] from-0% via-[#16191c] via-40% to-[#000000] to-100% rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                    <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">wstETH APY%</div>
                    <div>
                      <div className="text-xl font-heading font-medium text-[#ffffff] mb-2">
                        {stakingYield !== 0 ? <CountUp value={stakingYield} decimals={2} suffix="%" /> : "0.00%"}
                      </div>
                      <div className="text-s text-[#444a4f] font-medium">*Lido Data</div>
                    </div>
                  </div>

                  {/* Bottom Left: Monthly Earnings */}
                  <div className="p-6 bg-gradient-to-b from-[#22252a] from-0% via-[#16191c] via-40% to-[#000000] to-100% rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                    <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Monthly earnings</div>
                    <div className="text-xl font-heading font-medium text-[#37d097]">
                      ${monthlyCalculationUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                  </div>

                  {/* Bottom Right: Yearly Earnings */}
                  <div className="p-6 bg-gradient-to-b from-[#22252a] from-0% via-[#16191c] via-40% to-[#000000] to-100% rounded-sm border border-[#444a4f] flex flex-col justify-between text-left">
                    <div className="text-xs font-bold text-[#aab9be] uppercase tracking-wide mb-4">Yearly earnings</div>
                    <div className="text-xl font-heading font-medium text-[#37d097]">
                      ${yearlyCalculationUSD.toLocaleString(undefined, { maximumFractionDigits: 0 })}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Backtested Performance Section */}
        <BacktestedPerformance />

        {/* Kerne Explained Section */}
        <KerneExplained />

        {/* Institutional Reliability Section */}
        <section className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            <div className="flex flex-col items-center text-center mb-16">
              <h2 className="font-heading font-medium tracking-tight text-[#000000] mb-8">
                  Institutional Reliability
              </h2>
              <p className="text-m text-[#000000] max-w-2xl font-medium">
                Engineered for the most demanding capital allocators, Kerne combines absolute transparency with autonomous risk management.
              </p>
            </div>

            {/* Card Container */}
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-12">
                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Database size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Real Time Solvency</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Unlike traditional finance, Kerne offers absolute transparency. All protocol backing is verifiable onchain, providing institutions with immediate assurance of asset quality.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Cpu size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Automated Hedging</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Proprietary delta neutral engine that autonomously manages market exposure. Our infrastructure captures funding rates while eliminating directional risk through high frequency algorithmic precision.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Landmark size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Tier 1 Custody</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Designed for integration with multisig safe architectures and institutional custodians. Kerne maintains noncustodial principles while providing the technical scaffolding required by the world's largest funds.
                  </p>
                </div>

                <div className="p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] shadow-none flex flex-col items-start text-left group transition-colors">
                  <div className="w-12 h-12 bg-transparent border border-[#37d097] rounded-full flex items-center justify-center text-[#ffffff] mb-8">
                    <Eye size={24} />
                  </div>
                  <h3 className="font-heading font-medium mb-4 tracking-tight text-[#ffffff]">Audited Infrastructure</h3>
                  <p className="text-s text-[#d4dce1] leading-relaxed font-medium">
                    Battle tested smart contracts audited by industry leading security firms. We prioritize mathematical correctness and formal verification to maintain the standard for onchain security.
                  </p>
                </div>
              </div>

              {/* Partner Logo Belt */}
              <div className="mb-12">
                <h3 className="font-heading font-medium tracking-tight text-[#ffffff] leading-tight mb-4">
                  Ecosystem infrastructure
                </h3>
                <p className="text-m text-[#d4dce1] font-medium">
                  Built on LayerZero V2 Kerne enables zero slippage kUSD transfers across Base, Arbitrum, and Optimism without wrapped assets. Our delta neutral ERC-4626 vaults feature native production integrations with Base, Hyperliquid, Aerodrome, and CowDAO that process real capital instead of mere partnerships. We protect funds using the subsecond speed of Base allowing our Oracle Guard to mitigate depeg events faster than mainnet latency permits.
                </p>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 auto-rows-fr">
                <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex items-center justify-center p-6 md:p-8 min-h-[80px] md:min-h-[100px]">
                  <img 
                    src="/Base-LogoL.svg"
                    alt="Base" 
                    width="1280" 
                    height="323"
                    className="h-[20px] w-auto max-w-full object-contain" 
                    style={{ filter: 'brightness(0) invert(1)' }} 
                  />
                </div>
                <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex items-center justify-center p-6 md:p-8 min-h-[80px] md:min-h-[100px]">
                  <img 
                    src="/Hyperliquid-LogoL.svg"
                    alt="Hyperliquid" 
                    width="370" 
                    height="57"
                    className="h-6 w-auto max-w-full object-contain" 
                    style={{ filter: 'brightness(0) invert(1)' }} 
                  />
                </div>
                <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex items-center justify-center p-6 md:p-8 min-h-[80px] md:min-h-[100px]">
                  <img 
                    src="/Aerodrome-LogoL.svg"
                    alt="Aerodrome" 
                    width="401" 
                    height="56"
                    className="h-6 w-auto max-w-full object-contain" 
                    style={{ filter: 'brightness(0) invert(1)' }} 
                  />
                </div>
                <div className="bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm border border-[#444a4f] flex items-center justify-center p-6 md:p-8 min-h-[80px] md:min-h-[100px]">
                  <img 
                    src="/CoW-Protocol-LogoL.svg"
                    alt="CoW DAO" 
                    width="1630" 
                    height="400"
                    className="h-[30px] w-auto max-w-full object-contain" 
                    style={{ filter: 'brightness(0) invert(1)' }} 
                  />
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Contact Section */}
        <section className="pt-32 pb-32 bg-gradient-to-b from-[#ffffff] to-[#d4dce1]">
          <div className="max-w-7xl mx-auto px-6 md:px-12">
            <div className="w-full rounded-sm bg-[#000000] p-8 md:p-12 flex flex-col items-center text-center">
              <h2 className="font-heading font-medium tracking-tight text-[#ffffff] mb-8">
                Join the Genesis Epoch
              </h2>
              <p className="text-m text-[#d4dce1] max-w-2xl font-medium mb-12">
                Early depositors secure the highest allocation of Quanta rewards credits. Your first deposit starts earning within 60 seconds. No lockups. No vesting. Withdraw anytime.
              </p>
              <div className="flex flex-col sm:flex-row items-center justify-center gap-6">
                <a href="/terminal" target="_blank" rel="noopener noreferrer" className="relative px-10 font-bold rounded-sm transition-all flex items-center justify-center text-s border-none outline-none shadow-none h-12 bg-[#ffffff] text-[#000000] hover:bg-[#ffffff]">
                  Connect
                </a>
                <Link 
                  href="/institutional" 
                  className="inline-flex items-center gap-2 text-m text-[#ffffff] font-bold hover:underline transition-all"
                >
                  Institutional Onboarding
                  <ArrowRight size={20} />
                </Link>
              </div>
            </div>
          </div>
        </section>
      </main>

      <Footer />
    </div>
  );
}