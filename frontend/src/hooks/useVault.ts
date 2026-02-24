// Created: 2025-12-28
import { useReadContract, useWriteContract, useAccount, useChainId, useConnectorClient } from 'wagmi';
import { CONTRACT_ADDRESSES, DEFAULT_CHAIN_ID } from '@/constants/addresses';
import KerneVaultABI from '@/abis/KerneVault.json';

export function useVault() {
  const { address, connector } = useAccount();
  const chainId = useChainId();
  const { data: client } = useConnectorClient();
  
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

  const deposit = async (amount: bigint) => {
    // Get ACTUAL current chain from connector (not cached React state)
    const actualChainId = client?.chain?.id || chainId;
    
    console.log('[useVault] Initiating deposit:', {
      amount: amount.toString(),
      receiver: address,
      vaultAddress: VAULT_ADDRESS,
      reactChainId: chainId,
      actualChainId,
    });
    
    // Critical: Verify wallet's ACTUAL chain matches Base
    if (actualChainId !== 8453) {
      console.error('[useVault] Chain mismatch detected!', {
        reactState: chainId,
        walletActual: actualChainId,
      });
      throw new Error(`Wallet is on wrong network. Please switch to Base in MetaMask. (Actual chain: ${actualChainId})`);
    }
    
    writeContract({
      address: VAULT_ADDRESS,
      abi: KerneVaultABI.abi,
      functionName: 'deposit',
      args: [amount, address],
      chainId: 8453, // Explicit Base chain ID
    });
  };

  const withdraw = async (assets: bigint) => {
    // Get ACTUAL current chain from connector (not cached React state)
    const actualChainId = client?.chain?.id || chainId;
    
    console.log('[useVault] Initiating withdrawal:', {
      assets: assets.toString(),
      receiver: address,
      owner: address,
      vaultAddress: VAULT_ADDRESS,
      reactChainId: chainId,
      actualChainId,
    });
    
    // Critical: Verify wallet's ACTUAL chain matches Base
    if (actualChainId !== 8453) {
      console.error('[useVault] Chain mismatch detected!', {
        reactState: chainId,
        walletActual: actualChainId,
      });
      throw new Error(`Wallet is on wrong network. Please switch to Base in MetaMask. (Actual chain: ${actualChainId})`);
    }
    
    writeContract({
      address: VAULT_ADDRESS,
      abi: KerneVaultABI.abi,
      functionName: 'withdraw',
      args: [assets, address, address],
      chainId: 8453, // Explicit Base chain ID
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
