// Created: 2026-02-07
// API endpoint for fetching real Ethereum historical price data

import { NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

// Retry logic with exponential backoff
async function fetchWithRetry(url: string, maxRetries = 3): Promise<Response> {
  let lastError: Error | null = null;
  
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      const response = await fetch(url, {
        headers: {
          'Accept': 'application/json',
        },
        signal: AbortSignal.timeout(10000), // 10 second timeout
      });
      
      if (response.ok) {
        return response;
      }
      
      // If rate limited (429), wait longer
      if (response.status === 429) {
        const waitTime = Math.min(1000 * Math.pow(2, attempt + 2), 8000); // 4s, 8s, 8s
        await new Promise(resolve => setTimeout(resolve, waitTime));
        continue;
      }
      
      throw new Error(`API error: ${response.status}`);
    } catch (error: any) {
      lastError = error;
      
      // Don't retry on timeout or abort
      if (error.name === 'AbortError' || error.name === 'TimeoutError') {
        break;
      }
      
      // Exponential backoff: 1s, 2s, 4s
      if (attempt < maxRetries - 1) {
        const waitTime = 1000 * Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, waitTime));
      }
    }
  }
  
  throw lastError || new Error('Failed to fetch after retries');
}

export async function GET() {
  try {
    // Calculate date range (rolling 1 year window)
    const now = new Date();
    const oneYearAgo = new Date();
    oneYearAgo.setFullYear(now.getFullYear() - 1);
    
    const toTimestamp = Math.floor(now.getTime() / 1000);
    const fromTimestamp = Math.floor(oneYearAgo.getTime() / 1000);

    // Fetch real ETH historical prices from CoinGecko with retry logic
    const response = await fetchWithRetry(
      `https://api.coingecko.com/api/v3/coins/ethereum/market_chart/range?vs_currency=usd&from=${fromTimestamp}&to=${toTimestamp}`
    );

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

    return NextResponse.json(
      {
        success: true,
        data: dailyPrices,
        dataPoints: dailyPrices.length,
        dateRange: {
          from: dailyPrices[0]?.date || null,
          to: dailyPrices[dailyPrices.length - 1]?.date || null,
        },
      },
      {
        headers: {
          'Cache-Control': 'public, s-maxage=86400, stale-while-revalidate=43200',
        },
      }
    );
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