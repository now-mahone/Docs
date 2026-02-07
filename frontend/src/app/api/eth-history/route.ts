// Created: 2026-02-07
// API endpoint for fetching real Ethereum historical price data

import { NextResponse } from 'next/server';

export const runtime = 'edge';
export const dynamic = 'force-dynamic';

export async function GET() {
  try {
    // Calculate date range (last 13 months for smooth chart)
    const now = new Date();
    const thirteenMonthsAgo = new Date();
    thirteenMonthsAgo.setMonth(now.getMonth() - 13);
    
    const toTimestamp = Math.floor(now.getTime() / 1000);
    const fromTimestamp = Math.floor(thirteenMonthsAgo.getTime() / 1000);

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
    // Convert to monthly data points (first day of each month)
    const prices = data.prices || [];
    
    const monthlyPrices: { date: string; price: number }[] = [];
    const monthsProcessed = new Set<string>();

    for (const [timestamp, price] of prices) {
      const date = new Date(timestamp);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
      
      // Only keep first price of each month
      if (!monthsProcessed.has(monthKey)) {
        monthsProcessed.add(monthKey);
        monthlyPrices.push({
          date: date.toISOString().split('T')[0], // YYYY-MM-DD format
          price: parseFloat(price.toFixed(2)),
        });
      }
    }

    // Sort by date ascending
    monthlyPrices.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());

    return NextResponse.json({
      success: true,
      data: monthlyPrices,
      dataPoints: monthlyPrices.length,
      dateRange: {
        from: monthlyPrices[0]?.date || null,
        to: monthlyPrices[monthlyPrices.length - 1]?.date || null,
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