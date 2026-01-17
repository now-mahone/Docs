// Created: 2026-01-09
'use client';

import { useReadContract, useWriteContract, useAccount } from 'wagmi';
import { parseUnits, formatUnits } from 'viem';
import { useWhiteLabel } from '../context/WhiteLabelContext';

const VAULT_ABI = [
  {
    name: 'deposit',
    type: 'function',
    stateMutability: 'nonpayable',
    inputs: [
      { name: 'assets', type: 'uint256' },
      { name: 'receiver', type: 'address' },
    ],
    outputs: [{ name: 'shares', type: 'uint256' }],
  },
  {
    name: 'totalAssets',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint256' }],
  },
  {
    name: 'balanceOf',
    type: 'function',
    stateMutability: 'view',
    inputs: [{ name: 'account', type: 'address' }],
    outputs: [{ name: '', type: 'uint256' }],
  },
  {
    name: 'asset',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'address' }],
  },
] as const;

const ERC20_ABI = [
  {
    name: 'decimals',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint8' }],
  },
] as const;

export function useVault() {
  const { vaultAddress } = useWhiteLabel();
  const { address } = useAccount();
  const { writeContractAsync } = useWriteContract();

  const { data: assetAddress } = useReadContract({
    address: vaultAddress,
    abi: VAULT_ABI,
    functionName: 'asset',
  });

  const { data: decimals } = useReadContract({
    address: assetAddress,
    abi: ERC20_ABI,
    functionName: 'decimals',
    query: {
        enabled: !!assetAddress
    }
  });

  const { data: totalAssets, refetch: refetchTotalAssets } = useReadContract({
    address: vaultAddress,
    abi: VAULT_ABI,
    functionName: 'totalAssets',
  });

  const { data: userBalance, refetch: refetchUserBalance } = useReadContract({
    address: vaultAddress,
    abi: VAULT_ABI,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
        enabled: !!address
    }
  });

  const deposit = async (amount: string) => {
    if (!address || decimals === undefined) return;
    const assets = parseUnits(amount, decimals);
    return writeContractAsync({
      address: vaultAddress,
      abi: VAULT_ABI,
      functionName: 'deposit',
      args: [assets, address],
    });
  };

  return {
    totalAssets: totalAssets && decimals !== undefined ? formatUnits(totalAssets, decimals) : '0',
    userBalance: userBalance && decimals !== undefined ? formatUnits(userBalance, decimals) : '0',
    deposit,
    decimals: decimals ?? 18,
    refetch: () => {
      refetchTotalAssets();
      refetchUserBalance();
    },
  };
}

