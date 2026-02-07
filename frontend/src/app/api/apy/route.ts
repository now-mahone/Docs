// Created: 2026-02-07
// Live APY computation from funding rates + staking yields
// Mirrors bot/api_connector.py + bot/apy_calculator.py logic

import { NextResponse } from "next/server";

// ── Funding Rate Fetchers (public, no API keys) ─────────────────────────

async function getHyperliquidFunding(symbol: string = "ETH"): Promise<{ rate: number; annual: number; interval: string } | null> {
  try {
    const res = await fetch("https://api.hyperliquid.xyz/info", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type: "metaAndAssetCtxs" }),
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (Array.isArray(data) && data.length >= 2) {
      const meta = data[0];
      const assetCtxs = data[1];
      const universe = meta.universe || [];
      for (let i = 0; i < universe.length; i++) {
        if (universe[i].name?.toUpperCase() === symbol.toUpperCase()) {
          if (i < assetCtxs.length) {
            const rate = parseFloat(assetCtxs[i].funding || "0");
            return { rate, annual: rate * 24 * 365, interval: "1h" };
          }
        }
      }
    }
  } catch { /* silent */ }
  return null;
}

async function getBinanceFunding(symbol: string = "ETH"): Promise<{ rate: number; annual: number; interval: string } | null> {
  try {
    const res = await fetch(`https://fapi.binance.com/fapi/v1/fundingRate?symbol=${symbol.toUpperCase()}USDT&limit=1`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (Array.isArray(data) && data.length > 0) {
      const rate = parseFloat(data[0].fundingRate || "0");
      return { rate, annual: rate * 3 * 365, interval: "8h" };
    }
  } catch { /* silent */ }
  return null;
}

async function getBybitFunding(symbol: string = "ETH"): Promise<{ rate: number; annual: number; interval: string } | null> {
  try {
    const res = await fetch(`https://api.bybit.com/v5/market/tickers?category=linear&symbol=${symbol.toUpperCase()}USDT`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.retCode === 0) {
      const tickers = data.result?.list || [];
      if (tickers.length > 0) {
        const rate = parseFloat(tickers[0].fundingRate || "0");
        return { rate, annual: rate * 3 * 365, interval: "8h" };
      }
    }
  } catch { /* silent */ }
  return null;
}

async function getOkxFunding(symbol: string = "ETH"): Promise<{ rate: number; annual: number; interval: string } | null> {
  try {
    const res = await fetch(`https://www.okx.com/api/v5/public/funding-rate?instId=${symbol.toUpperCase()}-USDT-SWAP`, {
      signal: AbortSignal.timeout(10000),
    });
    if (!res.ok) return null;
    const data = await res.json();
    if (data?.code === "0") {
      const rates = data.data || [];
      if (rates.length > 0) {
        const rate = parseFloat(rates[0].fundingRate || "0");
        return { rate, annual: rate * 3 * 365, interval: "8h" };
      }
    }
  } catch { /* silent */ }
  return null;
}

// ── Staking Yield Fetcher ────────────────────────────────────────────────

async function getLidoStakingApy(): Promise<number> {
  // Try SMA APR endpoint first
  try {
    const res = await fetch("https://eth-api.lido.fi/v1/protocol/steth/apr/sma", {
      signal: AbortSignal.timeout(10000),
    });
    if (res.ok) {
      const data = await res.json();
      const smaApr = data?.data?.smaApr;
      if (smaApr !== undefined && smaApr !== null) {
        return parseFloat(smaApr) / 100; // Convert from percentage to decimal
      }
    }
  } catch { /* silent */ }

  // Fallback: last APR
  try {
    const res = await fetch("https://eth-api.lido.fi/v1/protocol/steth/apr/last", {
      signal: AbortSignal.timeout(10000),
    });
    if (res.ok) {
      const data = await res.json();
      const apr = data?.data?.apr;
      if (apr !== undefined && apr !== null) {
        return parseFloat(apr) / 100;
      }
    }
  } catch { /* silent */ }

  return 0.035; // Fallback: ~3.5%
}

// ── APY Calculator (mirrors bot/apy_calculator.py) ───────────────────────

function calculateExpectedApy(params: {
  leverage: number;
  fundingRateAnnual: number;
  stakingYield: number;
  spreadEdge: number;
  turnoverRate: number;
  costRate: number;
}): number {
  const { leverage, fundingRateAnnual, stakingYield, spreadEdge, turnoverRate, costRate } = params;
  const expectedLogReturn =
    leverage * fundingRateAnnual +
    leverage * stakingYield +
    turnoverRate * spreadEdge -
    costRate;
  return Math.exp(expectedLogReturn) - 1;
}

// ── Main API Handler ─────────────────────────────────────────────────────

export async function GET() {
  try {
    // Fetch all data in parallel
    const [hlFunding, bnFunding, bbFunding, okxFunding, stakingYield] = await Promise.all([
      getHyperliquidFunding(),
      getBinanceFunding(),
      getBybitFunding(),
      getOkxFunding(),
      getLidoStakingApy(),
    ]);

    // Collect all venues with positive funding
    const venues: Record<string, { rate: number; annual: number; interval: string }> = {};
    if (hlFunding) venues.hyperliquid = hlFunding;
    if (bnFunding) venues.binance = bnFunding;
    if (bbFunding) venues.bybit = bbFunding;
    if (okxFunding) venues.okx = okxFunding;

    // Find best positive funding venue (strategy routes to best venue)
    let bestVenue = "none";
    let bestAnnualFunding = 0;
    for (const [name, data] of Object.entries(venues)) {
      if (data.annual > bestAnnualFunding) {
        bestAnnualFunding = data.annual;
        bestVenue = name;
      }
    }

    // If all venues negative, use the least negative one but floor at 0
    if (bestAnnualFunding < 0) {
      bestAnnualFunding = 0;
    }

    // Calculate protocol APY using best venue (same params as bot)
    const leverage = 3.0;
    const expectedApy = calculateExpectedApy({
      leverage,
      fundingRateAnnual: bestAnnualFunding,
      stakingYield,
      spreadEdge: 0.0005,
      turnoverRate: 0.1,
      costRate: 0.01,
    });

    // APY as percentage (e.g. 0.1597 → 15.97)
    const apyPct = parseFloat((expectedApy * 100).toFixed(2));

    return NextResponse.json(
      {
        apy: apyPct,
        apy_decimal: expectedApy,
        breakdown: {
          best_funding_venue: bestVenue,
          best_funding_annual_pct: parseFloat((bestAnnualFunding * 100).toFixed(4)),
          staking_yield_pct: parseFloat((stakingYield * 100).toFixed(4)),
          leverage,
        },
        venues,
        staking_yield: stakingYield,
        timestamp: new Date().toISOString(),
      },
      {
        headers: {
          "Cache-Control": "public, s-maxage=60, stale-while-revalidate=120",
        },
      }
    );
  } catch (error) {
    console.error("APY API error:", error);
    return NextResponse.json(
      { error: "Failed to compute APY", apy: null },
      { status: 500 }
    );
  }
}