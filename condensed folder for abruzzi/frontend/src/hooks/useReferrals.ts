import { useState, useEffect } from 'react';
import { useAccount } from 'wagmi';

export interface ReferralStats {
  code: string;
  link: string;
  tier: string;
  referrals: number;
  totalVolume: string;
  pendingCommissions: string;
  totalEarned: string;
  wealthVelocity: string;
}

export function useReferrals() {
  const { address } = useAccount();
  const [stats, setStats] = useState<ReferralStats | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchStats = async () => {
    if (!address) return;
    setLoading(true);
    try {
      const response = await fetch(`/api/referrals?address=${address}`);
      if (!response.ok) throw new Error('Failed to fetch referral stats');
      const data = await response.json();
      setStats(data);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStats();
  }, [address]);

  const linkReferrer = async (code: string) => {
    if (!address) return;
    try {
      const response = await fetch('/api/referrals', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address, code }),
      });
      return await response.json();
    } catch (err: any) {
      console.error('Failed to link referrer:', err);
    }
  };

  const claimCommissions = async () => {
    if (!address) return;
    try {
      const response = await fetch('/api/referrals', {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ address }),
      });
      const data = await response.json();
      if (data.success) {
        await fetchStats();
      }
      return data;
    } catch (err: any) {
      console.error('Failed to claim commissions:', err);
    }
  };

  return { stats, loading, error, refresh: fetchStats, linkReferrer, claimCommissions };
}
