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
    <Card className="bg-black border-zinc-800 rounded-none">
      <CardHeader className="border-b border-zinc-800">
        <CardTitle className="text-sm font-mono text-zinc-400 uppercase tracking-widest">
          kUSD_Synthetic_Dollar_Minter
        </CardTitle>
      </CardHeader>
      <CardContent className="p-6">
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
            <div className="text-[10px] text-zinc-500 uppercase">kUSD_Balance</div>
            <div className="text-lg text-white">{kusdBalance ? Number(formatUnits(kusdBalance, 18)).toFixed(2) : '0.00'}</div>
          </div>
          <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
            <div className="text-[10px] text-zinc-500 uppercase">Health_Factor</div>
            <div className={`text-lg ${Number(healthFactor || 0n) > 1.2e18 ? 'text-emerald-500' : Number(healthFactor || 0n) > 1.1e18 ? 'text-amber-500' : 'text-red-500'}`}>
              {healthFactor ? (Number(formatUnits(healthFactor, 18))).toFixed(2) : 'N/A'}
            </div>
          </div>
          <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
            <div className="text-[10px] text-zinc-500 uppercase">Collateral_Ratio</div>
            <div className={`text-lg ${isHealthy ? 'text-emerald-500' : 'text-red-500'}`}>
              {currentCR ? `${currentCR.toFixed(1)}%` : 'N/A'}
            </div>
          </div>
          <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
            <div className="text-[10px] text-zinc-500 uppercase">Liq_Price_(kLP)</div>
            <div className="text-lg text-red-400">
              {liquidationPrice ? `$${Number(liquidationPrice).toFixed(2)}` : 'N/A'}
            </div>
          </div>
        </div>

        <Tabs defaultValue="mint" className="w-full">
          <TabsList className="grid w-full grid-cols-4 bg-zinc-900 rounded-none p-1">
            <TabsTrigger value="mint" className="rounded-none font-mono">MINT</TabsTrigger>
            <TabsTrigger value="leverage" className="rounded-none font-mono">LEVERAGE</TabsTrigger>
            <TabsTrigger value="fold" className="rounded-none font-mono">FOLD</TabsTrigger>
            <TabsTrigger value="burn" className="rounded-none font-mono">REPAY</TabsTrigger>
          </TabsList>

          <TabsContent value="fold" className="mt-6 space-y-4">
            <div className="p-3 bg-blue-950/20 border border-blue-900/50 font-mono text-[10px] text-blue-500 uppercase mb-4">
              Recursive Folding: Flash-mint kUSD to increase collateral exposure in a single transaction.
            </div>

            <div className="grid grid-cols-2 gap-4 mb-4">
              <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
                <div className="text-[10px] text-zinc-500 uppercase">Projected_APY</div>
                <div className="text-lg text-blue-400">
                  {projectedFoldAPY ? `${projectedFoldAPY.toFixed(2)}%` : '15.40%'}
                </div>
              </div>
              <div className="p-3 bg-zinc-900 border border-zinc-800 font-mono">
                <div className="text-[10px] text-zinc-500 uppercase">Risk_Level</div>
                <div className={`text-lg ${!foldAmount ? 'text-emerald-500' : Number(foldAmount) > Number(formatUnits(collateralAmount || 0n, 18)) * 2 ? 'text-red-500' : 'text-amber-500'}`}>
                  {!foldAmount ? 'LOW' : Number(foldAmount) > Number(formatUnits(collateralAmount || 0n, 18)) * 2 ? 'HIGH' : 'MED'}
                </div>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Fold_Amount_(kUSD)</label>
              <Input
                type="number"
                placeholder="0.00 kUSD"
                value={foldAmount}
                onChange={(e) => setFoldAmount(e.target.value)}
                className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
              />
            </div>

            <Button
              onClick={handleFold}
              disabled={isPending || !foldAmount}
              className="w-full bg-blue-600 text-white hover:bg-blue-700 rounded-none font-mono"
            >
              EXECUTE_FOLD
            </Button>
          </TabsContent>

          <TabsContent value="leverage" className="mt-6 space-y-4">
            <div className="p-3 bg-emerald-950/20 border border-emerald-900/50 font-mono text-[10px] text-emerald-500 uppercase mb-4">
              One-Click Leverage: Deposit WETH, Mint kLP, and Mint kUSD in a single transaction.
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Deposit_WETH</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 WETH"
                  value={leverageWeth}
                  onChange={(e) => setLeverageWeth(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => assetBalance && setLeverageWeth(formatUnits(assetBalance, 18))}
                  className="absolute right-2 top-1 text-[10px] font-mono"
                >
                  MAX
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Mint_kUSD_Debt</label>
              <Input
                type="number"
                placeholder="0.00 kUSD"
                value={leverageKusd}
                onChange={(e) => setLeverageKusd(e.target.value)}
                className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
              />
            </div>

            {needsAssetApproval ? (
              <Button
                onClick={handleApproveAsset}
                disabled={isPending}
                className="w-full bg-white text-black hover:bg-zinc-200 rounded-none font-mono"
              >
                APPROVE_WETH
              </Button>
            ) : (
              <Button
                onClick={handleLeverage}
                disabled={isPending || !leverageWeth}
                className="w-full bg-emerald-600 text-white hover:bg-emerald-700 rounded-none font-mono"
              >
                EXECUTE_LEVERAGE
              </Button>
            )}
          </TabsContent>

          <TabsContent value="mint" className="mt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Add_kLP_Collateral</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 kLP"
                  value={collateralToAdd}
                  onChange={(e) => setCollateralToAdd(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => klpBalance && setCollateralToAdd(formatUnits(klpBalance, 18))}
                  className="absolute right-2 top-1 text-[10px] font-mono"
                >
                  MAX
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Mint_kUSD_Debt</label>
              <Input
                type="number"
                placeholder="0.00 kUSD"
                value={mintAmount}
                onChange={(e) => setMintAmount(e.target.value)}
                className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
              />
            </div>

            {needsKLPApproval ? (
              <Button
                onClick={handleApproveKLP}
                disabled={isPending}
                className="w-full bg-white text-black hover:bg-zinc-200 rounded-none font-mono"
              >
                APPROVE_kLP
              </Button>
            ) : (
              <Button
                onClick={handleMint}
                disabled={isPending || (!mintAmount && !collateralToAdd)}
                className="w-full bg-emerald-600 text-white hover:bg-emerald-700 rounded-none font-mono"
              >
                CONFIRM_MINT
              </Button>
            )}
          </TabsContent>

          <TabsContent value="burn" className="mt-6 space-y-4">
            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Repay_kUSD_Debt</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 kUSD"
                  value={repayAmount}
                  onChange={(e) => setRepayAmount(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setRepayAmount(formatUnits(debtAmount, 18))}
                  className="absolute right-2 top-1 text-[10px] font-mono"
                >
                  MAX
                </Button>
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-[10px] font-mono text-zinc-500 uppercase">Remove_kLP_Collateral</label>
              <div className="relative">
                <Input
                  type="number"
                  placeholder="0.00 kLP"
                  value={collateralToRemove}
                  onChange={(e) => setCollateralToRemove(e.target.value)}
                  className="bg-zinc-950 border-zinc-800 rounded-none font-mono"
                />
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setCollateralToRemove(formatUnits(collateralAmount, 18))}
                  className="absolute right-2 top-1 text-[10px] font-mono"
                >
                  MAX
                </Button>
              </div>
            </div>

            <Button
              onClick={handleBurn}
              disabled={isPending || (!repayAmount && !collateralToRemove)}
              className="w-full bg-zinc-100 text-black hover:bg-zinc-300 rounded-none font-mono"
            >
              CONFIRM_REPAYMENT
            </Button>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
