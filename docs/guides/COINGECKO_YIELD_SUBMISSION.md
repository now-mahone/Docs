# Kerne Protocol: CoinGecko Yield Submission Guide

// Created: 2026-02-20

## Objective
To integrate Kerne Protocol's metrics into CoinGecko's Yield section as a lower-stakes testing ground before approaching DefiLlama. This will build institutional credibility and provide a dry run for our API infrastructure.

## Prerequisites
1. **API Endpoint Live**: The endpoint is hosted directly on our Vercel frontend at `https://kerne.finance/api/coingecko/yield`.
2. **Data Accuracy**: The endpoint fetches real-time TVL directly from the Base mainnet smart contract using `viem`.

## API Schema
The `/api/coingecko/yield` endpoint returns data in the following format, which is compatible with standard yield aggregators:

```json
{
  "status": "success",
  "data": [
    {
      "pool_id": "0xKerneVaultAddress-base",
      "pool_name": "kerne USDC Delta-Neutral Basis Yield",
      "tvl": 5000000,
      "apy": 15.5,
      "base_apy": 15.5,
      "reward_apy": 0,
      "reward_tokens": [],
      "underlying_tokens": [
        "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913"
      ],
      "chain": "Base",
      "url": "https://kerne.finance"
    }
  ]
}
```

## Submission Process
1. **Navigate to CoinGecko Support**: Go to the CoinGecko Request Form (usually found at `support.coingecko.com` or via their official listing portal).
2. **Select Category**: Choose "Add New Yield / Farm".
3. **Provide Details**:
   - **Protocol Name**: Kerne Protocol
   - **Website**: https://kerne.finance
   - **API Endpoint**: `https://kerne.finance/api/coingecko/yield`
   - **Description**: Delta-neutral basis yield protocol on Base.
4. **Monitor & Document**:
   - Track the submission ticket.
   - If CoinGecko requests changes to the API schema or asks questions about the yield source, document them immediately in `docs/reports/coingecko_feedback.md`.
   - Use this feedback to refine our ultimate DefiLlama adapter.

## Next Steps
Once CoinGecko successfully lists Kerne, we will use the exact same data structure and operational blueprint to submit our adapter to the official DefiLlama repository.