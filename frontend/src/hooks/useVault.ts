// Created: 2025-12-28
import { useReadContract, useWriteContract, useAccount, useChainId } from 'wagmi';
import { CONTRACT_ADDRESSES, DEFAULT_CHAIN_ID } from '@/constants/addresses';
import KerneVaultABI from '@/abis/KerneVault.json';

export function useVault() {
  const { address } = useAccount();
  const chainId = useChainId();
  
  const addresses = CONTRACT_ADDRESSES[chainId] || CONTRACT_ADDRESSES[DEFAULT_CHAIN_ID];
  const VAULT_ADDRESS = addresses.VAULT;

  // Read functions
  const { data: totalAssets, refetch: refetchTotalAssets } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'totalAssets',
    query: {
      enabled: VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: balanceOf, refetch: refetchBalanceOf } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: convertToAssets } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'convertToAssets',
    args: balanceOf ? [balanceOf] : undefined,
    query: {
      enabled: !!balanceOf && VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: offChainAssets } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'offChainAssets',
    query: {
      enabled: VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: asset } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'asset',
    query: {
      enabled: VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: grossPerformanceFeeBps } = useReadContract({
    address: VAULT_ADDRESS,
    abi: KerneVaultABI.abi,
    functionName: 'grossPerformanceFeeBps',
    query: {
      enabled: VAULT_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  // Write functions
  const { writeContract, data: hash, isPending, isSuccess, error } = useWriteContract();

  const deposit = (amount: bigint) => {
    writeContract({
      address: VAULT_ADDRESS,
      abi: KerneVaultABI.abi,
      functionName: 'deposit',
      args: [amount, address],
    });
  };

  const withdraw = (shares: bigint) => {
    writeContract({
      address: VAULT_ADDRESS,
      abi: KerneVaultABI.abi,
      functionName: 'withdraw',
      args: [shares, address, address],
    });
  };

  return {
    totalAssets: totalAssets as bigint | undefined,
    balanceOf: balanceOf as bigint | undefined,
    convertToAssets: convertToAssets as bigint | undefined,
    offChainAssets: offChainAssets as bigint | undefined,
    asset: asset as `0x${string}` | undefined,
    grossPerformanceFeeBps: grossPerformanceFeeBps as bigint | undefined,
    deposit,
    withdraw,
    isPending,
    isSuccess,
    hash,
    error,
    refetchTotalAssets,
    refetchBalanceOf,
  };
}
