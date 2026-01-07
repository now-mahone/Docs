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
        <button className="flex items-center gap-2 px-3 py-1.5 bg-zinc-900/50 border border-zinc-800 hover:border-emerald-500/50 transition-all rounded-sm text-[10px] font-bold uppercase tracking-widest">
          <Globe size={12} className="text-emerald-500" />
          <span>{currentChain.name}</span>
          <ChevronDown size={12} className="text-zinc-500" />
        </button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="bg-obsidian border-zinc-800 font-mono">
        {chains.map((chain) => (
          <DropdownMenuItem
            key={chain.id}
            onClick={() => switchChain({ chainId: chain.id })}
            className="text-[10px] uppercase tracking-widest focus:bg-emerald-500/10 focus:text-emerald-500 cursor-pointer gap-2"
          >
            <span>{chain.icon}</span>
            {chain.name}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
