from dotenv import load_dotenv
from loguru import logger
from bot.chain_manager import ChainManager
from bot.exchange_manager import ExchangeManager

# Created: 2025-12-28


def verify_live_system():
    """
    Checks the health of the live system by comparing Vault TVL and CEX Short Position.
    """
    load_dotenv()

    logger.info("Starting Genesis Verification...")

    try:
        # 1. Check Vault TVL on Base
        chain = ChainManager()
        vault_tvl = chain.get_vault_assets()
        logger.info(f"Vault TVL on Base: {vault_tvl:.4f} ETH")

        # 2. Check Short Position on CEX
        exchange = ExchangeManager()
        # Assuming we are shorting ETH/USDT or similar
        # This is a simplified check for the purpose of genesis verification
        positions = exchange.exchange.fetch_positions()
        eth_short_size = 0
        for pos in positions:
            if pos['symbol'].startswith('ETH') and float(pos['contracts']) > 0:
                # Rough estimate in ETH
                eth_short_size = abs(float(pos['notional']) / pos['markPrice'])
                break

        logger.info(f"Estimated Short Position on CEX: {eth_short_size:.4f} ETH equivalent")

        # 3. Delta Calculation
        delta = abs(vault_tvl - eth_short_size)
        logger.info(f"Current Delta: {delta:.4f} ETH")

        if delta < 0.1:
            logger.success("SYSTEM HEALTHY: Delta is within acceptable limits (< 0.1 ETH).")
        else:
            msg = f"SYSTEM ALERT: High Delta detected ({delta:.4f} ETH). Manual rebalancing may be required."
            logger.warning(msg)

    except Exception as e:
        logger.error(f"Verification failed: {e}")


if __name__ == "__main__":
    verify_live_system()
