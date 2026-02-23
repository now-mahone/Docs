// Created: 2025-12-29
import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const address = searchParams.get('address')?.toLowerCase();
  const leaderboard = searchParams.get('leaderboard') === 'true';

  try {
    const dbPath = path.join(process.cwd(), '..', 'bot', 'data', 'credits.json');
    
    if (!fs.existsSync(dbPath)) {
      return NextResponse.json({ credits: 0, leaderboard: [] });
    }

    const fileContent = fs.readFileSync(dbPath, 'utf8');
    const creditsData = JSON.parse(fileContent);

    if (leaderboard) {
      const sortedLeaderboard = Object.entries(creditsData)
        .map(([addr, data]: [string, any]) => ({
          address: addr,
          credits: data.total_credits,
          multiplier: data.multiplier,
          referrals: data.referral_count || 0
        }))
        .sort((a, b) => b.credits - a.credits)
        .slice(0, 10);

      return NextResponse.json({ leaderboard: sortedLeaderboard });
    }

    if (!address) {
      return NextResponse.json({ error: 'Address is required' }, { status: 400 });
    }

    const userData = creditsData[address] || { total_credits: 0, multiplier: 1.0, referral_count: 0 };

    return NextResponse.json({ 
      credits: userData.total_credits,
      multiplier: userData.multiplier,
      referrals: userData.referral_count
    });
  } catch (error) {
    console.error('Error fetching credits:', error);
    return NextResponse.json({ error: 'Internal Server Error' }, { status: 500 });
  }
}

export async function POST(request: Request) {
  try {
    const { address, referredBy } = await request.json();
    
    if (!address) {
      return NextResponse.json({ error: 'Address is required' }, { status: 400 });
    }

    // In a real app, we'd send this to the bot or a shared DB
    // For now, we'll simulate the referral registration
    console.log(`Registering referral: ${address} referred by ${referredBy}`);
    
    return NextResponse.json({ success: true });
  } catch (error) {
    return NextResponse.json({ error: 'Invalid request' }, { status: 400 });
  }
}
