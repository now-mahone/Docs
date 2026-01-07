// Created: 2026-01-06
'use client';

import { useState, useMemo } from 'react';
import { useAccount } from 'wagmi';
import { formatUnits, parseUnits } from 'viem';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { toast } from 'sonner';
import { useKUSD } from '@/hooks/useKUSD';
import { useToken } from '@/hooks/useToken';
import { KUSD_ADDRESS, KERNE_ADDRESS } from '@/constants/addresses';

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
    <Card className="bg-black border-zinc-800 rounded-none">
      <CardHeader className="border-b border-zinc-800">
        <CardTitle className="text-sm font-mono text-zinc-400 uppercase tracking-widest">
          Omnichain_Bridge_(LayerZero_V2)
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6 space-y-4">
        <div className="p-3 bg-blue-950/20 border border-blue-900/50 font-mono text-[10px] text-blue-500 uppercase mb-4">
          Move assets between Base, Arbitrum, and Optimism with zero slippage.
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono text-zinc-500 uppercase">Select_Token</label>
          <Select value={token} onValueChange={setToken}>
            <SelectTrigger className="bg-zinc-950 border-zinc-800 rounded-none font-mono">
              <SelectValue placeholder="Select Token" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-950 border-zinc-800 text-white font-mono">
              <SelectItem value="kUSD">kUSD (Synthetic Dollar)</SelectItem>
              <SelectItem value="KERNE">KERNE (Governance)</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <label className="text-[10px] font-mono text-zinc-500 uppercase">Destination_Chain</label>
          <Select value={destinationChain} onValueChange={setDestinationChain}>
            <SelectTrigger className="bg-zinc-950 border-zinc-800 rounded-none font-mono">
              <SelectValue placeholder="Select Chain" />
            </SelectTrigger>
            <SelectContent className="bg-zinc-950 border-zinc-800 text-white font-mono">
              <SelectItem value="arbitrum">Arbitrum One</SelectItem>
              <SelectItem value="optimism">Optimism</SelectItem>
              <SelectItem value="mantle">Mantle</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <div className="flex justify-between">
            <label className="text-[10px] font-mono text-zinc-500 uppercase">Amount_to_Bridge</label>
            <span className="text-[10px] font-mono text-zinc-600 uppercase">
              Balance: {currentBalance ? Number(formatUnits(currentBalance, 18)).toFixed(2) : '0.00'}
            </span>
          </div>
          <div className="relative">
            <Input
              type="number"
              placeholder="0.00"
              value={amount}
              onChange={(e) => setAmount(e.target.value)}
              className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
            />
            <Button
              variant="ghost"
              size="sm"
              onClick={() => currentBalance && setAmount(formatUnits(currentBalance, 18))}
              className="absolute right-2 top-1 text-[10px] font-mono"
            >
              MAX
            </Button>
          </div>
        </div>

        <Button
          onClick={handleBridge}
          disabled={isBridging || !amount}
          className="w-full bg-blue-600 text-white hover:bg-blue-700 rounded-none font-mono"
        >
          INITIATE_OMNICHAIN_TRANSFER
        </Button>

        <div className="pt-4 border-t border-zinc-900">
          <div className="flex justify-between text-[10px] font-mono text-zinc-600 uppercase">
            <span>Estimated_Time</span>
            <span>~2-5 Minutes</span>
          </div>
          <div className="flex justify-between text-[10px] font-mono text-zinc-600 uppercase mt-1">
            <span>Bridge_Fee</span>
            <span>0.0005 ETH</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
