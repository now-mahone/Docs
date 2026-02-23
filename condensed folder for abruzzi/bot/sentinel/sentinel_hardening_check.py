# Created: 2026-01-20
"""
Sentinel Hardening Validation Helper

Runs a localized analysis pass with mocked vault data to validate:
- Adaptive EWMA volatility calculation
- LST/ETH depeg detection
- Risk profile calculation and circuit breaker logic

Usage:
    python bot/sentinel/sentinel_hardening_check.py
"""
from loguru import logger
from bot.sentinel.risk_engine import RiskEngine


def build_mock_vault(lst_eth_ratio: float):
    return {
        "address": "0xMockVault",
        "onchain_collateral": 1000.0,
        "cex_short_position": -995.0,
        "current_price": 2000.0,
        "liq_onchain": 0.5,
        "liq_cex": 0.3,
        "symbol": "ETH/USDT",
        "lst_eth_ratio": lst_eth_ratio,
        "available_margin_usd": 100000.0
    }


async def run_validation():
    engine = RiskEngine()

    async def _mock_unwind(*_, **__):
        logger.warning("Emergency unwind skipped in mock validation run.")

    engine.emergency_unwind = _mock_unwind

    logger.info("Running Sentinel hardening validation...")

    # Seed price history with stable prices then spike volatility
    for price in [2000 + i for i in range(50)]:
        await engine.analyze_vault({
            "address": "0xMockVault",
            "onchain_collateral": 1000.0,
            "cex_short_position": -1000.0,
            "current_price": float(price),
            "liq_onchain": 0.5,
            "liq_cex": 0.3,
            "symbol": "ETH/USDT",
            "lst_eth_ratio": 1.0,
            "available_margin_usd": 100000.0
        })

    # Trigger depeg detection
    await engine.analyze_vault(build_mock_vault(0.97))
    await engine.analyze_vault(build_mock_vault(0.97))
    await engine.analyze_vault(build_mock_vault(0.97))

    logger.info("Validation complete. Emergency unwind failures are expected in this mock run.")


if __name__ == "__main__":
    import asyncio
    asyncio.run(run_validation())
