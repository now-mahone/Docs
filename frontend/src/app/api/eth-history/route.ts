// Created: 2026-02-07
// API endpoint for fetching real Ethereum historical price data

import { NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Calculate date range (rolling 1 year window)
    const now = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(now.getFullYear() - 1);
    
    const toTimestamp = Math.floor(now.getTime() / 1000);
    const fromTimestamp = Math.floor(oneYearAgo.getTime() / 1000);

    // Fetch real ETH historical prices from CoinGecko
    const response = await fetch(
      `https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range?vs_currency=usd&from=${fromTimestamp}&to=${toTimestamp}`,
      {
        headers: {
          'Accept': 'application/json',
        },
        next: {
          revalidate: 3600, // Cache for 1 hour
        },
      }
    );

    if (!response.ok) {
      throw new Error(`CoinGecko API error: ${response.status}`);
    }

    const data = await response.json();

    // CoinGecko returns { prices: [[timestamp, price], ...] }
    // Keep daily data points (1 year = ~365 points)
    const prices = data.prices || [];
    
    // Deduplicate to one price per day (CoinGecko sometimes returns multiple points per day)
    const dailyMap = new Map<string, number>();

    for (const [timestamp, price] of prices) {
      const dateStr = new Date(timestamp).toISOString().split('T')[0]; // YYYY-MM-DD
      // Keep the last price seen for each day
      dailyMap.set(dateStr, price);
    }

    const dailyPrices: { date: string; price: number }[] = Array.from(dailyMap.entries()).map(
      ([date, price]) => ({
        date,
        price: parseFloat(price.toFixed(2)),
      })
    );

    // Sort by date ascending
    dailyPrices.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return NextResponse.json({
      success: true,
      data: dailyPrices,
      dataPoints: dailyPrices.length,
      dateRange: {
        from: dailyPrices[0]?.date || null,
        to: dailyPrices[dailyPrices.length - 1]?.date || null,
      },
    });
  } catch (error: any) {
    console.error('Error fetching ETH historical data:', error);
    
    return NextResponse.json(
      {
        success: false,
        error: error.message || 'Failed to fetch historical data',
        data: [], // Return empty array as fallback
      },
      { status: 500 }
    );
  }
}