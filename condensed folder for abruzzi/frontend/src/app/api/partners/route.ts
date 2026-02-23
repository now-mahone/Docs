import { NextResponse } from "next/server";

// Created: 2026-01-04
// Mock data for the leaderboard to simulate activity and social proof
// In production, this would be fetched from a database or indexed events

export async function GET() {
  const topEarners = [
    { address: "0x71C...3f4E", name: "Institutional_Alpha", yield: "42.15 ETH", tvl: "$1.2M" },
    { address: "0x12A...9b2C", name: "Whale_Hunter", yield: "18.42 ETH", tvl: "$540k" },
    { address: "0x88F...1a0D", name: "Yield_Maxi", yield: "12.05 ETH", tvl: "$350k" },
    { address: "0x33B...7c4F", name: "Base_God", yield: "9.88 ETH", tvl: "$290k" },
    { address: "0x55E...2d1A", name: "Delta_Neutral_King", yield: "7.42 ETH", tvl: "$210k" },
  ];

  const topReferrers = [
    { address: "0x99D...4e2B", name: "Kerne_Evangelist", referrals: 42, volume: "$2.4M" },
    { address: "0x22C...8f1A", name: "DeFi_Influencer", referrals: 28, volume: "$1.1M" },
    { address: "0x44A...3d5C", name: "Alpha_Caller", referrals: 19, volume: "$850k" },
    { address: "0x66B...9e0F", name: "Yield_Aggregator", referrals: 14, volume: "$620k" },
    { address: "0x11D...5c3E", name: "Early_Adopter", referrals: 11, volume: "$410k" },
  ];

  const recentActivity = [
    { type: "DEPOSIT", address: "0x88F...1a0D", amount: "25.00 ETH", time: "2m ago" },
    { type: "REFERRAL", address: "0x99D...4e2B", amount: "0.42 ETH Earned", time: "15m ago" },
    { type: "DEPOSIT", address: "0x12A...9b2C", amount: "150.00 ETH", time: "1h ago" },
    { type: "MINT", address: "0x71C...3f4E", amount: "50,000 kUSD", time: "3h ago" },
  ];

  return NextResponse.json({
    topEarners,
    topReferrers,
    recentActivity,
    timestamp: new Date().toISOString(),
  });
}
