# ZIN Arbitrum Activation Runbook

**Objective:** Activate the Zero-Fee Intent Network (ZIN) on Arbitrum One by seeding liquidity and enabling the solver.

**Status:** Contracts Deployed. Solver Configured. **Awaiting Liquidity.**

## 1. Funding Instructions (User Action Required)

The ZIN Pool on Arbitrum is deployed but empty. To enable intent fulfillment, you must seed it with initial liquidity.

**Target Address (ZIN Pool Arbitrum):**
`0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD`

**Recommended Seed Amounts:**
- **USDC (Native):** 100 - 500 USDC
  - Contract: `0xaf88d065e77c8cC2239327C5EDb3A432268e5831`
- **WETH:** 0.05 - 0.1 WETH
  - Contract: `0x82aF49447D8a07e3bd95BD0d56f35241523fBab1`

**Action:**
Send the above amounts to the ZIN Pool address on Arbitrum One.

## 2. Solver Verification

Once funded, the solver (which is already configured for `ZIN_CHAINS=base,arbitrum`) will automatically detect the liquidity and begin bidding on UniswapX Dutch_V2 orders on Arbitrum.

**Verification Steps:**
1.  Check the logs for `[arbitrum] Found X potential intents`.
2.  Look for `Liquidity for WETH: <amount>` debug logs.
3.  Monitor for `Intent fulfilled successfully!` messages with Arbitrum TX hashes.

## 3. Troubleshooting

If the solver does not pick up Arbitrum intents:
1.  **Check RPC:** Ensure `ARBITRUM_RPC_URL` is set and responsive in `.env`.
2.  **Check Whitelist:** Ensure the tokens (USDC, WETH) are whitelisted in the ZIN Pool.
    - *Note:* This was done via `EnableZINTokensArbitrum.s.sol` (check project state).
3.  **Check Role:** Ensure the bot wallet (`0x57D4...0A99`) has `SOLVER_ROLE` on the Arbitrum pool.
    - *Note:* Confirmed in project state on 2026-01-20.

## 4. Rollback

If the solver behaves erratically on Arbitrum:
1.  Edit `.env` to set `ZIN_CHAINS=base`.
2.  Restart the bot.
3.  Withdraw liquidity from the ZIN Pool using the `adminWithdraw` function (requires admin key).