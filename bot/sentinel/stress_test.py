# Created: 2026-01-09
from bot.sentinel.risk_engine import RiskEngine
from bot.sentinel.performance_tracker import PerformanceTracker
from bot.sentinel.report_generator import ReportGenerator
from loguru import logger
import time

def run_stress_test():
    logger.info("Starting Kerne Sentinel Stress Test...")
    
    risk_engine = RiskEngine()
    perf_tracker = PerformanceTracker()
    report_gen = ReportGenerator(output_dir="stress_test_reports")
    
    vault_address = "0xSTRESS_TEST_VAULT"
    
    # Scenario 1: Perfect Delta Neutrality
    logger.info("Scenario 1: Perfect Delta Neutrality")
    data_1 = {
        "address": vault_address,
        "onchain_collateral": 1000.0,
        "cex_short_position": -1000.0,
        "liq_onchain": 0.50,
        "liq_cex": 0.50
    }
    profile_1 = risk_engine.analyze_vault(data_1)
    logger.info(f"Health Score: {profile_1.health_score}, Delta: {profile_1.net_delta}")
    
    # Scenario 2: Delta Drift (Market Volatility)
    logger.info("Scenario 2: Delta Drift (Market Volatility)")
    data_2 = {
        "address": vault_address,
        "onchain_collateral": 1100.0, # Price went up
        "cex_short_position": -1000.0, # Short didn't adjust yet
        "liq_onchain": 0.40,
        "liq_cex": 0.30
    }
    profile_2 = risk_engine.analyze_vault(data_2)
    logger.info(f"Health Score: {profile_2.health_score}, Delta: {profile_2.net_delta}")
    
    # Scenario 3: Liquidation Risk
    logger.info("Scenario 3: Liquidation Risk")
    data_3 = {
        "address": vault_address,
        "onchain_collateral": 1000.0,
        "cex_short_position": -1000.0,
        "liq_onchain": 0.15, # Below 20% threshold
        "liq_cex": 0.50
    }
    profile_3 = risk_engine.analyze_vault(data_3)
    logger.info(f"Health Score: {profile_3.health_score}, Delta: {profile_3.net_delta}")
    
    # Generate Report for Scenario 2
    perf_data = {
        "apy": 0.15,
        "attribution": {
            "funding_revenue": 0.80,
            "basis_trading": 0.15,
            "staking_rewards": 0.05
        }
    }
    report_path = report_gen.generate_vault_report(vault_address, profile_2, perf_data)
    logger.info(f"Stress test report generated at: {report_path}")

if __name__ == "__main__":
    run_stress_test()
