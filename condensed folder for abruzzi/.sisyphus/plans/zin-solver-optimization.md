# Plan: ZIN Solver Optimization: Multi-Venue Intent Capture

This plan outlines the steps to upgrade the Kerne ZIN Solver to monitor and fulfill intents across a broader range of venues, including 1inch Fusion, LI.FI, and Aori, leveraging Kerne's delta-neutral hedging edge.

## 1. ARCHITECTURE REFACTORING
- [ ] Refactor `bot/solver/zin_solver.py` to use a plugin-based architecture for intent venues.
- [ ] Define a standard `BaseIntentFetcher` interface to simplify adding new venues.
- [ ] Update `IntentVenue` enum to include `FUSION`, `LIFI`, and `AORI`.

## 2. 1INCH FUSION INTEGRATION
- [ ] Implement `FusionIntentFetcher` in `bot/solver/zin_solver.py`.
- [ ] Integrate with 1inch Orderbook API to fetch Fusion orders on Base and Arbitrum.
- [ ] Implement `_normalize_fusion_order` to convert 1inch orders to `IntentData`.
- [ ] Verify 1inch Fusion settlement requirements (check if `KerneIntentExecutorV2` needs updates).

## 3. LI.FI INTENT INTEGRATION
- [ ] Implement `LifiIntentFetcher` in `bot/solver/zin_solver.py`.
- [ ] Integrate with LI.FI Intent API to fetch cross-chain and local intents.
- [ ] Implement `_normalize_lifi_order` to convert LI.FI orders to `IntentData`.

## 4. AORI INTENT INTEGRATION
- [ ] Implement `AoriIntentFetcher` in `bot/solver/zin_solver.py`.
- [ ] Integrate with Aori API/WebSocket for real-time intent monitoring.
- [ ] Implement `_normalize_aori_order` to convert Aori orders to `IntentData`.

## 5. PRICING ENGINE & GUARDRAIL HARDENING
- [ ] Update `PricingEngine` to handle venue-specific fee structures and gas estimates.
- [ ] Harden `ZIN_MIN_PROFIT_BPS` enforcement across all venues.
- [ ] Implement venue-specific position caps in `_get_intent_cap`.

## 6. ON-CHAIN EXECUTOR UPDATES
- [ ] Audit `KerneIntentExecutorV2.sol` for compatibility with new venue settlement logic.
- [ ] If needed, implement `fulfillFusionIntent` or similar specialized functions.
- [ ] Deploy updated executor (if changes were made) and update `bot/.env`.

## 7. VERIFICATION & TESTING
- [ ] Expand `test/unit/KerneZIN.t.sol` with mock tests for Fusion, LI.FI, and Aori.
- [ ] Create `bot/tests/test_multi_venue_solver.py` for end-to-end dry-run verification.
- [ ] Run `forge test --match-path test/unit/KerneZIN.t.sol` and ensure all pass.
- [ ] Verify zero-fee flash loan logic for the new venues.

## 8. DEPLOYMENT & MONITORING
- [ ] Update `bot/.env` with new API keys and configuration.
- [ ] Restart ZIN Solver in dry-run mode and monitor logs for successful "virtual" fills.
- [ ] Activate live mode for a micro-cap run once virtual fills are validated.
