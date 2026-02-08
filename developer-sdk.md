# Developer SDK: `@kerne/sdk`

Kerne provides a robust TypeScript SDK for developers and institutional partners to integrate with the protocol's liquidity and intent-solving engine.

## Installation

```bash
npm install @kerne/sdk
```

## Core Features

### 1. Vault Integration
Easily interact with any KerneVault to deposit, withdraw, or query analytics.

```typescript
import { KerneSDK, VaultTier } from '@kerne/sdk';

const sdk = new KerneSDK({ chainId: 8453 }); // Base
const vault = await sdk.getVault('0x...');

// Get analytics
const apy = await vault.getProjectedAPY();
const solvency = await vault.getSolvencyRatio();
```

### 2. `useSolver` Hook
For partners building intent-based interfaces, the SDK provides a React hook to interact with the **Zero-Fee Intent Network (ZIN)**.

```typescript
const { fulfillIntent, estimateSpread } = useSolver();

// Fulfill a CowSwap intent
const result = await fulfillIntent({
  tokenIn: '0x...',
  tokenOut: '0x...',
  amountOut: parseUnits('100', 6),
  user: userAddress
});
```

### 3. Private Bundle Submission
The SDK supports submitting transactions via private RPCs (like Flashbots) to protect against MEV front-running during large ZIN executions or arbitrage runs.

### 4. Institutional Compliance
For "Pro Mode" vaults, the SDK includes built-in helpers for `IComplianceHook` integration, allowing for automated KYC/AML verification before transaction submission.

---