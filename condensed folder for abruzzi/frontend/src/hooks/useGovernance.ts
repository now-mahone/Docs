// Created: 2025-12-29
import { useReadContract, useWriteContract, useAccount } from 'wagmi';
import { KERNE_TOKEN_ADDRESS, KERNE_STAKING_ADDRESS } from '@/config';
import KerneTokenABI from '@/abis/KerneToken.json';
import KerneStakingABI from '@/abis/KerneStaking.json';

export function useGovernance() {
  const { address } = useAccount();

  // Read functions
  const { data: kerneBalance, refetch: refetchKerneBalance } = useReadContract({
    address: KERNE_TOKEN_ADDRESS,
    abi: KerneTokenABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  const { data: stakeInfo, refetch: refetchStake } = useReadContract({
    address: KERNE_STAKING_ADDRESS,
    abi: KerneStakingABI.abi,
    functionName: 'stakes',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  const { data: pendingRewards, refetch: refetchRewards } = useReadContract({
    address: KERNE_STAKING_ADDRESS,
    abi: KerneStakingABI.abi,
    functionName: 'getPendingRewards',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address,
    },
  });

  const { data: totalStaked } = useReadContract({
    address: KERNE_STAKING_ADDRESS,
    abi: KerneStakingABI.abi,
    functionName: 'totalStaked',
  });

  // Write functions
  const { writeContract, data: hash, isPending, isSuccess, error } = useWriteContract();

  const stake = (amount: bigint, duration: number) => {
    writeContract({
      address: KERNE_STAKING_ADDRESS,
      abi: KerneStakingABI.abi,
      functionName: 'stake',
      args: [amount, BigInt(duration)],
    });
  };

  const withdraw = () => {
    writeContract({
      address: KERNE_STAKING_ADDRESS,
      abi: KerneStakingABI.abi,
      functionName: 'withdraw',
    });
  };

  const claimRewards = () => {
    writeContract({
      address: KERNE_STAKING_ADDRESS,
      abi: KerneStakingABI.abi,
      functionName: 'claimRewards',
    });
  };

  return {
    kerneBalance: kerneBalance as bigint | undefined,
    stakedAmount: stakeInfo ? (stakeInfo as any)[0] as bigint : 0n,
    lockEnd: stakeInfo ? (stakeInfo as any)[1] as bigint : 0n,
    pendingRewards: pendingRewards as bigint | undefined,
    totalStaked: totalStaked as bigint | undefined,
    stake,
    withdraw,
    claimRewards,
    isPending,
    isSuccess,
    hash,
    error,
    refetchKerneBalance,
    refetchStake,
    refetchRewards,
  };
}
