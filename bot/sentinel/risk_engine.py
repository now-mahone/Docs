# Created: 2026-01-09
from typing import Dict, List, Optional
from loguru import logger
import pandas as pd
from dataclasses import dataclass
from web3 import Web3

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
    def __init__(self, w3: Optional[Web3] = None, private_key: Optional[str] = None):
        self.w3 = w3
        self.private_key = private_key
        self.risk_thresholds = {
            "delta_limit": 0.05,  # Max 5% delta exposure
            "min_health_score": 70.0,
            "min_liquidation_distance": 0.20,  # 20% buffer
            "critical_health_score": 40.0  # Trigger circuit breaker
        }
        self.alert_cooldowns = {} # To prevent spamming

    def trigger_circuit_breaker(self, vault_address: str):
        """
        Calls the pause() function on the KerneVault contract.
        Requires PAUSER_ROLE.
        """
        if not self.w3 or not self.private_key:
            logger.error(f"Circuit Breaker failed: Web3 or Private Key not configured for {vault_address}")
            return

        try:
            account = self.w3.eth.account.from_key(self.private_key)
            # Minimal ABI for pausing
            pause_abi = [{"inputs":[],"name":"pause","outputs":[],"stateMutability":"nonpayable","type":"function"}]
            vault_contract = self.w3.eth.contract(address=Web3.to_checksum_address(vault_address), abi=pause_abi)
            
            tx = vault_contract.functions.pause().build_transaction({
                'from': account.address,
                'nonce': self.w3.eth.get_transaction_count(account.address),
                'gas': 100000,
                'gasPrice': self.w3.eth.gas_price,
                'chainId': self.w3.eth.chain_id
            })
            
            signed_tx = self.w3.eth.account.sign_transaction(tx, self.private_key)
            tx_hash = self.w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            
            logger.critical(f"!!! CIRCUIT BREAKER TRIGGERED FOR {vault_address} !!! TX: {tx_hash.hex()}")
            return tx_hash.hex()
        except Exception as e:
            logger.error(f"Failed to trigger circuit breaker for {vault_address}: {e}")

    def calculate_vault_delta(self, onchain_collateral: float, cex_short_position: float) -> float:
        """
        Calculates the net delta of a vault.
        Perfect delta-neutrality = 0.
        """
        if onchain_collateral == 0:
            return 0.0
        
        net_delta = (onchain_collateral + cex_short_position) / onchain_collateral
        return round(net_delta, 4)

    def monitor_lst_peg(self, lst_symbol: str, current_price_eth: float) -> float:
        """
        Monitors LST/ETH peg. Returns the discount/premium.
        """
        # In production, this would fetch from Chainlink/Uniswap
        # For now, we assume 1.0 is parity
        deviation = (current_price_eth - 1.0) / 1.0
        if abs(deviation) > 0.02:  # 2% depeg threshold
            logger.warning(f"CRITICAL: {lst_symbol} depeg detected! Deviation: {deviation:.2%}")
        return deviation

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
        
        # Production Alerting & Circuit Breaker Logic
        if health_score < self.risk_thresholds["min_health_score"]:
            logger.warning(f"Vault {vault_data['address']} health low: {health_score:.2f}")
            
            if health_score < self.risk_thresholds["critical_health_score"]:
                logger.critical(f"Vault {vault_data['address']} CRITICAL RISK! Health: {health_score:.2f}")
                self.trigger_circuit_breaker(vault_data["address"])

        return VaultRiskProfile(
            vault_address=vault_data["address"],
            net_delta=net_delta,
            gamma_exposure=0.0,  # Placeholder for future gamma logic
            liquidation_distance_onchain=vault_data["liq_onchain"],
            liquidation_distance_cex=vault_data["liq_cex"],
            health_score=health_score
        )
