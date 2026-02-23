// Created: 2025-12-29
'use client';

import { useState, useMemo } from 'react';
import { useAccount } from 'wagmi';
import { formatUnits, parseUnits } from 'viem';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useKUSD } from '@/hooks/useKUSD';
import { useVault } from '@/hooks/useVault';
import { KUSD_MINTER_ADDRESS, VAULT_ADDRESS } from '@/config';
import { toast } from 'sonner';
import { useToken } from '@/hooks/useToken';

export function KUSDInterface() {
  const { address } = useAccount();
  const { 
    kusdBalance, 
    collateralAmount, 
    debtAmount, 
    klpPrice, 
    isHealthy, 
    healthFactor,
    mint, 
    burn, 
    leverage,
    fold,
    isPending: isKUSDPending,
    refetchKUSDBalance,
    refetchPosition
  } = useKUSD();

  const { balanceOf: klpBalance, refetchBalanceOf: refetchKLPBalance, asset: vaultAsset } = useVault();
  const { allowance: klpAllowance, approve: approveKLP, refetchAllowance: refetchKLPAllowance } = useToken(address, KUSD_MINTER_ADDRESS, VAULT_ADDRESS);
  const { allowance: assetAllowance, approve: approveAsset, refetchAllowance: refetchAssetAllowance, balance: assetBalance } = useToken(address, KUSD_MINTER_ADDRESS, vaultAsset);

  const [mintAmount, setMintAmount] = useState('');
  const [collateralToAdd, setCollateralToAdd] = useState('');
  const [repayAmount, setRepayAmount] = useState('');
  const [collateralToRemove, setCollateralToRemove] = useState('');
  const [leverageWeth, setLeverageWeth] = useState('');
  const [leverageKusd, setLeverageKusd] = useState('');
  const [foldAmount, setFoldAmount] = useState('');

  const isPending = isKUSDPending;

  const projectedFoldAPY = useMemo(() => {
    if (!foldAmount) return null;
    // Base Vault Yield (Simulated 15%) + Leverage Multiplier
    // Folded APY = (Base Yield * Leverage) - (Borrow Cost * (Leverage - 1))
    const baseYield = 15.4;
    const borrowCost = 2.5; // kUSD borrow rate
    const leverageFactor = 1 + (Number(foldAmount) / Number(formatUnits(collateralAmount || 1n, 18)));
    return (baseYield * leverageFactor) - (borrowCost * (leverageFactor - 1));
  }, [foldAmount, collateralAmount]);

  const handleMint = async () => {
    if (!mintAmount && !collateralToAdd) return;
    const toastId = toast.loading("EXECUTING MINT...");
    try {
      const klpBI = parseUnits(collateralToAdd || '0', 18);
      const kusdBI = parseUnits(mintAmount || '0', 18);
      await mint(klpBI, kusdBI);
      setMintAmount('');
      setCollateralToAdd('');
      refetchKUSDBalance();
      refetchPosition();
      refetchKLPBalance();
      toast.success("MINT SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("MINT FAILED", { id: toastId });
    }
  };

  const handleBurn = async () => {
    if (!repayAmount && !collateralToRemove) return;
    const toastId = toast.loading("EXECUTING BURN...");
    try {
      const kusdBI = parseUnits(repayAmount || '0', 18);
      const klpBI = parseUnits(collateralToRemove || '0', 18);
      await burn(kusdBI, klpBI);
      setRepayAmount('');
      setCollateralToRemove('');
      refetchKUSDBalance();
      refetchPosition();
      refetchKLPBalance();
      toast.success("BURN SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("BURN FAILED", { id: toastId });
    }
  };

  const handleApproveKLP = async () => {
    if (!collateralToAdd) return;
    const toastId = toast.loading("APPROVING kLP...");
    try {
      await approveKLP(collateralToAdd);
      refetchKLPAllowance();
      toast.success("kLP APPROVED", { id: toastId });
    } catch (e) {
      toast.error("APPROVAL FAILED", { id: toastId });
    }
  };

  const handleApproveAsset = async () => {
    if (!leverageWeth) return;
    const toastId = toast.loading("APPROVING WETH...");
    try {
      await approveAsset(leverageWeth);
      refetchAssetAllowance();
      toast.success("WETH APPROVED", { id: toastId });
    } catch (e) {
      toast.error("APPROVAL FAILED", { id: toastId });
    }
  };

  const handleLeverage = async () => {
    if (!leverageWeth) return;
    const toastId = toast.loading("EXECUTING LEVERAGE...");
    try {
      const wethBI = parseUnits(leverageWeth, 18);
      const kusdBI = parseUnits(leverageKusd || '0', 18);
      await leverage(wethBI, kusdBI);
      setLeverageWeth('');
      setLeverageKusd('');
      refetchKUSDBalance();
      refetchPosition();
      refetchKLPBalance();
      toast.success("LEVERAGE SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("LEVERAGE FAILED", { id: toastId });
    }
  };

  const handleFold = async () => {
    if (!foldAmount) return;
    const toastId = toast.loading("EXECUTING RECURSIVE FOLD...");
    try {
      const amountBI = parseUnits(foldAmount, 18);
      // minKLPOut set to 99% for simulation
      const minKLPOut = (amountBI * 99n) / 100n;
      await fold(amountBI, minKLPOut);
      setFoldAmount('');
      refetchKUSDBalance();
      refetchPosition();
      refetchKLPBalance();
      toast.success("FOLD SUCCESSFUL", { id: toastId });
    } catch (e) {
      toast.error("FOLD FAILED", { id: toastId });
    }
  };

  const needsKLPApproval = useMemo(() => {
    if (!collateralToAdd || !klpAllowance) return false;
    try {
      return klpAllowance < parseUnits(collateralToAdd, 18);
    } catch {
      return true;
    }
  }, [collateralToAdd, klpAllowance]);

  const needsAssetApproval = useMemo(() => {
    if (!leverageWeth || !assetAllowance) return false;
    try {
      return assetAllowance < parseUnits(leverageWeth, 18);
    } catch {
      return true;
    }
  }, [leverageWeth, assetAllowance]);

  const currentCR = useMemo(() => {
    if (!debtAmount || debtAmount === 0n || !klpPrice) return null;
    const collateralValue = (collateralAmount * klpPrice) / 10n**18n;
    return (Number(collateralValue) * 100) / Number(debtAmount);
  }, [collateralAmount, debtAmount, klpPrice]);

  const liquidationPrice = useMemo(() => {
    if (!debtAmount || debtAmount === 0n || !collateralAmount || collateralAmount === 0n || !klpPrice) return null;
    // Liquidation happens when CR < 120% (1.2)
    // (Collateral * Price) / Debt = 1.2
    // Price = (1.2 * Debt) / Collateral
    const liqPriceBI = (120n * debtAmount * 10n**18n) / (100n * collateralAmount);
    return formatUnits(liqPriceBI, 18);
  }, [collateralAmount, debtAmount]);

  return (
    <Card className="bg-white border-[#f1f1ed] rounded-sm overflow-hidden mt-6">
      <CardHeader className="border-b border-[#f1f1ed] bg-[#f9f9f4]/30 px-6 py-4">
        <CardTitle className="text-xs font-bold text-zinc-400 uppercase tracking-tight">
          kUSD Synthetic Minter
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-2 gap-4 mb-8">
          <div className="px-4 py-3 bg-[#f1f1ed]/30 rounded-sm border border-[#f1f1ed]">
            <div className="text-xs font-bold text-zinc-400 uppercase tracking-tight">kUSD Balance</div>
            <div className="text-l font-heading font-medium text-[#000000] mt-1">
              {kusdBalance ? Number(formatUnits(kusdBalance, 18)).toFixed(2) : '0.00'}
            </div>
          </div>
          <div className="px-4 py-3 bg-[#f1f1ed]/30 rounded-sm border border-[#f1f1ed]">
            <div className="text-xs font-bold text-zinc-400 uppercase tracking-tight">Health Factor</div>
            <div className={`text-l font-heading font-medium mt-1 ${Number(healthFactor || 0n) > 1.2e18 ? 'text-primary' : 'text-red-500'}`}>
              {healthFactor ? (Number(formatUnits(healthFactor, 18))).toFixed(2) : 'N/A'}
            </div>
          </div>
        </div>

        <Tabs defaultValue="mint" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-[#f1f1ed] rounded-full p-1.5 h-12">
            <TabsTrigger value="mint" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs">Mint</TabsTrigger>
            <TabsTrigger value="leverage" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs">Leverage</TabsTrigger>
            <TabsTrigger value="fold" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs">Fold</TabsTrigger>
            <TabsTrigger value="burn" className="rounded-full data-[state=active]:bg-white data-[state=active]:text-primary font-bold text-xs">Repay</TabsTrigger>
          </TabsList>

          <TabsContent value="fold" className="mt-8 space-y-6">
            <div className="px-4 py-3 bg-primary/5 border border-primary/10 rounded-sm text-xs font-medium text-primary">
              Recursive Folding: Flash-mint kUSD to increase collateral exposure instantly.
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div className="p-4 bg-[#f1f1ed]/30 rounded-sm border border-[#f1f1ed]">
                <div className="text-xs font-bold text-zinc-400 uppercase">Projected APY</div>
                <div className="text-l font-heading font-medium text-primary mt-1">
                  {projectedFoldAPY ? `${projectedFoldAPY.toFixed(2)}%` : '15.40%'}
                </div>
              </div>
              <div className="p-4 bg-[#f1f1ed]/30 rounded-sm border border-[#f1f1ed]">
                <div className="text-xs font-bold text-zinc-400 uppercase">Risk Level</div>
                <div className={`text-l font-heading font-bold mt-1 ${!foldAmount ? 'text-primary' : 'text-red-500'}`}>
                  {!foldAmount ? 'Low' : 'Med'}
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-400">Fold Amount (kUSD)</label>
              <Input
                type="number"
                placeholder="0.00 kUSD"
                value={foldAmount}
                onChange={(e) => setFoldAmount(e.target.value)}
                className="bg-[#f9f9f4] border-[#f1f1ed] rounded-sm font-bold text-l h-14 px-4 shadow-none"
              />
            </div>

            <button
              onClick={handleFold}
              disabled={isPending || !foldAmount}
              className="w-full bg-primary text-[#f9f9f4] hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
            >
              Execute Fold
            </button>
          </TabsContent>

          <TabsContent value="leverage" className="mt-8 space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-400">Deposit WETH</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 WETH"
                  value={leverageWeth}
                  onChange={(e) => setLeverageWeth(e.target.value)}
                  className="bg-[#f9f9f4] border-[#f1f1ed] rounded-sm font-bold text-l h-14 px-4 shadow-none"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => assetBalance && setLeverageWeth(formatUnits(assetBalance, 18))}
                  className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7 shadow-none"
                >
                  Max
                </Button>
              </div>
            </div>

            {needsAssetApproval ? (
              <button
                onClick={handleApproveAsset}
                disabled={isPending}
                className="w-full bg-primary text-[#f9f9f4] hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
              >
                Approve WETH
              </button>
            ) : (
              <button
                onClick={handleLeverage}
                disabled={isPending || !leverageWeth}
                className="w-full bg-primary text-[#f9f9f4] hover:bg-primary-dark rounded-full font-bold h-14 transition-all text-s"
              >
                Execute Leverage
              </button>
            )}
          </TabsContent>

          <TabsContent value="mint" className="mt-8 space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-400">Add kLP Collateral</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 kLP"
                  value={collateralToAdd}
                  onChange={(e) => setCollateralToAdd(e.target.value)}
                  className="bg-zinc-50 border-zinc-100 rounded-sm font-bold text-l h-14 px-4"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => klpBalance && setCollateralToAdd(formatUnits(klpBalance, 18))}
                  className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7"
                >
                  Max
                </Button>
              </div>
            </div>

            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-400">Mint kUSD Debt</label>
              <Input
                type="number"
                placeholder="0.00 kUSD"
                value={mintAmount}
                onChange={(e) => setMintAmount(e.target.value)}
                className="bg-zinc-50 border-zinc-100 rounded-sm font-bold text-l h-14 px-4"
              />
            </div>

            {needsKLPApproval ? (
              <button
                onClick={handleApproveKLP}
                disabled={isPending}
                className="w-full bg-primary text-white hover:bg-primary-dark rounded-full font-bold h-14 shadow-sm transition-all text-s"
              >
                Approve kLP
              </button>
            ) : (
              <button
                onClick={handleMint}
                disabled={isPending || (!mintAmount && !collateralToAdd)}
                className="w-full bg-primary text-white hover:bg-primary-dark rounded-full font-bold h-14 shadow-sm transition-all text-s"
              >
                Confirm Mint
              </button>
            )}
          </TabsContent>

          <TabsContent value="burn" className="mt-8 space-y-6">
            <div className="space-y-3">
              <label className="text-xs font-bold text-zinc-400">Repay kUSD Debt</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 kUSD"
                  value={repayAmount}
                  onChange={(e) => setRepayAmount(e.target.value)}
                  className="bg-zinc-50 border-zinc-100 rounded-sm font-bold text-l h-14 px-4"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRepayAmount(formatUnits(debtAmount, 18))}
                  className="absolute right-3 top-3.5 text-xs font-bold hover:bg-white rounded-sm px-2 h-7"
                >
                  Max
                </Button>
              </div>
            </div>

            <button
              onClick={handleBurn}
              disabled={isPending || (!repayAmount && !collateralToRemove)}
              className="w-full bg-[#191919] text-[#f9f9f4] hover:bg-[#1f1f1f] rounded-full font-bold h-14 transition-all text-s"
            >
              Confirm Repayment
            </button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
