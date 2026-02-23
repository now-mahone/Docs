// Created: 2026-01-06
'use client';

import React from 'react';
import { useChainId, useSwitchChain } from 'wagmi';
import { base, arbitrum, optimism, foundry } from 'wagmi/chains';
import { ChevronDown, Globe } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";

const chains = [
  { id: base.id, name: 'Base', icon: '🔵' },
  { id: arbitrum.id, name: 'Arbitrum', icon: '💙' },
  { id: optimism.id, name: 'Optimism', icon: '🔴' },
  { id: foundry.id, name: 'Foundry', icon: '🛠️' },
];

export function ChainSwitcher() {
  const chainId = useChainId();
  const { switchChain } = useSwitchChain();

  const currentChain = chains.find(c => c.id === chainId) || chains[0];

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button className="flex items-center gap-2 px-4 py-2 bg-[#f9f9f4] border border-[#f1f1ed] hover:border-primary/50 transition-all rounded-full text-xs font-bold text-[#000000]">
          <Globe size={14} className="text-primary" />
          <span>{currentChain.name}</span>
          <ChevronDown size={14} className="text-zinc-400" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-white border-[#f1f1ed] rounded-sm p-1 min-w-[140px]">
        {chains.map((chain) => (
          <DropdownMenuItem
            key={chain.id}
            onClick={() => switchChain?.({ chainId: chain.id })}
            className="text-xs font-bold text-[#1f1f1f] focus:bg-[#f9f9f4] focus:text-primary cursor-pointer gap-3 px-3 py-2 rounded-sm transition-colors"
          >
            <span className="text-[14px]">{chain.icon}</span>
            {chain.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
