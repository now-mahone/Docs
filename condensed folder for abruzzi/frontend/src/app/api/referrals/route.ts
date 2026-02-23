import { NextResponse } from 'next/server';
import fs from 'fs';
import path from 'path';

// In a production environment, this would be backed by a database (e.g., Redis or Postgres)
// For the Genesis phase, we use an in-memory store or simple mapping logic
const referralStore: Record<string, string> = {};

export async function GET(request: Request) {
  const { searchParams } = new URL(request.url);
  const address = searchParams.get('address');

  const dbPath = path.join(process.cwd(), '..', 'bot', 'data', 'referrals.json');
  let allData: any = {};

  try {
    if (fs.existsSync(dbPath)) {
      allData = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
    }
  } catch (e) {
    console.error("Failed to read referral DB:", e);
  }

  if (!address) {
    return NextResponse.json({ error: 'Address required' }, { status: 400 });
  }

  // Generate a deterministic referral code if one doesn't exist
  const referralCode = address.toLowerCase().slice(2, 10).toUpperCase();
  
  // Read real data from the bot's referral database
  let realStats = {
    pendingCommissions: 0.0,
    totalEarned: 0.0,
    totalVolume: 0.0,
    referrals: 0,
    wealthVelocity: 0.0
  };

  if (allData[address.toLowerCase()]) {
    const userRefData = allData[address.toLowerCase()];
    realStats = {
      pendingCommissions: userRefData.pending_commissions || 0,
      totalEarned: userRefData.total_earned || 0,
      totalVolume: userRefData.total_volume_referred || 0,
      referrals: userRefData.referral_count || 0,
      wealthVelocity: userRefData.wealth_velocity || 0
    };
  }

  const stats = {
    code: referralCode,
    link: `https://kerne.finance/terminal?ref=${referralCode}`,
    tier: 'Genesis Partner',
    referrals: realStats.referrals,
    totalVolume: `${realStats.totalVolume.toFixed(2)} ETH`,
    pendingCommissions: `${realStats.pendingCommissions.toFixed(4)} ETH`,
    totalEarned: `${realStats.totalEarned.toFixed(4)} ETH`,
    wealthVelocity: `${(realStats.wealthVelocity * 100).toFixed(2)}%`,
  };

  return NextResponse.json(stats);
}

export async function POST(request: Request) {
  const body = await request.json();
  const { address, code } = body;

  if (!address || !code) {
    return NextResponse.json({ error: 'Address and code required' }, { status: 400 });
  }

  // Logic to link a new user to a referrer
  console.log(`Linking ${address} to referrer ${code}`);

  return NextResponse.json({ success: true });
}

export async function PATCH(request: Request) {
  const body = await request.json();
  const { address } = body;

  if (!address) {
    return NextResponse.json({ error: 'Address required' }, { status: 400 });
  }

  const dbPath = path.join(process.cwd(), '..', 'bot', 'data', 'referrals.json');
  
  try {
    if (fs.existsSync(dbPath)) {
      const data = JSON.parse(fs.readFileSync(dbPath, 'utf8'));
      const userAddr = address.toLowerCase();
      
      if (data[userAddr] && data[userAddr].pending_commissions > 0) {
        const amount = data[userAddr].pending_commissions;
        data[userAddr].pending_commissions = 0;
        // In a real app, we'd trigger a transfer here
        fs.writeFileSync(dbPath, JSON.stringify(data, null, 4));
        return NextResponse.json({ success: true, amount });
      }
    }
  } catch (e) {
    console.error("Failed to process payout:", e);
  }

  return NextResponse.json({ error: 'No pending commissions' }, { status: 400 });
}
