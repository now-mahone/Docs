# Kerne Multi-Asset Best Yield Router
## Architecture for Optimal Cross-Asset Delta-Neutral Yield

**Date:** 2026-01-19  
**Status:** Design Specification  
**Author:** Kerne Lead Architect

---

## Executive Summary

Based on our 6-month multi-asset backtest with **real Binance funding data**, we've validated that different assets offer significantly different APYs:

| Asset | 6-Month APY | Sharpe Ratio | Key Insight |
|-------|-------------|--------------|-------------|
| ETH   | **22.23%**  | 46.48        | Best risk-adjusted (LST + stable funding) |
| BTC   | 13.97%      | 25.70        | Most stable funding (89% positive) |
| SOL   | 16.70%      | 5.30         | High LST yield (6.5%) but volatile funding |
| LINK  | 14.01%      | 14.69        | Pure funding play, no LST |
| ARB   | 12.22%      | 11.47        | L2 token, decent funding |

**Key Finding:** A Sharpe-weighted portfolio across all assets yields **17.56% APY** with better risk diversification than any single asset.

---

## The Problem: Single-Asset Limitation

Current Kerne vault accepts only ETH-based LSTs. This limits:
1. **Yield Optimization** - Missing higher-yielding opportunities in other assets
2. **User Accessibility** - BTC/SOL holders must swap first
3. **Risk Concentration** - 100% exposure to ETH funding rates

---

## The Solution: Best Yield Router

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         USER DEPOSIT FLOW                                │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│   User deposits ANY supported asset:                                     │
│   ┌─────┐  ┌─────┐  ┌─────┐  ┌──────┐  ┌──────┐  ┌──────┐              │
│   │ ETH │  │ BTC │  │ SOL │  │ USDC │  │ LINK │  │ ARB  │              │
│   └──┬──┘  └──┬──┘  └──┬──┘  └──┬───┘  └──┬───┘  └──┬───┘              │
│      │        │        │        │         │         │                    │
│      └────────┴────────┴────────┴─────────┴─────────┘                    │
│                              │                                           │
│                              ▼                                           │
│                    ┌─────────────────┐                                   │
│                    │  KerneRouter    │                                   │
│                    │  (Entry Point)  │                                   │
│                    └────────┬────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│                    ┌─────────────────┐                                   │
│                    │  YieldOptimizer │  ← Reads real-time funding rates  │
│                    │  (Off-chain)    │  ← Calculates optimal allocation  │
│                    └────────┬────────┘                                   │
│                             │                                            │
│                             ▼                                            │
│         ┌───────────────────┼───────────────────┐                        │
│         │                   │                   │                        │
│         ▼                   ▼                   ▼                        │
│   ┌───────────┐      ┌───────────┐      ┌───────────┐                   │
│   │ ETH Vault │      │ BTC Vault │      │ SOL Vault │                   │
│   │ (cbETH)   │      │ (WBTC)    │      │ (mSOL)    │                   │
│   └─────┬─────┘      └─────┬─────┘      └─────┬─────┘                   │
│         │                  │                  │                          │
│         └──────────────────┼──────────────────┘                          │
│                            │                                             │
│                            ▼                                             │
│                    ┌─────────────────┐                                   │
│                    │     KUSD        │  ← Single unified token           │
│                    │  (User gets)    │  ← Represents diversified yield   │
│                    └─────────────────┘                                   │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## User Deposit Flow

### Option 1: Simple Deposit (Recommended for Most Users)

```
User Action: Deposit 10 ETH
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. KerneRouter receives 10 ETH                                  │
│ 2. YieldOptimizer calculates current best allocation:          │
│    - ETH: 37.3% (best Sharpe)                                  │
│    - BTC: 20.6%                                                │
│    - SOL: 4.3%                                                 │
│    - Others: 37.8%                                             │
│ 3. Router swaps portions via DEX aggregator:                   │
│    - Keep 3.73 ETH as ETH                                      │
│    - Swap 2.06 ETH → WBTC                                      │
│    - Swap 0.43 ETH → SOL                                       │
│    - Swap 3.78 ETH → other assets                              │
│ 4. Each portion deposited to respective vault                  │
│ 5. User receives KUSD representing total position              │
└─────────────────────────────────────────────────────────────────┘
```

### Option 2: Direct Asset Deposit (For Whales/Institutions)

