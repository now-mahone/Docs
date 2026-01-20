# Zero-Fee Intent Network (ZIN) - Technical Specification

**Created:** 2026-01-17  
**Version:** 1.0.0  
**Status:** Draft

## Executive Summary

The Zero-Fee Intent Network (ZIN) transforms Kerne from a passive vault into the primary execution engine for high-volume trading on the Base network. By using Kerne's internal liquidity to fulfill intent-based trades (CowSwap, UniswapX), ZIN captures the spread that would otherwise go to external liquidity providers or Aave.

## Core Value Proposition

1. **Organic Awareness**: Every time Kerne fills a trade on Uniswap or Aerodrome, the user's transaction history shows "Filled by Kerne". This establishes Kerne as the de facto "market maker" for Base.
2. **Revenue Capture**: Spread profits that normally go to Aave or DEXs are captured by Kerne
3. **Zero-Fee Execution**: Users get instant, zero-fee fills while Kerne captures the arbitrage spread

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Intent Sources                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐    │
│  │ CowSwap  │  │UniswapX  │  │  1inch   │    │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘    │
│       │                │                │            │
│       └────────────────┴────────────────┘            │
│                    │                                   │
│                    ▼                                   │
│          ┌───────────────────────┐                   │
│          │   ZIN Solver Bot    │                   │
│          │   (Python)          │                   │
│          └───────────┬───────────┘                   │
│                      │                               │
┌─────────────────────┼───────────────────────────────────────┐
│                      │                               │    │
│                      ▼                               │    │
│          ┌───────────────────────────────┐             │    │
│          │  KerneIntentExecutorV2      │             │    │
│          │  (Solidity)                 │             │    │
│          └───────────┬───────────────────┘             │    │
│                      │                               │    │
│        ┌─────────────┴─────────────┐               │    │
│        │                           │               │    │
│        ▼                           ▼               │    │
│  ┌─────────┐               ┌──────────────┐    │    │
│  │  Vault   │               │  ZIN Pool   │    │    │
│  │ (USDC)  │               │  (Liquidity  │    │    │
│  └─────────┘               │  Aggregator) │    │    │
│  ┌─────────┐               └──────────────┘    │    │
│  │  Vault   │               ┌──────────────┐    │    │
│  │ (WETH)  │               │  PSM / Other │    │    │
│  └─────────┘               │  Liquidity   │    │    │
│                            └──────────────┘    │    │
│                                            │    │
└────────────────────────────────────────────────────┘    │
                                                     │
└─────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. KerneIntentExecutorV2 (Solidity)

**File:** `src/KerneIntentExecutorV2.sol`

**Purpose:** Core intent fulfillment engine that uses flash loans from internal liquidity.

**Key Features:**
- Zero-fee flash loans from KerneVault/KUSDPSM
- Automatic spread capture and profit routing
- Sentinel V2 safety checks (latency, price deviation)
- Support for 1inch, Uniswap, and Aerodrome aggregators

**Core Functions:**

```solidity
function fulfillIntent(
    address lender,           // KerneVault or KUSDPSM
    address tokenIn,
    address tokenOut,
    uint256 amount,
    address user,
    bytes calldata aggregatorData,
    bytes calldata safetyParams
) external onlyRole(SOLVER_ROLE);
```

**Profit Flow:**
1. Flash loan `amount` of `tokenOut` from vault
2. Send `tokenOut` to user (fulfill intent)
3. Execute aggregator trade to swap `tokenIn` to `tokenOut`
4. Calculate spread: `balanceAfter - (amount + fee)`
5. If spread > 0: auto-harvest to profit vault
6. Repay flash loan

**Metrics Tracked:**
- `totalSpreadCaptured`: Lifetime spread captured
- `totalIntentsFulfilled`: Total intents processed
- `tokenSpreadCaptured[token]`: Per-token spread capture

### 2. KerneZINPool (Solidity)

**File:** `src/KerneZINPool.sol`

**Purpose:** Liquidity aggregation pool for multi-source intent fulfillment.

**Key Features:**
- Support multiple liquidity sources (vaults, PSM, external)
- Priority-based liquidity routing
- Per-token fee configuration
- Automatic profit routing

