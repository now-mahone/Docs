# Implementation Plan: Kerne LST Sentinel

## Stage 1: Contract Hardening (T-Minus 24h)
1.  **Update Interface**: Add `IAaveV3Pool` and `ICLRouter` (Aerodrome Slipstream) interfaces to `src/interfaces/`.
2.  **Modify `KerneFlashArbBot.sol`**:
    - Implement `AaveV3` callback logic.
    - Add `_executeSlipstreamSwap` internal function.
    - Add `executeLiquidation` function.
3.  **Testing**:
    - Run `forge test --match-path test/Sentinel.t.sol` on a Base mainnet fork.
    - Verify 100% profit distribution to Treasury.

## Stage 2: Discovery Engine Refinement (T-Minus 12h)
1.  **Configure `GraphArbScanner.py`**:
    - Add Aerodrome Slipstream pool addresses for `wstETH/WETH` and `cbETH/WETH`.
    - Set `minProfitThreshold` to $1.00 (targeting high-frequency small wins).
2.  **Environment Setup**:
    - Deploy to a low-latency VPS (e.g., AWS us-east-1 or equivalent Base node proximity).
    - Load wallet with $100 ETH for gas.

## Stage 3: Mainnet Launch (Zero Hour)
1.  **Deploy Executor**: `forge create KerneFlashArbBot --rpc-url $BASE_RPC --private-key $PRIVATE_KEY ...`
2.  **Verify & Grant Roles**:
    - Grant `EXECUTOR_ROLE` to the bot wallet.
    - Set `Treasury` to the Kerne Multisig.
3.  **Initiate Scanner**: Start `python bot/flash_arb_scanner.py`.
4.  **Monitor**: Track successful transactions on Basescan and Discord.

## Success Metrics
- **TVL Impact**: Visibility of Kerne on "Most Profitable Bots" lists.
- **Revenue**: $50+ net profit/day during volatile periods.
- **Ecosystem Health**: Reduction in LST de-peg duration on Base.
