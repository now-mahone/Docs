// Created: 2026-01-06
'use client';

import { useAccount, useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { PRIME_ADDRESS } from '@/constants/addresses';
import { parseEther } from 'viem';

const PRIME_ABI = [
  {
    "inputs": [{"internalType": "address", "name": "", "type": "address"}],
    "name": "primeAccounts",
    "outputs": [
      {"internalType": "bool", "name": "active", "type": "bool"},
      {"internalType": "uint256", "name": "balance", "type": "uint256"},
      {"internalType": "uint256", "name": "lastTradeTimestamp", "type": "uint256"},
      {"internalType": "address", "name": "vault", "type": "address"}
    ],
    "stateMutability": "view",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "_amount", "type": "uint256"}],
    "name": "allocateToPrime",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  },
  {
    "inputs": [{"internalType": "uint256", "name": "_amount", "type": "uint256"}],
    "name": "deallocateFromPrime",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
] as const;

export function usePrime() {
  const { address } = useAccount();
  const { writeContract, data: hash } = useWriteContract();

  const { data: accountData, refetch } = useReadContract({
    address: PRIME_ADDRESS as `0x${string}`,
    abi: PRIME_ABI,
    functionName: 'primeAccounts',
    args: [address as `0x${string}`],
    query: {
      enabled: !!address,
    }
  });

  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  const allocate = async (amount: string) => {
    writeContract({
      address: PRIME_ADDRESS as `0x${string}`,
      abi: PRIME_ABI,
      functionName: 'allocateToPrime',
      args: [parseEther(amount)],
    });
  };

  const deallocate = async (amount: string) => {
    writeContract({
      address: PRIME_ADDRESS as `0x${string}`,
      abi: PRIME_ABI,
      functionName: 'deallocateFromPrime',
      args: [parseEther(amount)],
    });
  };

  return {
    account: accountData ? {
      active: accountData[0],
      balance: accountData[1],
      lastTradeTimestamp: accountData[2],
      vault: accountData[3]
    } : null,
    allocate,
    deallocate,
    isConfirming,
    isConfirmed,
    refetch
  };
}
