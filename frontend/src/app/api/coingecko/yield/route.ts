import { NextResponse } from "next/server";
import { createPublicClient, http, formatEther } from "viem";
import { base } from "viem/chains";
import { VAULT_ADDRESS } from "@/config";

// Created: 2026-02-20
// CoinGecko Yield API Endpoint

const abi = [
  {
    inputs: [],
    name: "totalAssets",
    outputs: [{ internalType: "uint256", name: "", type: "uint256" }],
    stateMutability: "view",
    type: "function",
  },
] as const;

export async function GET() {
  try {
    const client = createPublicClient({
      chain: base as any,
      transport: http(process.env.RPC_URL || "https://mainnet.base.org"),
    });

    const totalAssets = await client.readContract({
      address: VAULT_ADDRESS as `0x${string}`,
      abi,
      functionName: "totalAssets",
    });

    const tvl_eth = parseFloat(formatEther(totalAssets));
    
    // Fetch ETH price
    const priceRes = await fetch("https://api.binance.com/api/v3/ticker/price?symbol=ETHUSDT");
    const priceData = await priceRes.json();
    const ethPrice = parseFloat(priceData.price);
    
    const tvl_usd = tvl_eth * ethPrice;

    // CoinGecko Yield Schema
    const response = {
      status: "success",
      data: [
        {
          pool_id: `${VAULT_ADDRESS}-base`,
          pool_name: "Kerne WETH Delta-Neutral Basis Yield",
          tvl: tvl_usd,
          apy: 15.5,
          base_apy: 15.5,
          reward_apy: 0,
          reward_tokens: [],
          underlying_tokens: [
            "0x4200000000000000000000000000000000000006" // WETH on Base
          ],
          chain: "Base",
          url: "https://kerne.finance"
        }
      ]
    };

    return NextResponse.json(response);
  } catch (error) {
    console.error("CoinGecko API Error:", error);
    return NextResponse.json({ status: "error", message: "Internal Server Error" }, { status: 500 });
  }
}