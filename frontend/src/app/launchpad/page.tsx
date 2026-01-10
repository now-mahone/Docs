'use client';

import React, { useState } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  ArrowRight, 
  ChevronRight, 
  Settings, 
  Palette, 
  Rocket, 
  CheckCircle2, 
  Shield, 
  Zap, 
  Globe,
  Download,
  ExternalLink,
  Info,
  Loader2
} from 'lucide-react';
import { toast } from 'sonner';
import { useFactory } from '@/sdk/hooks/useFactory';
import { FACTORY_ADDRESS, WETH_ADDRESS } from '@/config';
import { useWaitForTransactionReceipt } from 'wagmi';
import { formatEther } from 'viem';

// Steps:
// 1. Configuration (Name, Symbol, Fees)
// 2. Branding (Colors, Logo)
// 3. Deployment (On-chain transaction)
// 4. Success (Download config, next steps)

const STEPS = [
  { id: 'config', title: 'Configure', icon: Settings },
  { id: 'branding', title: 'Brand', icon: Palette },
  { id: 'deploy', title: 'Deploy', icon: Rocket },
  { id: 'success', title: 'Launch', icon: CheckCircle2 },
];

export default function LaunchpadPage() {
  const [currentStep, setCurrentStep] = useState(0);
  const [isDeploying, setIsDeploying] = useState(false);
  const [deployedAddress, setDeployedAddress] = useState<string | null>(null);
  const [txHash, setTxHash] = useState<`0x${string}` | null>(null);

  const [config, setConfig] = useState({
    name: '',
    symbol: '',
    performanceFee: 10,
    whitelistEnabled: false,
    primaryColor: '#4c7be7',
    logoUrl: '',
  });

  const { deployVault, deploymentFee } = useFactory(FACTORY_ADDRESS);
  
  const { data: receipt, isLoading: isWaitingForTx } = useWaitForTransactionReceipt({
    hash: txHash || undefined,
  });

  // Effect to handle successful deployment from receipt
  React.useEffect(() => {
    if (receipt && receipt.status === 'success' && currentStep === 2) {
      // In a real scenario, we'd parse the logs for the VaultDeployed event
      // For now, we'll simulate finding the address or just move to success
      toast.success('Vault deployed successfully!');
      setCurrentStep(3);
      setIsDeploying(false);
    }
  }, [receipt, currentStep]);

  const handleDeploy = async () => {
    if (!config.name || !config.symbol) {
      toast.error('Please provide a name and symbol for your vault.');
      return;
    }

    try {
      setIsDeploying(true);
      const hash = await deployVault({
        asset: WETH_ADDRESS,
        name: config.name,
        symbol: config.symbol,
        performanceFeeBps: config.performanceFee * 100,
        whitelistEnabled: config.whitelistEnabled,
        maxTotalAssets: '0', // Unlimited
      });

      if (hash) {
        setTxHash(hash);
        toast.info('Deployment transaction submitted...');
      }
    } catch (error: any) {
      console.error('Deployment failed:', error);
      toast.error(error.message || 'Deployment failed. Please try again.');
      setIsDeploying(false);
    }
  };

  const downloadConfig = () => {
    const configData = {
      vaultAddress: deployedAddress || '0x...',
      name: config.name,
      symbol: config.symbol,
      branding: {
        primaryColor: config.primaryColor,
        logoUrl: config.logoUrl,
      },
      network: 'base',
      version: '1.0.0',
    };

    const blob = new Blob([JSON.stringify(configData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `kerne-config-${config.symbol.toLowerCase()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    toast.success('Configuration downloaded!');
  };

  const nextStep = () => {
    if (currentStep === 2) {
      handleDeploy();
    } else {
      setCurrentStep(prev => Math.min(prev + 1, STEPS.length - 1));
    }
  };
  
  const prevStep = () => setCurrentStep(prev => Math.max(prev - 1, 0));

  return (
    <div className="min-h-screen bg-white text-zinc-900 font-sans selection:bg-primary/20">
      {/* Navigation */}
      <nav className="fixed top-0 left-0 right-0 h-20 border-b border-zinc-100 bg-white/80 backdrop-blur-xl z-[100]">
        <div className="max-w-7xl mx-auto h-full px-6 flex items-center justify-between">
          <Link href="/" className="flex items-center">
            <Image src="/kerne-lockup.svg" alt="Kerne" width={110} height={24} priority />
          </Link>
          <div className="flex items-center gap-4">
            <Link href="/terminal" className="text-[11px] font-bold uppercase tracking-wider text-zinc-500 hover:text-primary transition-colors">
              Back to Terminal
            </Link>
          </div>
        </div>
      </nav>

      <main className="pt-32 pb-24 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="mb-16 text-center">
            <h1 className="text-4xl md:text-5xl font-heading font-bold tracking-tight mb-4 uppercase">
              White-Label <span className="text-primary italic">Launchpad</span>
            </h1>
            <p className="text-zinc-500 font-medium max-w-xl mx-auto">
              Deploy your own institutional-grade delta-neutral fund in minutes. 
              No-code, non-custodial, and fully branded.
            </p>
          </div>

          {/* Progress Bar */}
          <div className="mb-12 relative">
            <div className="absolute top-1/2 left-0 right-0 h-px bg-zinc-100 -translate-y-1/2 z-0" />
            <div className="relative z-10 flex justify-between">
              {STEPS.map((step, idx) => {
                const Icon = step.icon;
                const isActive = idx === currentStep;
                const isCompleted = idx < currentStep;
                
                return (
                  <div key={step.id} className="flex flex-col items-center gap-3">
                    <div className={`
                      w-10 h-10 rounded-full flex items-center justify-center transition-all duration-500
                      ${isActive ? 'bg-primary text-white shadow-lg shadow-primary/20 scale-110' : 
                        isCompleted ? 'bg-zinc-900 text-white' : 'bg-white border border-zinc-200 text-zinc-400'}
                    `}>
                      {isCompleted ? <CheckCircle2 size={20} /> : <Icon size={20} />}
                    </div>
                    <span className={`text-[10px] font-bold uppercase tracking-widest ${isActive ? 'text-primary' : 'text-zinc-400'}`}>
                      {step.title}
                    </span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Step Content */}
          <div className="bg-zinc-50 border border-zinc-100 rounded-3xl p-8 md:p-12 min-h-[400px] relative overflow-hidden">
            <AnimatePresence mode="wait">
              {currentStep === 0 && (
                <motion.div
                  key="step-0"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                    <div className="space-y-2">
                      <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Vault Name</label>
                      <input 
                        type="text" 
                        placeholder="e.g. Alpha Institutional Fund"
                        className="w-full px-4 py-3 rounded-xl border border-zinc-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                        value={config.name}
                        onChange={(e) => setConfig({...config, name: e.target.value})}
                      />
                    </div>
                    <div className="space-y-2">
                      <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Vault Symbol</label>
                      <input 
                        type="text" 
                        placeholder="e.g. ALPHA"
                        className="w-full px-4 py-3 rounded-xl border border-zinc-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all uppercase"
                        value={config.symbol}
                        onChange={(e) => setConfig({...config, symbol: e.target.value})}
                      />
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between items-center">
                      <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Performance Fee (%)</label>
                      <span className="text-primary font-bold">{config.performanceFee}%</span>
                    </div>
                    <input 
                      type="range" 
                      min="0" 
                      max="30" 
                      step="1"
                      className="w-full h-2 bg-zinc-200 rounded-lg appearance-none cursor-pointer accent-primary"
                      value={config.performanceFee}
                      onChange={(e) => setConfig({...config, performanceFee: parseInt(e.target.value)})}
                    />
                    <p className="text-[10px] text-zinc-400 font-medium">
                      Kerne Protocol takes a 10% share of your performance fees.
                    </p>
                  </div>

                  <div className="p-6 bg-white border border-zinc-200 rounded-2xl flex items-center justify-between">
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-zinc-50 rounded-full flex items-center justify-center text-zinc-400">
                        <Shield size={20} />
                      </div>
                      <div>
                        <div className="text-xs font-bold uppercase tracking-tight">Whitelist Enforcement</div>
                        <div className="text-[10px] text-zinc-400 font-medium">Only approved addresses can deposit</div>
                      </div>
                    </div>
                    <button 
                      onClick={() => setConfig({...config, whitelistEnabled: !config.whitelistEnabled})}
                      className={`w-12 h-6 rounded-full transition-all relative ${config.whitelistEnabled ? 'bg-primary' : 'bg-zinc-200'}`}
                    >
                      <div className={`absolute top-1 w-4 h-4 bg-white rounded-full transition-all ${config.whitelistEnabled ? 'left-7' : 'left-1'}`} />
                    </button>
                  </div>
                </motion.div>
              )}

              {currentStep === 1 && (
                <motion.div
                  key="step-1"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="space-y-8"
                >
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-12">
                    <div className="space-y-8">
                      <div className="space-y-2">
                        <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Primary Brand Color</label>
                        <div className="flex gap-4">
                          <input 
                            type="color" 
                            className="w-12 h-12 rounded-lg border-none cursor-pointer"
                            value={config.primaryColor}
                            onChange={(e) => setConfig({...config, primaryColor: e.target.value})}
                          />
                          <input 
                            type="text" 
                            className="flex-1 px-4 py-3 rounded-xl border border-zinc-200 bg-white focus:outline-none uppercase font-mono text-xs"
                            value={config.primaryColor}
                            onChange={(e) => setConfig({...config, primaryColor: e.target.value})}
                          />
                        </div>
                      </div>

                      <div className="space-y-2">
                        <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Logo URL (SVG/PNG)</label>
                        <input 
                          type="text" 
                          placeholder="https://your-brand.com/logo.svg"
                          className="w-full px-4 py-3 rounded-xl border border-zinc-200 bg-white focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all"
                          value={config.logoUrl}
                          onChange={(e) => setConfig({...config, logoUrl: e.target.value})}
                        />
                      </div>
                    </div>

                    <div className="space-y-4">
                      <label className="text-[11px] font-bold uppercase tracking-widest text-zinc-400">Live Preview</label>
                      <div className="aspect-video bg-white border border-zinc-200 rounded-2xl p-6 flex flex-col justify-between shadow-sm">
                        <div className="flex justify-between items-start">
                          {config.logoUrl ? (
                            <img src={config.logoUrl} alt="Logo" className="h-6 object-contain" />
                          ) : (
                            <div className="h-6 w-24 bg-zinc-100 rounded animate-pulse" />
                          )}
                          <div className="w-8 h-8 rounded-full bg-zinc-50" />
                        </div>
                        <div>
                          <div className="text-[10px] font-bold text-zinc-400 uppercase mb-1">Vault Balance</div>
                          <div className="text-2xl font-heading font-bold">$0.00</div>
                        </div>
                        <button 
                          className="w-full py-3 rounded-xl text-white text-[10px] font-bold uppercase tracking-widest"
                          style={{ backgroundColor: config.primaryColor }}
                        >
                          Deposit Now
                        </button>
                      </div>
                    </div>
                  </div>
                </motion.div>
              )}

              {currentStep === 2 && (
                <motion.div
                  key="step-2"
                  initial={{ opacity: 0, x: 20 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -20 }}
                  className="flex flex-col items-center justify-center text-center py-12"
                >
                  <div className="w-20 h-20 bg-primary/10 rounded-full flex items-center justify-center text-primary mb-8 animate-pulse">
                    <Rocket size={40} />
                  </div>
                  <h3 className="text-2xl font-heading font-bold mb-4 uppercase">Ready for Deployment</h3>
                  <p className="text-zinc-500 font-medium max-w-md mb-8">
                    Deploying your vault requires a one-time protocol fee of <span className="text-zinc-900 font-bold">0.05 ETH</span>. 
                    This covers the smart contract deployment and initializes the hedging engine.
                  </p>
                  <div className="w-full max-w-sm p-6 bg-white border border-zinc-200 rounded-2xl space-y-4 mb-8">
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-zinc-400">Vault Name</span>
                      <span>{config.name || 'Unnamed Fund'}</span>
                    </div>
                    <div className="flex justify-between text-xs font-medium">
                      <span className="text-zinc-400">Performance Fee</span>
                      <span>{config.performanceFee}%</span>
                    </div>
                    <div className="pt-4 border-t border-zinc-100 flex justify-between text-sm font-bold">
                      <span>Total Due</span>
                      <span className="text-primary">
                        {deploymentFee ? formatEther(deploymentFee) : '0.05'} ETH
                      </span>
                    </div>
                  </div>
                  
                  {(isDeploying || isWaitingForTx) && (
                    <div className="flex items-center gap-3 text-primary font-bold animate-pulse">
                      <Loader2 className="animate-spin" size={20} />
                      <span className="text-xs uppercase tracking-widest">
                        {isWaitingForTx ? 'Confirming on-chain...' : 'Awaiting Signature...'}
                      </span>
                    </div>
                  )}
                </motion.div>
              )}

              {currentStep === 3 && (
                <motion.div
                  key="step-3"
                  initial={{ opacity: 0, scale: 0.95 }}
                  animate={{ opacity: 1, scale: 1 }}
                  className="flex flex-col items-center justify-center text-center py-12"
                >
                  <div className="w-20 h-20 bg-green-500 text-white rounded-full flex items-center justify-center mb-8 shadow-lg shadow-green-500/20">
                    <CheckCircle2 size={40} />
                  </div>
                  <h3 className="text-2xl font-heading font-bold mb-4 uppercase">Vault Deployed!</h3>
                  <p className="text-zinc-500 font-medium max-w-md mb-12">
                    Your institutional vault is now live on Base. Download your configuration file to launch your branded frontend.
                  </p>
                  
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 w-full max-w-lg">
                    <button 
                      onClick={downloadConfig}
                      className="flex items-center justify-center gap-3 p-4 bg-zinc-900 text-white rounded-2xl font-bold uppercase tracking-wider text-xs hover:bg-zinc-800 transition-all"
                    >
                      <Download size={18} /> Download Config
                    </button>
                    <Link href={`/partner/${deployedAddress || '0x...'}/dashboard`} className="flex items-center justify-center gap-3 p-4 border border-zinc-200 text-zinc-900 rounded-2xl font-bold uppercase tracking-wider text-xs hover:bg-zinc-50 transition-all">
                      <ExternalLink size={18} /> Partner Dashboard
                    </Link>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>

            {/* Navigation Buttons */}
            {currentStep < 3 && (
              <div className="mt-12 flex justify-between items-center pt-8 border-t border-zinc-100">
                <button 
                  onClick={prevStep}
                  disabled={currentStep === 0}
                  className={`text-[11px] font-bold uppercase tracking-widest transition-all ${currentStep === 0 ? 'opacity-0 pointer-events-none' : 'text-zinc-400 hover:text-zinc-900'}`}
                >
                  Back
                </button>
                <button 
                  onClick={nextStep}
                  disabled={isDeploying || isWaitingForTx}
                  className={`px-8 py-4 bg-primary text-white rounded-xl font-bold uppercase tracking-widest text-[11px] flex items-center gap-3 hover:bg-primary-dark transition-all shadow-lg shadow-primary/20 ${(isDeploying || isWaitingForTx) ? 'opacity-50 cursor-not-allowed' : ''}`}
                >
                  {currentStep === 2 ? (isDeploying || isWaitingForTx ? 'Deploying...' : 'Deploy Vault') : 'Continue'} <ArrowRight size={16} />
                </button>
              </div>
            )}
          </div>

          {/* Info Cards */}
          {currentStep < 3 && (
            <div className="mt-12 grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
                <Zap className="text-primary mb-4" size={20} />
                <h5 className="text-[10px] font-bold uppercase tracking-widest mb-2">Instant Liquidity</h5>
                <p className="text-[10px] text-zinc-400 font-medium leading-relaxed">
                  Your vault is automatically integrated into the Kerne hedging engine for delta-neutral yield.
                </p>
              </div>
              <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
                <Globe className="text-primary mb-4" size={20} />
                <h5 className="text-[10px] font-bold uppercase tracking-widest mb-2">Global Reach</h5>
                <p className="text-[10px] text-zinc-400 font-medium leading-relaxed">
                  Launch your fund to a global audience with a fully branded, non-custodial interface.
                </p>
              </div>
              <div className="p-6 bg-white border border-zinc-100 rounded-2xl">
                <Shield className="text-primary mb-4" size={20} />
                <h5 className="text-[10px] font-bold uppercase tracking-widest mb-2">Secure & Audited</h5>
                <p className="text-[10px] text-zinc-400 font-medium leading-relaxed">
                  Built on the same audited smart contracts that power the core Kerne Protocol.
                </p>
              </div>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}
