// Created: 2026-01-14
// Mock utilities for viem client responses
import { vi } from 'vitest';

export const mockPublicClient = {
  readContract: vi.fn(),
  simulateContract: vi.fn(),
};

export const mockWalletClient = {
  account: {
    address: '0x1234567890123456789012345678901234567890' as `0x${string}`,
  },
  writeContract: vi.fn(),
};

export const mockContract = {
  read: {
    totalAssets: vi.fn(),
    totalSupply: vi.fn(),
    getProjectedAPY: vi.fn(),
    symbol: vi.fn(),
    getSolvencyRatio: vi.fn(),
    lastReportedTimestamp: vi.fn(),
    asset: vi.fn(),
  },
  write: {},
};

export function createMockPublicClient() {
  return mockPublicClient;
}

export function createMockWalletClient() {
  return mockWalletClient;
}

export function resetAllMocks() {
  mockPublicClient.readContract.mockReset();
  mockPublicClient.simulateContract.mockReset();
  mockWalletClient.writeContract.mockReset();
  Object.values(mockContract.read).forEach((fn) => fn.mockReset());
}

// Default mock responses for common scenarios
export const mockResponses = {
  tierConfig: [BigInt(100000000000000000), 10000n, true] as const, // 0.1 ETH fee, 100% maxHedge, enabled
  userVaults: [
    '0xVault1234567890123456789012345678901234' as `0x${string}`,
    '0xVault2234567890123456789012345678901234' as `0x${string}`,
  ],
  vaultData: {
    totalAssets: BigInt(1000000000000000000000), // 1000 tokens
    totalSupply: BigInt(1000000000000000000000), // 1000 shares
    projectedAPY: 850n, // 8.5%
    symbol: 'kUSDC',
  },
  solvencyRatio: 10500n, // 105%
  lastReportedTimestamp: BigInt(Math.floor(Date.now() / 1000) - 3600), // 1 hour ago
  allowance: BigInt(0),
  assetAddress: '0xAsset123456789012345678901234567890123' as `0x${string}`,
  txHash: '0xTx12345678901234567890123456789012345678901234567890123456789012' as `0x${string}`,
};
