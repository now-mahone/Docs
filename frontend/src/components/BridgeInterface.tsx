// Created: 2026-01-06
'use client';

import { useState, useMemo } from 'react';
import { useAccount } from 'wagmi';
import { formatUnits, parseUnits } from 'viem';
import { Card, CardContent, CardHeader, CardTitle } from './ui/card';
import { Button } from './ui/button';
import { Input } from './ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './ui/select';
import { toast } from 'sonner';
import { useKUSD } from '../hooks/useKUSD';
import { useToken } from '../hooks/useToken';
import { KUSD_ADDRESS, KERNE_ADDRESS } from '../constants/addresses';

export function BridgeInterface() {
  const { address } = useAccount();
  const { kusdBalance } = useKUSD();
  const { balance: kerneBalance } = useToken(address as `0x${string}`, address as `0x${string}`, KERNE_ADDRESS as `0x${string}`);

  const [token, setToken] = useState('kUSD');
  const [amount, setAmount] = useState('');
  const [destinationChain, setDestinationChain] = useState('arbitrum');
  const [isBridging, setIsBridging] = useState(false);

  const currentBalance = token === 'kUSD' ? kusdBalance : kerneBalance;

  const handleBridge = async () => {
    if (!amount || !address) return;
    setIsBridging(true);
    const toastId = toast.loading(`BRIDGING ${amount} ${token} TO ${destinationChain.toUpperCase()}...`);
    
    try {
      // Simulation of LayerZero OFT bridge call
      await new Promise(resolve => setTimeout(resolve, 2000));
      toast.success("BRIDGE TRANSACTION BROADCAST", { id: toastId });
      setAmount('');
    } catch (e) {
      toast.error("BRIDGE FAILED", { id: toastId });
    } finally {
      setIsBridging(false);
    }
  };

  return (
    <Card className="bg-white border-[#f1f1ed] rounded-sm overflow-hidden mt-6">
      <CardHeader className="border-b border-[#f1f1ed] bg-[#f9f9f4]/30 px-6 py-4">
        <CardTitle className="text-xs font-bold text-zinc-400 uppercase tracking-tight">
          Omnichain Bridge (LayerZero V2)
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 space-y-6">
        <div className="px-4 py-3 bg-primary/5 border border-primary/10 rounded-sm text-xs font-medium text-primary">
          Move assets between Base, Arbitrum, and Optimism with zero slippage.
        </div>

        <div className="space-y-3">
          <label className="text-xs font-bold text-zinc-400">Select Token</label>
          <Select value={token} onValueChange={setToken}>
            <SelectTrigger className="bg-[#f1f1ed]/30 border-[#f1f1ed] rounded-sm font-bold text-xs h-12 px-4 shadow-none">
              <SelectValue placeholder="Select Token" />
            </SelectTrigger>
            <SelectContent className="bg-white border-[#f1f1ed]">
              <SelectItem value="kUSD" className="text-xs font-medium">kUSD (Synthetic Dollar)</SelectItem>
              <SelectItem value="KERNE" className="text-xs font-medium">KERNE (Governance)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <label className="text-xs font-bold text-zinc-400">Destination Chain</label>
          <Select value={destinationChain} onValueChange={setDestinationChain}>
            <SelectTrigger className="bg-[#f1f1ed]/30 border-[#f1f1ed] rounded-sm font-bold text-xs h-12 px-4 shadow-none">
              <SelectValue placeholder="Select Chain" />
            </SelectTrigger>
            <SelectContent className="bg-white border-[#f1f1ed]">
              <SelectItem value="arbitrum" className="text-xs font-medium">Arbitrum One</SelectItem>
              <SelectItem value="optimism" className="text-xs font-medium">Optimism</SelectItem>
              <SelectItem value="mantle" className="text-xs font-medium">Mantle</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-3">
          <div className="flex justify-between">
            <label className="text-xs font-bold text-zinc-400">Amount to Bridge</label>
            <span className="text-xs font-bold text-zinc-500">
              Balance: {currentBalance ? Number(formatUnits(currentBalance, 18)).toFixed(2) : '0.00'}
            </span>
          </div>
          <div className="relative">
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="bg-[#f9f9f4] border-[#f1f1ed] rounded-sm font-bold text-l h-14 px-4 shadow-none"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => currentBalance && setAmount(formatUnits(currentBalance, 18))}
              className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7 shadow-none"
            >
              Max
            </Button>
          </div>
        </div>

        <button
          onClick={handleBridge}
          disabled={isBridging || !amount}
          className="w-full bg-primary text-[#f9f9f4] hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
        >
          Initiate Transfer
        </button>

        <div className="pt-6 border-t border-[#f1f1ed] space-y-2">
          <div className="flex justify-between text-xs font-medium text-zinc-400">
            <span>Estimated Time</span>
            <span className="font-bold text-[#000000]">~2-5 Minutes</span>
          </div>
          <div className="flex justify-between text-xs font-medium text-zinc-400">
            <span>Bridge Fee</span>
            <span className="font-bold text-[#000000]">0.0005 ETH</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
