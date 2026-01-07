"use client";

import React from "react";
import { Share2, Check } from "lucide-react";
import { toast } from "sonner";

// Created: 2025-12-29

interface ShareYieldProps {
  userAddress?: string;
  yieldPercent?: string;
}

export default function ShareYield({ userAddress, yieldPercent = "12.42" }: ShareYieldProps) {
  const [copied, setCopied] = React.useState(false);

  const handleShare = () => {
    const shortAddress = userAddress ? `${userAddress.slice(0, 6)}...${userAddress.slice(-4)}` : "ANONYMOUS";
    const text = `[KERNE_TERMINAL_v1.0] | USER: ${shortAddress} | YIELD: +${yieldPercent}% | kerne.ai`;
    
    navigator.clipboard.writeText(text);
    setCopied(true);
    toast.success("PROOF_OF_YIELD COPIED TO CLIPBOARD");
    
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <button
      onClick={handleShare}
      className="flex items-center gap-2 px-4 py-2 bg-emerald-500/10 border border-emerald-500/30 text-emerald-500 font-mono text-[10px] uppercase tracking-widest hover:bg-emerald-500 hover:text-black transition-all group"
    >
      {copied ? <Check size={12} /> : <Share2 size={12} className="group-hover:scale-110 transition-transform" />}
      {copied ? "COPIED" : "Share_Proof_of_Yield"}
    </button>
  );
}
