# Plan: Dynamic Hedge Rebalancing Engine (V2)

## Phase 1: Infrastructure & Event Logic
- [ ] Implement `VaultEventListener` using `web3.py` WebSockets to monitor `KerneVault` events.
- [ ] Implement an internal `RebalanceQueue` to handle concurrent events and deduplicate triggers.
- [ ] Update `HedgingEngine.__init__` to support asynchronous execution.

## Phase 2: Advanced Execution & Routing
- [ ] Enhance `ExchangeManager` with `get_order_book(symbol)` for all active exchanges.
- [ ] Implement `SmartRouter` class to calculate optimal order distribution based on:
    - Current liquidity (depth)
    - Real-time funding rates
    - Existing position concentration
- [ ] Implement `execute_twap_order` for large rebalances (> 1% TVL).

## Phase 3: Risk & Hysteresis
- [ ] Replace `THRESHOLD_ETH` with `calculate_dynamic_threshold()` (TVL and Volatility-based).
- [ ] Implement `MarginMonitor` to alert or auto-transfer funds between exchanges if margin ratios drop.
- [ ] Add "Circuit Breaker" to the bot: Stop trading if market price deviates > 5% from oracle price.

## Phase 4: Monitoring & Reporting
- [ ] Integrate `metrics.py` with the rebalancing loop to track "Hedge Drift" (Target vs Actual).
- [ ] Add automated logging of "Slippage vs Expected" for every rebalance.
- [ ] Update `YieldServer` adapters to consume the new rebalancer telemetry.

## Phase 5: Verification & Stress Testing
- [ ] Write integration tests in `bot/tests/test_dynamic_rebalancer.py` using Anvil fork.
- [ ] Perform a "Chaos Test": Simulate exchange disconnects during a 100 ETH deposit cycle.
- [ ] Verify `KerneVault` off-chain asset reporting matches the new aggregate equity calculations.
