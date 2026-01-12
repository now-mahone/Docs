# Created: 2026-01-09
# Updated: 2026-01-12 - Institutional Deep Hardening: Volatility-adjusted thresholds & multi-factor risk scoring
import os
import time
import asyncio
import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger
from dataclasses import dataclass, field
from web3 import Web3
from datetime import datetime, timedelta

@dataclass
class VaultRiskProfile:
    vault_address: str
    net_delta: float
    gamma_exposure: float
    vega_exposure: float
    liquidation_distance_onchain: float
    liquidation_distance_cex: float
    volatility_24h: float
    health_score: float  # 0 to 100
    timestamp: float = field(default_factory=time.time)
    risk_factors: Dict = field(default_factory=dict)

class RiskEngine:
    """
    Kerne Sentinel Risk Engine - Institutional Grade
    Calculates real-time risk metrics using volatility-adjusted thresholds.
    """
    def __init__(self, w3: Optional[Web3] = None, private_key: Optional[str] = None):
        self.w3 = w3
        self.private_key = private_key
        self.base_thresholds = {
            "delta_limit": 0.02,  # 2% base limit
            "min_health_score": 80.0,
            "critical_health_score": 60.0,
            "max_slippage_allowed": 0.003, # 0.3%
            "min_liquidation_distance": 0.30, # 30% buffer
            "min_liquidity_depth_usd": 2000000 # $2M
        }
        self.price_history = {} # symbol -> list of prices

    def calculate_volatility(self, symbol: str) -> float:
        """
        Calculates realized volatility using EWMA (Exponentially Weighted Moving Average).
        """
        prices = self.price_history.get(symbol, [])
        if len(prices) < 20:
            return 0.05 # Default 5% if insufficient data
        
        returns = np.diff(np.log(prices))
        # EWMA volatility calculation
        alpha = 0.94 # Standard RiskMetrics lambda
        vol = np.sqrt(np.sum([(alpha**i) * (returns[-(i+1)]**2) for i in range(len(returns))]) * (1-alpha))
        return vol * np.sqrt(365 * 24 * 60) # Annualized

    def get_volatility_adjusted_thresholds(self, symbol: str) -> Dict:
        """
        Adjusts risk thresholds based on current market volatility.
        Higher volatility = tighter thresholds.
        """
        vol = self.calculate_volatility(symbol)
        vol_multiplier = 1.0 + (vol * 2.0) # Scale factor
        
        return {
            "delta_limit": self.base_thresholds["delta_limit"] / vol_multiplier,
            "min_liquidation_distance": self.base_thresholds["min_liquidation_distance"] * vol_multiplier,
            "max_slippage_allowed": self.base_thresholds["max_slippage_allowed"] * vol_multiplier
        }

    async def check_liquidity_depth(self, pair_address: str, amount_usd: float) -> bool:
        """
        Deep Liquidity Check: Queries multiple venues for aggregate depth.
        """
        try:
            from exchange_manager import ExchangeManager
            venues = ["binance", "bybit", "okx"]
            total_depth = 0
            
            async def fetch_depth(ex_id):
                try:
                    ex = ExchangeManager(ex_id)
                    depth = ex.get_order_book_depth(pair_address)
                    return depth.get("bids_usd", 0) + depth.get("asks_usd", 0)
                except:
                    return 0

            depth_results = await asyncio.gather(*[fetch_depth(v) for v in venues])
            total_depth = sum(depth_results)
            
            if total_depth < self.base_thresholds["min_liquidity_depth_usd"]:
                logger.warning(f"Aggregate liquidity depth low: ${total_depth:.2f}")
                return False
            
            # Price impact model: impact = sqrt(trade_size / depth)
            impact = np.sqrt(amount_usd / (total_depth / 2)) * 0.01
            if impact > self.base_thresholds["max_slippage_allowed"]:
                logger.warning(f"Estimated price impact too high: {impact:.4%}")
                return False
                
            return True
        except Exception as e:
            logger.error(f"Deep liquidity check failed: {e}")
            return False

    def calculate_health_score(self, profile: VaultRiskProfile) -> float:
        """
        Multi-factor health score calculation.
        Factors: Delta, Liquidation Distance, Volatility, Liquidity.
        """
        score = 100.0
        
        # 1. Delta Penalty (Exponential)
        thresholds = self.get_volatility_adjusted_thresholds("ETH/USDT")
        delta_excess = max(0, abs(profile.net_delta) - thresholds["delta_limit"])
        score -= (delta_excess * 1000) ** 1.2
        
        # 2. Liquidation Penalty
        liq_dist = min(profile.liquidation_distance_onchain, profile.liquidation_distance_cex)
        if liq_dist < thresholds["min_liquidation_distance"]:
            score -= (thresholds["min_liquidation_distance"] - liq_dist) * 300
            
        # 3. Volatility Penalty
        if profile.volatility_24h > 0.10: # >10% daily vol
            score -= (profile.volatility_24h - 0.10) * 500
            
        return max(0.0, min(100.0, score))

    async def analyze_vault(self, vault_data: Dict) -> VaultRiskProfile:
        """
        Performs a deep institutional risk analysis.
        """
        symbol = vault_data.get("symbol", "ETH/USDT")
        # Update price history
        if symbol not in self.price_history: self.price_history[symbol] = []
        self.price_history[symbol].append(vault_data["current_price"])
        if len(self.price_history[symbol]) > 100: self.price_history[symbol].pop(0)
        
        vol = self.calculate_volatility(symbol)
        
        net_delta = (vault_data["onchain_collateral"] + vault_data["cex_short_position"]) / vault_data["onchain_collateral"]
        
        profile = VaultRiskProfile(
            vault_address=vault_data["address"],
            net_delta=net_delta,
            gamma_exposure=vault_data.get("gamma", 0.0),
            vega_exposure=vault_data.get("vega", 0.0),
            liquidation_distance_onchain=vault_data["liq_onchain"],
            liquidation_distance_cex=vault_data["liq_cex"],
            volatility_24h=vol,
            health_score=0.0 # Calculated below
        )
        
        profile.health_score = self.calculate_health_score(profile)
        
        # Circuit Breaker Logic
        if profile.health_score < self.base_thresholds["critical_health_score"]:
            logger.critical(f"CRITICAL RISK: Vault {profile.vault_address} Health {profile.health_score:.2f}")
            await self.trigger_circuit_breaker(profile.vault_address, f"Health Score {profile.health_score:.2f}")
            
        return profile

    async def trigger_circuit_breaker(self, vault_address: str, reason: str):
        """
        Asynchronous circuit breaker trigger.
        """
        if not self.w3 or not self.private_key: return
        
        try:
            account = self.w3.eth.account.from_key(self.private_key)
            # Minimal ABI for pausing
            pause_abi = [{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"}]
            vault = self.w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=pause_abi)
            
            tx = vault.functions.pause().build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 150000,
                'gasPrice': int(self.w3.eth.gas_price * 1.2), # 20% premium for speed
                'chainId': self.w3.eth.chain_id
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            logger.warning(f"Circuit breaker TX sent: {tx_hash.hex()} | Reason: {reason}")
            
            # Alerting
            from bot.alerts import send_discord_alert
            send_discord_alert(f"🚨 **INSTITUTIONAL CIRCUIT BREAKER**\nVault: {vault_address}\nReason: {reason}\nTX: {tx_hash.hex()}", level="CRITICAL")
            
        except Exception as e:
            logger.error(f"Failed to trigger circuit breaker: {e}")

if __name__ == "__main__":
    # Autonomous Guardian Loop
    from chain_manager import ChainManager
    from exchange_manager import ExchangeManager
    
    async def main():
        logger.info("🛡️ Kerne Sentinel Deep Hardening Loop Starting...")
        chain = ChainManager()
        exchange = ExchangeManager()
        risk_engine = RiskEngine(w3=chain.w3, private_key=chain.private_key)
        
        while True:
            try:
                # Fetch real-time data
                vault_tvl = chain.get_vault_tvl()
                short_pos, _ = exchange.get_short_position('ETH/USDT:USDT')
                price = exchange.get_market_price('ETH/USDT')
                
                vault_data = {
                    "address": chain.vault_address,
                    "onchain_collateral": vault_tvl,
                    "cex_short_position": short_pos,
                    "current_price": price,
                    "liq_onchain": 0.5,
                    "liq_cex": 0.3,
                    "symbol": "ETH/USDT"
                }
                
                await risk_engine.analyze_vault(vault_data)
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Guardian loop error: {e}")
                await asyncio.sleep(10)

    asyncio.run(main())
