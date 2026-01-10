# Created: 2026-01-09
from typing import Dict, List, Optional
from loguru import logger
import pandas as pd
from dataclasses import dataclass

@dataclass
class VaultRiskProfile:
    vault_address: str
    net_delta: float
    gamma_exposure: float
    liquidation_distance_onchain: float
    liquidation_distance_cex: float
    health_score: float  # 0 to 100

class RiskEngine:
    """
    Kerne Sentinel Risk Engine
    Calculates real-time risk metrics for Kerne Vaults.
    """
    def __init__(self):
        self.risk_thresholds = {
            "delta_limit": 0.05,  # Max 5% delta exposure
            "min_health_score": 70.0,
            "min_liquidation_distance": 0.20  # 20% buffer
        }

    def calculate_vault_delta(self, onchain_collateral: float, cex_short_position: float) -> float:
        """
        Calculates the net delta of a vault.
        Perfect delta-neutrality = 0.
        """
        if onchain_collateral == 0:
            return 0.0
        
        net_delta = (onchain_collateral + cex_short_position) / onchain_collateral
        return round(net_delta, 4)

    def calculate_health_score(self, profile: Dict) -> float:
        """
        Aggregates various risk metrics into a single health score.
        """
        score = 100.0
        
        # Delta Penalty
        delta_abs = abs(profile.get("net_delta", 0))
        if delta_abs > self.risk_thresholds["delta_limit"]:
            score -= (delta_abs - self.risk_thresholds["delta_limit"]) * 500
            
        # Liquidation Penalty
        liq_dist = min(profile.get("liq_onchain", 1.0), profile.get("liq_cex", 1.0))
        if liq_dist < self.risk_thresholds["min_liquidation_distance"]:
            score -= (self.risk_thresholds["min_liquidation_distance"] - liq_dist) * 200
            
        return max(0.0, min(100.0, score))

    def analyze_vault(self, vault_data: Dict) -> VaultRiskProfile:
        """
        Performs a full risk analysis on a single vault.
        """
        net_delta = self.calculate_vault_delta(
            vault_data["onchain_collateral"], 
            vault_data["cex_short_position"]
        )
        
        profile_dict = {
            "net_delta": net_delta,
            "liq_onchain": vault_data["liq_onchain"],
            "liq_cex": vault_data["liq_cex"]
        }
        
        health_score = self.calculate_health_score(profile_dict)
        
        return VaultRiskProfile(
            vault_address=vault_data["address"],
            net_delta=net_delta,
            gamma_exposure=0.0,  # Placeholder for future gamma logic
            liquidation_distance_onchain=vault_data["liq_onchain"],
            liquidation_distance_cex=vault_data["liq_cex"],
            health_score=health_score
        )
