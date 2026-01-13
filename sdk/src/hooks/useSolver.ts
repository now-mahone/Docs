// Created: 2026-01-13
import { useContractRead, useContractWrite, useAccount } from 'wagmi';
import { parseEther, formatEther } from 'viem';

const INTENT_EXECUTOR_ABI = [
  {
    "inputs": [
      { "name": "tokenIn", "type": "address" },
      { "name": "tokenOut", "type": "address" },
      { "name": "amount", "type": "uint256" },
      { "name": "user", "type": "address" },
      { "name": "aggregatorData", "type": "bytes" }
    ],
    "name": "fulfillIntent",
    "outputs": [],
    "stateMutability": "nonpayable",
    "type": "function"
  }
] as const;

export function useSolver(executorAddress: `0x${string}`) {
  const { address } = useAccount();

  const { writeAsync: fulfillIntent } = useContractWrite({
    address: executorAddress,
    abi: INTENT_EXECUTOR_ABI,
    functionName: 'fulfillIntent',
  });

  return {
    fulfillIntent,
    address,
  };
}
