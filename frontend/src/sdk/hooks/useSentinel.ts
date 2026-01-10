// Created: 2026-01-09
import { useState, useEffect } from 'react';

export interface RiskProfile {
  vault_address: string;
  net_delta: number;
  health_score: number;
  liquidation_distance_onchain: number;
  liquidation_distance_cex: number;
}

export const useSentinel = (vaultAddress: string) => {
  const [risk, setRisk] = useState<RiskProfile | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!vaultAddress) return;

    // Fetch initial risk data
    const fetchRisk = async () => {
      try {
        const response = await fetch(`http://localhost:8080/vault/${vaultAddress}/risk`);
        const data = await response.json();
        setRisk(data);
      } catch (error) {
        console.error('Failed to fetch risk data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRisk();

    // Connect to WebSocket for real-time updates
    const ws = new WebSocket('ws://localhost:8080/ws/risk');
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.vault === vaultAddress) {
        setRisk((prev) => prev ? { ...prev, health_score: data.health_score, net_delta: data.net_delta } : null);
      }
    };

    return () => ws.close();
  }, [vaultAddress]);

  return { risk, loading };
};
