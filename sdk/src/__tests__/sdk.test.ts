// Created: 2026-01-14
// SDK Test Suite - Comprehensive tests for institutional partner distribution
import { describe, it, expect, vi } from 'vitest';

// Type definitions
type Address = `0x${string}`;

// Mock data
const mockFactoryAddress = '0xFactory1234567890123456789012345678901234' as Address;
const mockRpcUrl = 'https://mainnet.base.org';
const mockVaultAddress = '0xVault1234567890123456789012345678901234' as Address;

// Setup mocks at module level
vi.mock('viem', () => ({
  createPublicClient: vi.fn(() => ({
    readContract: vi.fn(),
    simulateContract: vi.fn(),
  })),
  createWalletClient: vi.fn(),
  getContract: vi.fn(() => ({
    read: {
      totalAssets: vi.fn().mockResolvedValue(BigInt(1000000000000000000000)),
      totalSupply: vi.fn().mockResolvedValue(BigInt(1000000000000000000000)),
      getProjectedAPY: vi.fn().mockResolvedValue(850n),
      symbol: vi.fn().mockResolvedValue('kUSDC'),
      getSolvencyRatio: vi.fn().mockResolvedValue(10500n),
      lastReportedTimestamp: vi.fn().mockResolvedValue(BigInt(Math.floor(Date.now() / 1000) - 3600)),
      asset: vi.fn().mockResolvedValue('0xAsset123456789012345678901234567890123'),
    },
  })),
  http: vi.fn(),
}));

vi.mock('viem/chains', () => ({
  base: { id: 8453, name: 'Base' },
}));

vi.mock('wagmi', () => ({
  useContractRead: vi.fn(() => ({ data: undefined, isLoading: false, error: null })),
  useContractWrite: vi.fn(() => ({ writeAsync: vi.fn(), isLoading: false, error: null })),
  useAccount: vi.fn(() => ({ address: '0x1234567890123456789012345678901234567890' })),
}));

describe('KerneSDK Core', () => {
  it('exports VaultTier BASIC = 0', async () => {
    const { VaultTier } = await import('../index.js');
    expect(VaultTier.BASIC).toBe(0);
  });

  it('exports VaultTier PRO = 1', async () => {
    const { VaultTier } = await import('../index.js');
    expect(VaultTier.PRO).toBe(1);
  });

  it('exports VaultTier INSTITUTIONAL = 2', async () => {
    const { VaultTier } = await import('../index.js');
    expect(VaultTier.INSTITUTIONAL).toBe(2);
  });

  it('creates SDK with factoryAddress', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    expect(sdk.factoryAddress).toBe(mockFactoryAddress);
  });

  it('creates SDK with publicClient', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    expect(sdk.publicClient).toBeDefined();
  });

  it('SDK has undefined walletClient by default', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    expect(sdk.walletClient).toBeUndefined();
  });

  it('SDK accepts optional walletClient', async () => {
    const { KerneSDK } = await import('../index.js');
    const mockWallet = { account: { address: mockFactoryAddress } } as any;
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl, mockWallet);
    expect(sdk.walletClient).toBe(mockWallet);
  });
});

describe('Wallet Required Operations', () => {
  it('deployVault throws without wallet', async () => {
    const { KerneSDK, VaultTier } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    await expect(sdk.deployVault({
      asset: '0xAsset123456789012345678901234567890123' as Address,
      name: 'Test', symbol: 'TEST',
      admin: '0xAdmin123456789012345678901234567890123' as Address,
      performanceFeeBps: 1000, whitelistEnabled: false,
      maxTotalAssets: BigInt(1000000), tier: VaultTier.PRO,
    })).rejects.toThrow('Wallet client required');
  });

  it('setComplianceHook throws without wallet', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    await expect(sdk.setComplianceHook(mockVaultAddress, '0xHook12345678901234567890123456789012345' as Address)).rejects.toThrow('Wallet client required');
  });

  it('setWhitelisted throws without wallet', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    await expect(sdk.setWhitelisted(mockVaultAddress, '0xUser12345678901234567890123456789012345' as Address, true)).rejects.toThrow('Wallet client required');
  });

  it('deposit throws without wallet', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    await expect(sdk.deposit(mockVaultAddress, BigInt(1000), '0xReceiver23456789012345678901234567890' as Address)).rejects.toThrow('Wallet client required');
  });
});

describe('Vault Analytics', () => {
  it('getVaultAnalytics returns totalAssets', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics).toHaveProperty('totalAssets');
  });

  it('getVaultAnalytics returns solvencyRatio', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics).toHaveProperty('solvencyRatio');
  });

  it('getVaultAnalytics returns isHealthy', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics).toHaveProperty('isHealthy');
  });

  it('solvencyRatio is percentage (105)', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics.solvencyRatio).toBe(105);
  });

  it('vault is healthy when solvency >= 100%', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics.isHealthy).toBe(true);
  });

  it('lastReported is Date', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics.lastReported).toBeInstanceOf(Date);
  });
});

describe('Vault Data', () => {
  it('getVaultData returns totalAssets', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const data = await sdk.getVaultData(mockVaultAddress);
    expect(data).toHaveProperty('totalAssets');
  });

  it('getVaultData returns symbol', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const data = await sdk.getVaultData(mockVaultAddress);
    expect(typeof data.symbol).toBe('string');
  });
});

describe('useSolver Hook', () => {
  it('returns fulfillIntent function', async () => {
    const { useSolver } = await import('../hooks/useSolver.js');
    const result = useSolver('0xExec1234567890123456789012345678901234' as Address);
    expect(result.fulfillIntent).toBeDefined();
  });

  it('returns user address', async () => {
    const { useSolver } = await import('../hooks/useSolver.js');
    const result = useSolver('0xExec1234567890123456789012345678901234' as Address);
    expect(result.address).toBe('0x1234567890123456789012345678901234567890');
  });
});

describe('Deposit Flow', () => {
  it('SDK with wallet has walletClient defined', async () => {
    const { KerneSDK } = await import('../index.js');
    const mockWallet = { account: { address: '0x1234567890123456789012345678901234567890' }, writeContract: vi.fn() } as any;
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl, mockWallet);
    expect(sdk.walletClient).toBeDefined();
  });

  it('handles BigInt amounts', () => {
    expect(BigInt(0)).toBe(0n);
    expect(BigInt('1000000000000000000000000')).toBeGreaterThan(0n);
  });
});

describe('Institutional Compliance', () => {
  it('meets requirements (healthy + 100%+ solvency)', async () => {
    const { KerneSDK } = await import('../index.js');
    const sdk = new KerneSDK(mockFactoryAddress, mockRpcUrl);
    const analytics = await sdk.getVaultAnalytics(mockVaultAddress);
    expect(analytics.isHealthy && analytics.solvencyRatio >= 100).toBe(true);
  });
});
