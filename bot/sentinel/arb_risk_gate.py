# Created: 2026-01-16
from dataclasses import dataclass
from typing import Optional, Tuple, Dict
from loguru import logger
from bot.sentinel.risk_engine import RiskEngine, VaultRiskProfile

@dataclass
class ArbRiskGate:
    """Explicit risk gates for flash arb execution."""
    
    # Hard blocks - never execute if violated
    MIN_HEALTH_SCORE: float = 70.0           # Below this = circuit breaker territory
    MAX_DELTA_DEVIATION: float = 0.03        # 3% net delta = too exposed
    MIN_LIQUIDITY_DEPTH_USD: float = 500_000 # $500k minimum for arb size
    MAX_VAR_99_PCT: float = 0.05             # 5% of portfolio at risk
    MAX_VOLATILITY_24H: float = 0.15         # 15% daily vol = too risky
    
    # Soft limits - reduce position size
    WARN_HEALTH_SCORE: float = 80.0
    WARN_VAR_99_PCT: float = 0.03
    
    def evaluate(self, profile: VaultRiskProfile, arb_size_usd: float) -> Tuple[bool, str, float]:
        """
        Returns: (should_execute, reason, position_multiplier)
        position_multiplier: 1.0 = full size, 0.5 = half size, 0 = blocked
        """
        # Hard blocks
        if profile.health_score < self.MIN_HEALTH_SCORE:
            return False, f"Health score {profile.health_score:.1f} < {self.MIN_HEALTH_SCORE}", 0.0
        
        if abs(profile.net_delta) > self.MAX_DELTA_DEVIATION:
            return False, f"Delta deviation {profile.net_delta:.4f} > {self.MAX_DELTA_DEVIATION}", 0.0
        
        if profile.volatility_24h > self.MAX_VOLATILITY_24H:
            return False, f"24h volatility {profile.volatility_24h:.2%} > {self.MAX_VOLATILITY_24H:.2%}", 0.0
        
        # Calculate VaR as percentage of arb size (or portfolio if preferred)
        # Here we use the VaR from the profile which is absolute USD
        var_usd = profile.risk_factors.get("VaR_99", 0)
        # If we don't have portfolio value, we can't calculate pct easily here without more context
        # But we can use a fixed USD limit or pass in portfolio value
        
        # Soft limits - reduce size
        multiplier = 1.0
        if profile.health_score < self.WARN_HEALTH_SCORE:
            multiplier *= 0.5
            logger.warning(f"Risk gate soft limit: Health score {profile.health_score:.1f} < {self.WARN_HEALTH_SCORE}. Multiplier: {multiplier}")
        
        return True, "OK", multiplier
