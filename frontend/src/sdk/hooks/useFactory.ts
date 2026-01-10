// Created: 2026-01-09
'use client';

import { useReadContract, useWriteContract, useAccount } from 'wagmi';
import { parseEther } from 'viem';

const FACTORY_ABI = [
  {
    name: 'deployVault',
    type: 'function',
    stateMutability: 'payable',
    inputs: [
      { name: 'asset', type: 'address' },
      { name: 'name', type: 'string' },
      { name: 'symbol', type: 'string' },
      { name: 'admin', type: 'address' },
      { name: 'performanceFeeBps', type: 'uint256' },
      { name: 'whitelistEnabled', type: 'bool' },
      { name: 'maxTotalAssets', type: 'uint256' },
    ],
    outputs: [{ name: '', type: 'address' }],
  },
  {
    name: 'deploymentFee',
    type: 'function',
    stateMutability: 'view',
    inputs: [],
    outputs: [{ name: '', type: 'uint256' }],
  },
] as const;

export function useFactory(factoryAddress: `0x${string}`) {
  const { address } = useAccount();
  const { writeContractAsync } = useWriteContract();

  const { data: deploymentFee } = useReadContract({
    address: factoryAddress,
    abi: FACTORY_ABI,
    functionName: 'deploymentFee',
  });

  const deployVault = async (params: {
    asset: `0x${string}`;
    name: string;
    symbol: string;
    performanceFeeBps: number;
    whitelistEnabled: boolean;
    maxTotalAssets: string;
  }) => {
    if (!address) return;
    
    return writeContractAsync({
      address: factoryAddress,
      abi: FACTORY_ABI,
      functionName: 'deployVault',
      args: [
        params.asset,
        params.name,
        params.symbol,
        address,
        BigInt(params.performanceFeeBps),
        params.whitelistEnabled,
        BigInt(params.maxTotalAssets),
      ],
      value: deploymentFee || parseEther('0.05'),
    });
  };

  return {
    deployVault,
    deploymentFee,
  };
}
