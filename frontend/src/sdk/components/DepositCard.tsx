// Created: 2026-01-09
'use client';

import React, { useState } from 'react';
import { useVault } from '../hooks/useVault';
import { useWhiteLabel } from '../context/WhiteLabelContext';

export function DepositCard() {
  const { brandName, assetSymbol, primaryColor } = useWhiteLabel();
  const { totalAssets, userBalance, deposit } = useVault();
  const [amount, setAmount] = useState('');
  const [loading, setLoading] = useState(false);

  const handleDeposit = async () => {
    if (!amount) return;
    setLoading(true);
    try {
      await deposit(amount);
      setAmount('');
    } catch (error) {
      console.error('Deposit failed', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl border border-white/10 bg-black/40 backdrop-blur-xl shadow-2xl">
      <h2 className="text-xl font-bold mb-4 text-white">{brandName} Vault</h2>
      
      <div className="grid grid-cols-2 gap-4 mb-6">
        <div className="p-4 rounded-xl bg-white/5">
          <p className="text-xs text-white/50 uppercase">Total Assets</p>
          <p className="text-lg font-mono text-white">{totalAssets} {assetSymbol}</p>
        </div>
        <div className="p-4 rounded-xl bg-white/5">
          <p className="text-xs text-white/50 uppercase">Your Balance</p>
          <p className="text-lg font-mono text-white">{userBalance} {assetSymbol}</p>
        </div>
      </div>

      <div className="space-y-4">
        <input
          type="number"
          value={amount}
          onChange={(e) => setAmount(e.target.value)}
          placeholder={`Amount in ${assetSymbol}`}
          className="w-full p-4 rounded-xl bg-white/5 border border-white/10 text-white focus:outline-none focus:border-[var(--primary-color)] transition-colors"
        />
        <button
          onClick={handleDeposit}
          disabled={loading || !amount}
          style={{ backgroundColor: primaryColor }}
          className="w-full p-4 rounded-xl font-bold text-black hover:opacity-90 disabled:opacity-50 transition-all"
        >
          {loading ? 'Processing...' : `Deposit ${assetSymbol}`}
        </button>
      </div>
    </div>
  );
}