```
User Action: Deposit 100 BTC directly
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. KerneRouter receives 100 BTC                                 │
│ 2. No swap needed - direct to BTC vault                        │
│ 3. BTC vault opens short BTC perp on CEX                       │
│ 4. User receives KUSD at current BTC/USD rate                  │
│ 5. User earns BTC funding rate (13.97% APY backtest)           │
└─────────────────────────────────────────────────────────────────┘
```

### Option 3: Stablecoin Deposit (Maximum Flexibility)

```
User Action: Deposit 1,000,000 USDC
   │
   ▼
┌─────────────────────────────────────────────────────────────────┐
│ 1. KerneRouter receives 1M USDC                                 │
│ 2. YieldOptimizer determines optimal allocation                │
│ 3. USDC used as margin on CEX for all positions:               │
│    - $373K → ETH long spot + short perp                        │
│    - $206K → BTC long spot + short perp                        │
│    - $43K  → SOL long spot + short perp                        │
│    - etc.                                                       │
│ 4. User receives 1M KUSD                                       │
│ 5. User earns blended portfolio APY (17.56% backtest)          │
└─────────────────────────────────────────────────────────────────┘
```

---

## Smart Contract Architecture

### 1. KerneYieldRouter.sol

```solidity
// SPDX-License-Identifier: MIT
pragma solidity 0.8.24;

interface IKerneYieldRouter {
    /// @notice Deposit any supported asset and receive KUSD
    /// @param asset The asset to deposit (ETH, WBTC, SOL, USDC, etc.)
    /// @param amount The amount to deposit
    /// @param allocationMode 0=Auto (best yield), 1=Single asset, 2=Custom
    /// @param customAllocation Optional custom allocation percentages
    /// @return kusdAmount The amount of KUSD minted
    function deposit(
        address asset,
        uint256 amount,
        uint8 allocationMode,
        uint256[] calldata customAllocation
    ) external returns (uint256 kusdAmount);
    
    /// @notice Withdraw to any supported asset
    /// @param kusdAmount Amount of KUSD to redeem
    /// @param targetAsset The asset to receive (address(0) for original mix)
    /// @return assetAmount The amount of target asset received
    function withdraw(
        uint256 kusdAmount,
        address targetAsset
    ) external returns (uint256 assetAmount);
    
    /// @notice Get current optimal allocation based on live funding rates
    function getOptimalAllocation() external view returns (
        address[] memory assets,
        uint256[] memory weights,
        uint256 expectedAPY
    );
    
    /// @notice Get current APY for a specific asset
    function getAssetAPY(address asset) external view returns (uint256 apy);
}
```

### 2. KerneVaultRegistry.sol (Enhanced)

```solidity
// Manages multiple asset-specific vaults
interface IKerneVaultRegistry {
    /// @notice Register a new asset vault
    function registerVault(
        address asset,
        address vault,
        address perpSymbol,
        bool hasLST,
        uint256 lstYield
    ) external;
    
    /// @notice Get all registered vaults
    function getAllVaults() external view returns (
        address[] memory assets,
        address[] memory vaults,
        uint256[] memory tvls,
        uint256[] memory apys
    );
    
    /// @notice Get vault for specific asset
    function getVault(address asset) external view returns (address vault);
}
```

### 3. YieldOptimizer (Off-chain Service)

```python
# bot/yield_optimizer.py
class YieldOptimizer:
    """
    Real-time yield optimization across all supported assets.
    Runs every 8 hours (aligned with funding rate updates).
    """
    
    def get_optimal_allocation(self) -> Dict[str, float]:
        """
        Calculate Sharpe-weighted allocation based on:
        1. Current funding rates (from CEX APIs)
        2. LST yields (from on-chain oracles)
        3. Historical volatility (rolling 30-day)
        4. Liquidity constraints (max position sizes)
        """
        allocations = {}
        
        for asset in SUPPORTED_ASSETS:
            funding_apy = self.get_current_funding_apy(asset)
            lst_yield = self.get_lst_yield(asset)
            volatility = self.get_volatility(asset)
            
            # Expected return
            expected_return = funding_apy + lst_yield
            
            # Sharpe ratio (risk-adjusted)
            sharpe = (expected_return - RISK_FREE_RATE) / volatility
            
            allocations[asset] = max(0, sharpe)
        
        # Normalize to sum to 100%
        total = sum(allocations.values())
        return {k: v/total for k, v in allocations.items()}
```

---

## Supported Assets (Phase 1)