**Core Functions:**

```solidity
function addLiquiditySource(
    address token,
    address source,
    uint256 priority
) external onlyRole(MANAGER_ROLE);

function fillIntentInternal(
    address tokenIn,
    address tokenOut,
    uint256 amount,
    address user
) external onlyRole(SOLVER_ROLE) returns (uint256 profit);
```

### 3. ZIN Solver Bot (Python)

**File:** `bot/solver/zin_solver.py`

**Purpose:** Monitors intent protocols and fulfills profitable trades.

**Key Responsibilities:**
1. Listen to CowSwap/UniswapX order events
2. Parse incoming intents
3. Check profitability using 1inch API
4. Fulfill profitable intents via KerneIntentExecutorV2
5. Track performance metrics

**Configuration:**
```bash
BASE_RPC_URL=https://mainnet.base.org
PRIVATE_KEY=<your_private_key>
ZIN_EXECUTOR_ADDRESS=<deployed_executor>
PROFIT_VAULT_ADDRESS=<vault_address>
ONE_INCH_API_KEY=<1inch_api_key>
```

**Key Methods:**

```python
async def get_aggregator_quote(
    token_in: str,
    token_out: str,
    amount: int,
    aggregator: str = "1inch"
) -> Tuple[bytes, int]

async def fulfill_intent(
    intent: IntentData,
    vault_address: str,
    aggregator_calldata: bytes,
    expected_profit_bps: int
) -> Optional[str]

def calculate_profit_potential(
    intent_amount: int,
    market_price: int,
    our_price: int
) -> Tuple[int, int]
```

### 4. KerneVault Integration

**File:** `src/KerneVault.sol`

**ZIN-Specific Additions:**
- `zinExecutor` address variable
- `setZINExecutor()` function
- Zero-fee flash loans for ZIN executor

**Modified Functions:**

```solidity
function flashFee(address token, uint256 amount) public view override returns (uint256) {
    require(token == asset(), "Unsupported token");
    
    // Zero-fee for ZIN executor
    if (msg.sender == zinExecutor) {
        return 0;
    }
    
    // ... rest of function
}
```

## Profit Calculation

### Example Scenario

**User Intent:** Swap 1 WETH for 2000 USDC  
**Market Price:** 1 WETH = 2000 USDC (via 1inch)  
**Our Price:** 1 WETH = 2015 USDC (via vault liquidity)  

**Flow:**

1. Flash loan 2000 USDC from vault (0 fee)
2. Send 2000 USDC to user
3. User sends 1 WETH to executor
4. Swap 1 WETH for 2015 USDC via 1inch
5. Repay 2000 USDC flash loan
6. **Profit:** 15 USDC (0.75% spread)

**Profit Distribution:**
- Auto-harvested to profit vault
- Compounds in vault yield
- Available for withdrawal by KUSD holders

## Security Considerations

### 1. Sentinel V2 Circuit Breakers

**Latency Check:**
- Max latency: 500ms (configurable)
- Rejects intents older than `block.timestamp - maxLatency`

**Price Deviation Check:**
- Max deviation: 1% (100 bps)
- Prevents sandwich attacks and oracle manipulation

### 2. Access Control

**Roles:**
- `SOLVER_ROLE`: Can fulfill intents
- `SENTINEL_ROLE`: Can update safety parameters
- `DEFAULT_ADMIN_ROLE`: Full control

### 3. Reentrancy Protection

All external functions use `nonReentrant` modifier to prevent reentrancy attacks.

## Deployment Steps

### 1. Deploy ZIN System

```bash
forge script script/DeployZIN.s.sol:DeployZIN \
  --rpc-url $BASE_RPC_URL \
  --broadcast \
  -vvvv
```

### 2. Configure Vaults

For each KerneVault:

```solidity
vault.setZINExecutor(zinExecutorAddress);
```

### 3. Add Liquidity Sources

```solidity
zinPool.addLiquiditySource(
    USDC_ADDRESS,
    usdcVaultAddress,
    1  // priority (lower = higher priority)
);
```

### 4. Grant Solver Role

