// Created: 2025-12-30
import { useState, useEffect } from 'react';

export interface SolvencyData {
  assets: {
    total_eth: string;
    total_usd: string;
    on_chain_eth: string;
    off_chain_eth: string;
    breakdown: Array<{
      name: string;
      value: string;
      type: string;
    }>;
  };
  liabilities: {
    total_usd: string;
    kusd_supply: string;
  };
  solvency_ratio: string;
  status: string;
  timestamp: string;
}

export function useSolvency() {
  const [data, setData] = useState<SolvencyData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/solvency');
      if (!response.ok) throw new Error('Failed to fetch solvency data');
      const result = await response.json();
      setData(result);
    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  return { data, loading, error, refetch: fetchData };
}
