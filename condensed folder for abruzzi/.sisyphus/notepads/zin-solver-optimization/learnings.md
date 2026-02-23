## [2026-01-26] 1inch Fusion Settlement Analysis
- 1inch Fusion requires the filler (resolver) to provide the takerAsset to the Settlement contract.
- The Settlement contract handles the transfer to the user.
- Current KerneIntentExecutorV2.sol sends tokenOut directly to the user, which is incompatible with Fusion.
- Recommendation: Implement fulfillFusionIntent in KerneIntentExecutorV2.sol that skips the direct transfer to the user and instead approves the Fusion settler.
