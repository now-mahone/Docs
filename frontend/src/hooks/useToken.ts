// Created: 2025-12-28
import { useReadContract, useWriteContract, useWaitForTransactionReceipt } from 'wagmi';
import { erc20Abi, parseUnits } from 'viem';
import { WETH_ADDRESS } from '../config';

export function useToken(owner?: `0x${string}`, spender?: `0x${string}`, tokenAddress: `0x${string}` = WETH_ADDRESS) {
  const { data: allowance, refetch: refetchAllowance } = useReadContract({
    address: tokenAddress,
    abi: erc20Abi,
    functionName: 'allowance',
    args: owner && spender ? [owner, spender] : undefined,
    query: {
      enabled: !!owner && !!spender,
    },
  });

  const { data: balance, refetch: refetchBalance } = useReadContract({
    address: tokenAddress,
    abi: erc20Abi,
    functionName: 'balanceOf',
    args: owner ? [owner] : undefined,
    query: {
      enabled: !!owner,
    },
  });

  const { writeContract, data: hash, isPending, error } = useWriteContract();

  const { isLoading: isConfirming, isSuccess: isConfirmed } = useWaitForTransactionReceipt({
    hash,
  });

  const approve = async (amount: string) => {
    if (!spender) return;
    const amountBI = parseUnits(amount, 18);
    writeContract({
      address: tokenAddress,
      abi: erc20Abi,
      functionName: 'approve',
      args: [spender, amountBI],
    });
  };

  return {
    allowance: allowance as bigint | undefined,
    balance: balance as bigint | undefined,
    approve,
    isPending: isPending || isConfirming,
    isConfirmed,
    error,
    refetchAllowance,
    refetchBalance,
  };
}
