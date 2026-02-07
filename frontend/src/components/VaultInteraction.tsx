// Created: 2026-01-30
'use client';

import React, { useState } from 'react';
import { useAccount } from 'wagmi';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  DropdownMenu, 
  DropdownMenuContent, 
  DropdownMenuItem, 
  DropdownMenuTrigger 
} from '@/components/ui/dropdown-menu';
import { Vault, ChevronDown } from 'lucide-react';

export function VaultInteraction() {
  const { isConnected } = useAccount();
  const [amount, setAmount] = useState('');
  const [selectedChain, setSelectedChain] = useState('Base');

  // Hardcoded price for UI refinement phase, matching terminal simulation
  const ethPrice = 2400;
  const usdValue = amount ? (parseFloat(amount) * ethPrice).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : '0.00';

  const chainLogos: { [key: string]: string } = {
    'Base': '/Base-Square-Blue.svg',
    'Arbitrum': '/Arbitrum-Mark.svg',
    'OP Mainnet': '/OP-Mainnet.svg'
  };

  return (
    <div className="p-6 lg:p-8 bg-gradient-to-b from-[#22252a] via-[#16191c] to-[#000000] rounded-sm h-full flex flex-col">
      <div className="flex items-start justify-between mb-8">
        <div className="flex flex-col flex-1">
          <span className="text-xs font-bold text-[#aab9be] uppercase tracking-wide">Vault Interaction</span>
          <DropdownMenu modal={false}>
            <DropdownMenuTrigger className="flex items-center gap-4 text-xl font-heading font-medium text-[#ffffff] mt-4 outline-none text-left">
              <img src={chainLogos[selectedChain]} alt={selectedChain} className="w-5 h-5 object-contain" />
              {selectedChain}
              <ChevronDown size={20} className="text-[#aab9be] ml-1" />
            </DropdownMenuTrigger>
            <DropdownMenuContent align="start" className="bg-[#000000] border-[#444a4f] text-[#ffffff] min-w-[260px] p-4 shadow-2xl space-y-1">
              <DropdownMenuItem 
                onClick={() => setSelectedChain('Base')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/Base-Square-Blue.svg" alt="Base" className="w-5 h-5 object-contain" />
                Base
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => setSelectedChain('Arbitrum')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/Arbitrum-Mark.svg" alt="Arbitrum" className="w-5 h-5 object-contain" />
                Arbitrum
              </DropdownMenuItem>
              <DropdownMenuItem 
                onClick={() => setSelectedChain('OP Mainnet')}
                className="cursor-pointer bg-[#22252a] border border-[#444a4f] rounded-sm text-s font-medium py-3 px-4 flex items-center gap-3 focus:bg-[#22252a] focus:text-[#ffffff]"
              >
                <img src="/OP-Mainnet.svg" alt="OP Mainnet" className="w-5 h-5 object-contain" />
                OP Mainnet
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <Vault size={16} className="text-[#aab9be] flex-shrink-0" />
      </div>

      <Tabs defaultValue="deposit" className="flex-1 flex flex-col">
        <TabsList className="grid w-full grid-cols-2 bg-transparent gap-0 mb-8 border border-[#444a4f] rounded-sm p-0 h-12 overflow-hidden">
          <TabsTrigger 
            value="deposit" 
            className="rounded-none border-none bg-[#22252a] data-[state=active]:bg-[#ffffff] !text-[#d4dce1] data-[state=active]:!text-[#000000] font-bold text-s h-full border-r border-[#444a4f] shadow-none transition-all"
          >
            Deposit
          </TabsTrigger>
          <TabsTrigger 
            value="withdraw" 
            className="rounded-none border-none bg-[#22252a] data-[state=active]:bg-[#ffffff] !text-[#d4dce1] data-[state=active]:!text-[#000000] font-bold text-s h-full shadow-none transition-all"
          >
            Withdraw
          </TabsTrigger>
        </TabsList>

        <TabsContent value="deposit" className="flex-1 flex flex-col space-y-6 mt-0">
          <div className="space-y-3">
            <div className="flex justify-between items-end">
              <label className="text-s font-medium text-[#aab9be] tracking-tight block">Amount (WETH)</label>
              <span className="text-s font-medium text-[#aab9be] tracking-tight">Balance: 0.00</span>
            </div>
            <div className="relative">
              <input 
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#37d097] hover:text-[#37d097]/80 transition-colors">
                MAX
              </button>
            </div>
            <div className="flex justify-start mt-2">
              <span className="text-s font-medium text-[#aab9be] tracking-tight">≈ ${usdValue}</span>
            </div>
          </div>

          <div className="flex-1" />

          <button 
            disabled={!isConnected}
            className={`w-full h-12 font-bold text-s rounded-sm flex items-center justify-center transition-all ${
              isConnected 
                ? 'bg-[#ffffff] text-[#000000]' 
                : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-default'
            }`}
          >
            {isConnected ? 'Confirm Deposit' : 'Connect wallet to interact'}
          </button>
        </TabsContent>

        <TabsContent value="withdraw" className="flex-1 flex flex-col space-y-6 mt-0">
          <div className="space-y-3">
            <div className="flex justify-between items-end">
              <label className="text-s font-medium text-[#aab9be] tracking-tight block">Amount (Kerne-V1)</label>
              <span className="text-s font-medium text-[#aab9be] tracking-tight">Balance: 0.00</span>
            </div>
            <div className="relative">
              <input 
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.00"
                className="w-full bg-[#22252a] border border-[#444a4f] rounded-sm px-5 py-4 text-[#ffffff] font-medium focus:border-[#37d097] outline-none transition-colors shadow-none placeholder:font-medium placeholder:text-s placeholder:text-[#aab9be] [appearance:textfield] [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none"
              />
              <button className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-bold text-[#37d097] hover:text-[#37d097]/80 transition-colors">
                MAX
              </button>
            </div>
            <div className="flex justify-start mt-2">
              <span className="text-s font-medium text-[#aab9be] tracking-tight">≈ ${usdValue}</span>
            </div>
          </div>

          <div className="flex-1" />

          <button 
            disabled={!isConnected}
            className={`w-full h-12 font-bold text-s rounded-sm flex items-center justify-center transition-all ${
              isConnected 
                ? 'bg-transparent border border-[#ffffff] text-[#ffffff]' 
                : 'bg-transparent border border-[#444a4f] text-[#ffffff] cursor-default'
            }`}
          >
            {isConnected ? 'Confirm Withdrawal' : 'Connect wallet to interact'}
          </button>
        </TabsContent>
      </Tabs>

      {/* Risk Disclosure */}
      <div className="mt-8 pt-6 border-t border-[#444a4f]/30">
        <p className="text-xs text-[#444a4f] font-medium leading-relaxed">
          Risk Disclosure: Interacting with delta neutral vaults involves smart contract, execution, and counterparty risk. High frequency hedging may result in principal drawdown during extreme market volatility. Deposit only what you can afford to lose.
        </p>
      </div>
    </div>
  );
}