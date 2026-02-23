import asyncio
import os
from loguru import logger
from bot.flash_arb_scanner import GraphArbScanner, Token, DEX, Pool
from bot.sentinel.risk_engine import RiskEngine

async def test_full_cycle_dry_run():
    logger.info("🚀 Starting Production Arb-Sentinel Integration Test (Dry Run)")
    
    # 1. Initialize Scanner
    try:
        scanner = GraphArbScanner()
        logger.success("✅ Scanner initialized")
    except Exception as e:
        logger.error(f"❌ Scanner initialization failed: {e}")
        return

    # 2. Mock a cycle
    weth = scanner.WETH
    usdc = scanner.USDC
    mock_pool = Pool(DEX.UNISWAP_V3, weth, usdc, fee=500)
    cycle = [mock_pool, Pool(DEX.AERODROME, usdc, weth, stable=False)]
    
    logger.info(f"Testing cycle: WETH -> USDC -> WETH")

    # 3. Test Quote Logic
    try:
        amount_in = 10**18 # 1 ETH
        out = await scanner.get_quote(mock_pool, weth, amount_in)
        logger.info(f"Quote Result: 1 ETH -> {out/1e6:.2f} USDC")
        logger.success("✅ Quote logic functional")
    except Exception as e:
        logger.error(f"❌ Quote logic failed: {e}")

    # 4. Test Risk Engine
    try:
        risk_engine = scanner.risk_engine
        vault_data = {
            "address": "0x0000000000000000000000000000000000000000",
            "onchain_collateral": 1000.0,
            "cex_short_position": -1000.0,
            "current_price": 3000.0,
            "liq_onchain": 0.5,
            "liq_cex": 0.3,
            "symbol": "ETH/USDT"
        }
        profile = await risk_engine.analyze_vault(vault_data)
        logger.info(f"Risk Profile Health: {profile.health_score:.2f}")
        logger.success("✅ Risk engine functional")
    except Exception as e:
        logger.error(f"❌ Risk engine failed: {e}")

    # 5. Verify Sentinel Check
    allowed, multiplier = await scanner.check_sentinel_risk(1000.0)
    if allowed:
        logger.success(f"✅ Sentinel check functional (Allowed, Multiplier: {multiplier})")
    else:
        logger.warning("⚠️ Sentinel check functional (Blocked)")

    logger.info("🏁 Integration test complete.")

if __name__ == "__main__":
    asyncio.run(test_full_cycle_dry_run())
