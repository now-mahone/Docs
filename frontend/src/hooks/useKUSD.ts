// Created: 2025-12-29
import { useReadContract, useWriteContract, useAccount, useChainId } from 'wagmi';
import { CONTRACT_ADDRESSES, DEFAULT_CHAIN_ID } from '@/constants/addresses';
import kUSDABI from '@/abis/kUSD.json';
import kUSDMinterABI from '@/abis/kUSDMinter.json';

export function useKUSD() {
  const { address } = useAccount();
  const chainId = useChainId();

  const addresses = CONTRACT_ADDRESSES[chainId] || CONTRACT_ADDRESSES[DEFAULT_CHAIN_ID];
  const KUSD_ADDRESS = addresses.TOKEN;
  const KUSD_MINTER_ADDRESS = addresses.MINTER;

  // Read functions
  const { data: kusdBalance, refetch: refetchKUSDBalance } = useReadContract({
    address: KUSD_ADDRESS,
    abi: kUSDABI.abi,
    functionName: 'balanceOf',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && KUSD_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: position, refetch: refetchPosition } = useReadContract({
    address: KUSD_MINTER_ADDRESS,
    abi: kUSDMinterABI.abi,
    functionName: 'positions',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && KUSD_MINTER_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: klpPrice } = useReadContract({
    address: KUSD_MINTER_ADDRESS,
    abi: kUSDMinterABI.abi,
    functionName: 'getKLPPrice',
    query: {
      enabled: KUSD_MINTER_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: isHealthy } = useReadContract({
    address: KUSD_MINTER_ADDRESS,
    abi: kUSDMinterABI.abi,
    functionName: 'isHealthy',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && KUSD_MINTER_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  const { data: healthFactor } = useReadContract({
    address: KUSD_MINTER_ADDRESS,
    abi: kUSDMinterABI.abi,
    functionName: 'getHealthFactor',
    args: address ? [address] : undefined,
    query: {
      enabled: !!address && KUSD_MINTER_ADDRESS !== '0x0000000000000000000000000000000000000000',
    },
  });

  // Write functions
  const { writeContract, data: hash, isPending, isSuccess, error } = useWriteContract();

  const mint = (klpAmount: bigint, kusdAmount: bigint) => {
    writeContract({
      address: KUSD_MINTER_ADDRESS,
      abi: kUSDMinterABI.abi,
      functionName: 'mint',
      args: [klpAmount, kusdAmount],
    });
  };

  const burn = (kusdAmount: bigint, klpAmount: bigint) => {
    writeContract({
      address: KUSD_MINTER_ADDRESS,
      abi: kUSDMinterABI.abi,
      functionName: 'burn',
      args: [kusdAmount, klpAmount],
    });
  };

  const leverage = (wethAmount: bigint, kusdAmount: bigint) => {
    writeContract({
      address: KUSD_MINTER_ADDRESS,
      abi: kUSDMinterABI.abi,
      functionName: 'leverage',
      args: [wethAmount, kusdAmount],
    });
  };

  const fold = (amountToBorrow: bigint, minKLPOut: bigint) => {
    writeContract({
      address: KUSD_MINTER_ADDRESS,
      abi: kUSDMinterABI.abi,
      functionName: 'fold',
      args: [amountToBorrow, minKLPOut],
    });
  };

  return {
    kusdBalance: kusdBalance as bigint | undefined,
    collateralAmount: position ? (position as any)[0] as bigint : 0n,
    debtAmount: position ? (position as any)[1] as bigint : 0n,
    klpPrice: klpPrice as bigint | undefined,
    isHealthy: isHealthy as boolean | undefined,
    healthFactor: healthFactor as bigint | undefined,
    mint,
    burn,
    leverage,
    fold,
    isPending,
    isSuccess,
    hash,
    error,
    refetchKUSDBalance,
    refetchPosition,
  };
}
