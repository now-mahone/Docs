# Kerne "Hedge Fund in a Box" White-Label SDK

The Kerne White-Label SDK allows partners to launch and manage their own delta-neutral hedge funds on Base with minimal effort.

## Installation

```bash
npm install @kerne-protocol/sdk
```

## Quick Start

### 1. Initialize the SDK

```typescript
import { KerneSDK } from '@kerne-protocol/sdk';
import { createWalletClient, http, custom } from 'viem';
import { base } from 'viem/chains';

const walletClient = createWalletClient({
  chain: base,
  transport: custom(window.ethereum)
});

const sdk = new KerneSDK(
  '0xFACTORY_ADDRESS',
  'https://mainnet.base.org',
  walletClient
);
```

### 2. Deploy a Permissionless Vault

Anyone can deploy a vault by paying the deployment fee (default 0.05 ETH).

```typescript
const hash = await sdk.deployVault({
  asset: '0xUSDC_ADDRESS',
  name: 'My Branded Fund',
  symbol: 'MBF',
  admin: '0xYOUR_ADDRESS',
  founder: '0xKERNE_TREASURY', // For protocol fee capture
  founderFeeBps: 500,          // 5% of gross yield
  performanceFeeBps: 1500,     // 15% performance fee
  whitelistEnabled: false,
  maxTotalAssets: 0n           // Unlimited
});
```

### 3. Fetch Vault Data

```typescript
const data = await sdk.getVaultData('0xVAULT_ADDRESS');
console.log(`APY: ${data.projectedAPY / 100}%`);
console.log(`Total Assets: ${data.totalAssets}`);
```

### 4. Deposit into a Vault

```typescript
const depositHash = await sdk.deposit(
  '0xVAULT_ADDRESS',
  1000000n, // 1 USDC (6 decimals)
  '0xRECEIVER_ADDRESS'
);
```

## Permissionless Factory

The `KerneVaultFactory` is now permissionless. 

- **Deployment Fee:** 0.05 ETH (adjustable by Kerne governance).
- **Standardized Fees:** All white-label vaults contribute a portion of their yield to the Kerne Protocol.
- **Bespoke Configuration:** Partners control their own fees, whitelisting, and caps.
