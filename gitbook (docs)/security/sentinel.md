# Sentinel V2

**Sentinel V2** is Kerne's autonomous risk management layer, responsible for protecting protocol capital from market volatility and technical failures.

## Features

### 1. Real Time VaR Monitoring
Sentinel performs continuous Value at Risk (VaR) analysis on the protocol's CEX positions, ensuring that the Insurance Fund always has sufficient margin to cover potential drawdowns.

### 2. Depeg Protection
The system monitors the price ratio between LSTs (e.g., stETH) and ETH. If the ratio deviates beyond a strict threshold (e.g., 2%), Sentinel can trigger an emergency deleverage or pause the PSM to protect the peg of kUSD.

### 3. Circuit Breakers
Sentinel has the authority to pause protocol operations if it detects abnormal onchain activity or CEX API instability. This "Guardian" role is hardcoded into the core smart contracts to ensure subsecond response times.

### 4. Smart Contract Hardening
The `KerneIntentExecutor` and `KerneZINPool` contracts include Sentinel enforced limits on intent sizes, gas costs, and stale price data, preventing "fat finger" errors or malicious intent fulfillment.