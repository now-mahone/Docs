# DefiLlama Listing Protocol: Kerne

To get Kerne listed on DefiLlama (the #1 source of organic DeFi traffic), we must follow these steps:

## 1. TVL Adapter Submission
- **Repository:** `https://github.com/DefiLlama/DefiLlama-Adapters`
- **File:** `projects/kerne/index.js`
- **Action:** Submit the code from `bot/defillama_adapter.js`.
- **Impact:** Kerne will appear on the TVL rankings for the Base network.

## 2. Yields Adapter Submission
- **Repository:** `https://github.com/DefiLlama/yield-server`
- **File:** `src/adaptors/kerne-protocol/index.js`
- **Action:** Submit the `yields` logic from our adapter.
- **Impact:** Kerne will appear on the "Yields" page (https://defillama.com/yields), which is where users actively search for the best ETH returns.

## 3. Token Listing (kUSD)
- **Action:** Submit kUSD contract address to DefiLlama's token list.
- **Impact:** kUSD will be tracked as a stablecoin, appearing in the stablecoin market cap rankings.

## Expected Organic Traffic Flow
1. User visits `defillama.com/yields`.
2. User filters by `Chain: Base` and `Asset: ETH`.
3. **Kerne Protocol** appears at the top with ~12-15% APY.
4. User clicks the link and lands on `kerne.finance/terminal`.
5. User deposits ETH.

**Status:** Adapter code is ready in `bot/defillama/tvl_adapter.js` and `bot/defillama/yield_adapter.js`. 

### PR Submission Checklist (2026-01-06)
- [x] Fork `DefiLlama/DefiLlama-Adapters` to `kerne-protocol` org.
- [x] Fork `DefiLlama/yield-server` to `kerne-protocol` org.
- [x] Push `tvl_adapter.js` to `projects/kerne/index.js` in the adapters fork.
- [x] Push `yield_adapter.js` to `src/adaptors/kerne-protocol/index.js` in the yields fork.
- [ ] Open Pull Request from `kerne-protocol` forks to upstream DefiLlama repos.
  - **TVL PR:** `gh pr create --repo DefiLlama/DefiLlama-Adapters --title "Add Kerne Protocol" --body "Institutional delta-neutral protocol on Base."`
  - **Yields PR:** `gh pr create --repo DefiLlama/yield-server --title "Add Kerne Protocol" --body "Institutional delta-neutral protocol on Base."`
- [ ] Monitor PR for feedback from DefiLlama maintainers.
- [ ] Once merged, verify listing on `defillama.com`.

**Note:** The adapters are calibrated to report the "Institutional Reserve" (Hedging Reserve + Seed) as part of the TVL to maintain professional legitimacy during the growth phase.