```solidity
zinExecutor.grantRole(
    zinExecutor.SOLVER_ROLE(),
    solverBotAddress
);
```

### 5. Start Solver Bot

```bash
cd bot
python solver/zin_solver.py
```

## Monitoring & Analytics

### Contract Metrics

```solidity
var (totalSpread, totalIntents, profitVault) = zinExecutor.getZINMetrics();
```

### Bot Metrics

Located in `bot/solver/zin_profit_log.csv`:

```csv
timestamp,token_in,token_out,amount_out,profit_bps,gas_used,tx_hash
```

### Key Performance Indicators (KPIs)

1. **Total Spread Captured**: Lifetime profit (USD equivalent)
2. **Intents Fulfilled**: Total number of successful executions
3. **Average Profit per Intent**: `totalSpread / totalIntents`
4. **Success Rate**: `successful / (successful + failed)`
5. **Gas Efficiency**: Average gas per transaction

## Optimization Opportunities

### 1. MEV Protection

- Implement priority fee bidding
- Use Flashbots-style private mempool
- Front-running detection

### 2. Liquidity Management

- Dynamic liquidity allocation based on demand
- Cross-vault arbitrage opportunities
- External liquidity integration (Aave, Compound)

### 3. Intent Source Expansion

- Direct integration with CowSwap API
- UniswapX order book monitoring
- CoWSwap limit order support
- Perpetual protocol integration

## Risk Mitigation

### 1. Price Oracle Manipulation

- Multi-source price validation (1inch + Uniswap + Aerodrome)
- Deviation thresholds
- Time-weighted average prices

### 2. Flash Loan Risks

- Max flash loan amount limits
- Per-user rate limiting
- Circuit breaker on suspicious activity

### 3. Smart Contract Risks

- Comprehensive testing (unit, integration, fuzzing)
- Third-party audits
- Bug bounty program

## Future Enhancements

### Phase 2 (Q2 2026)

1. **Cross-Chain Intents**: Support for intent fulfillment across chains
2. **Limit Order Book**: Accept limit orders directly
3. **Yield Source Integration**: Use ZIN profits for yield generation

### Phase 3 (Q3 2026)

1. **AI-Powered Pricing**: ML models for optimal pricing
2. **Predictive Liquidity**: Anticipate demand for efficient capital allocation
3. **Social Trading**: Allow users to follow successful ZIN strategies

## Appendix A: Aggregator Integration

### 1inch

**API Endpoint:** `https://api.1inch.dev/swap/v6.0/8453/swap`

**Required Params:**
- `src`: Input token address
- `dst`: Output token address
- `amount`: Amount (wei)
- `from`: Executor address
- `slippage`: Maximum slippage (e.g., "0.5")

### Uniswap V3

**Contract:** `0xE592427A0AEce92De3Edee1F18E0157C05861564`

**Function:** `exactInputSingleOutput`

### Aerodrome

**Contract:** `0xcF77a3Ba9A5CA399B7c97c478569a74DD55C726f`

**Router:** Similar to Uniswap V3 interface

## Appendix B: Gas Optimization

### Target Gas Costs

- `fulfillIntent`: ~250,000 gas
- Flash loan + repay: ~50,000 gas
- Aggregator swap: ~100,000 gas
- **Total**: ~400,000 gas per intent

### Optimization Strategies

1. Use assembly for critical loops
2. Batch multiple intents in single transaction
3. Optimize storage access patterns
4. Use `call` instead of `delegatecall` where possible

## Appendix C: Example Transactions

### Successful Intent Fulfillment

**Input:**
- TokenIn: WETH (0x4200000000000000000000000000000000000000000006)
- TokenOut: USDC (0x833589fCD6eDb6E08f4c7C32D4f71b54bDA02913)
- Amount: 2,000,000,000 (2000 USDC, 6 decimals)
- User: 0xUserAddress...

**Output:**
- Status: Success
- Gas Used: 385,421
- Profit Captured: 15 USDC (0.75% spread)
- TX Hash: 0x...

---

**Document Owner:** Kerne Protocol  
**Last Updated:** 2026-01-17  
**Next Review:** Post-deployment