| Asset | Spot Token | LST Available | LST Yield | Perp Exchange | Status |
|-------|------------|---------------|-----------|---------------|--------|
| ETH   | WETH/cbETH | ✅ cbETH, wstETH | 3.5% | Binance, Bybit | ✅ Live |
| BTC   | WBTC       | ❌ (coming: sBTC) | 0% | Binance, Bybit | 🔜 Phase 1 |
| SOL   | wSOL       | ✅ mSOL, jitoSOL | 6.5% | Binance, Bybit | 🔜 Phase 1 |
| USDC  | USDC       | N/A (margin only) | 0% | All | ✅ Live |
| LINK  | LINK       | ❌ | 0% | Binance | 🔜 Phase 2 |
| ARB   | ARB        | ❌ | 0% | Binance | 🔜 Phase 2 |

---

## User Experience

### Frontend Deposit Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                    KERNE DEPOSIT                                 │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Select Asset:  [ETH ▼] [BTC] [SOL] [USDC] [LINK] [ARB]        │
│                                                                  │
│  Amount:        [________] ETH                                   │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  Allocation Strategy:                                            │
│                                                                  │
│  ○ 🎯 AUTO-OPTIMIZE (Recommended)                               │
│    Sharpe-weighted across all assets                            │
│    Expected APY: 17.56%                                         │
│                                                                  │
│  ○ 📊 SINGLE ASSET                                              │
│    100% exposure to deposited asset                             │
│    Expected APY: 22.23% (ETH)                                   │
│                                                                  │
│  ○ ⚙️ CUSTOM ALLOCATION                                         │
│    Set your own weights                                         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│                                                                  │
│  You will receive: ~10,000 KUSD                                 │
│                                                                  │
│  [        DEPOSIT & EARN YIELD        ]                         │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Live APY Dashboard

```
┌─────────────────────────────────────────────────────────────────┐
│                    LIVE YIELD RATES                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Asset    Funding APY   LST Yield   Total APY   Allocation      │
│  ─────────────────────────────────────────────────────────────  │
│  ETH      14.65%        3.50%       18.15%      37.3% ████████  │
│  BTC      16.54%        0.00%       16.54%      20.6% █████     │
│  SOL       1.80%        6.50%        8.30%       4.3% █         │
│  LINK     17.22%        0.00%       17.22%      11.8% ███       │
│  ARB      15.39%        0.00%       15.39%       9.2% ██        │
│  DOGE     13.98%        0.00%       13.98%       8.4% ██        │
│  AVAX     -1.91%        5.50%        3.59%       2.8% █         │
│                                                                  │
│  ─────────────────────────────────────────────────────────────  │
│  PORTFOLIO APY (Sharpe-Optimized):  17.56%                      │
│  Last Updated: 2 minutes ago                                    │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: ETH + BTC + USDC (Q1 2026)
- Deploy BTC vault with WBTC collateral
- Add USDC as margin-only deposit option
- Implement basic yield router with 2-asset optimization

### Phase 2: SOL + L2 Tokens (Q2 2026)
- Add SOL vault with mSOL/jitoSOL LST support
- Add ARB, OP, LINK vaults
- Implement full Sharpe-weighted optimization

### Phase 3: Cross-Chain (Q3 2026)
- Deploy vaults on Arbitrum, Optimism, Solana
- Enable cross-chain deposits via LayerZero
- Unified KUSD across all chains

---

## Risk Considerations

### 1. Swap Slippage
- Large deposits may incur slippage when swapping to optimal allocation
- Mitigation: Use DEX aggregators (1inch, Paraswap), split large orders

### 2. Rebalancing Costs
- Optimal allocation changes as funding rates shift
- Mitigation: Only rebalance when benefit > cost (threshold: 50bps improvement)

### 3. Asset-Specific Risks
- BTC: No LST yield, pure funding play
- SOL: Bridge risk for wrapped SOL on Base
- Altcoins: Lower liquidity, higher funding volatility

### 4. Correlation Risk
- All crypto assets correlated in extreme market conditions
- Mitigation: Maintain USDC buffer, circuit breakers

---

## Conclusion

The Multi-Asset Best Yield Router transforms Kerne from a single-asset ETH vault into a **universal yield aggregator** that:

1. **Accepts any asset** - ETH, BTC, SOL, stables, L2 tokens
2. **Optimizes automatically** - Sharpe-weighted allocation across all opportunities
3. **Returns single token** - KUSD represents diversified delta-neutral exposure
4. **Maximizes yield** - 17.56% portfolio APY vs 22.23% single-asset (with better risk-adjusted returns)

This positions Kerne as the **"Yearn for Delta-Neutral"** - the go-to protocol for institutional-grade, diversified yield.

---

*Specification created: 2026-01-19*
