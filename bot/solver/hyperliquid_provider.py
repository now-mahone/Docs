# Created: 2026-01-13
import asyncio
from loguru import logger
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import eth_account
import os
from dotenv import load_dotenv

load_dotenv()

class HyperliquidProvider:
    def __init__(self, private_key=None, account_address=None):
        self.private_key = private_key or os.getenv("HYPERLIQUID_PRIVATE_KEY")
        self.account_address = account_address or os.getenv("HYPERLIQUID_ADDRESS")
        
        # Use mainnet by default
        self.base_url = constants.MAINNET_API_URL
        self.info = Info(self.base_url, skip_ws=True)
        
        if self.private_key:
            self.account = eth_account.Account.from_key(self.private_key)
            self.exchange = Exchange(self.account, self.base_url)
            logger.info(f"Hyperliquid Provider initialized for address: {self.account.address}")
        else:
            logger.warning("Hyperliquid Provider initialized in READ-ONLY mode (no private key)")

    async def get_funding_rate(self, coin="ETH"):
        """
        Fetches the current annualized funding rate for a coin.
        """
        try:
            contexts = self.info.meta_and_asset_ctxs()
            # contexts is a list [meta, asset_ctxs]
            asset_ctxs = contexts[1]
            universe = contexts[0]['universe']
            
            coin_index = next((i for i, asset in enumerate(universe) if asset['name'] == coin), None)
            if coin_index is not None:
                ctx = asset_ctxs[coin_index]
                funding = float(ctx['funding'])
                # Hyperliquid funding is 1-hour. Annualized = funding * 24 * 365
                annualized_funding = funding * 24 * 365
                logger.debug(f"Current {coin} funding: {funding} (Annualized: {annualized_funding:.2%})")
                return annualized_funding
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            return 0.0
            
    async def open_short(self, coin, size_eth, leverage):
        """
        Opens a short position on Hyperliquid.
        """
        if not self.private_key:
            logger.error("Cannot open short: No private key provided")
            return False
            
        try:
            logger.info(f"Opening {leverage}x Short on {coin} for {size_eth} ETH")
            # Set leverage first
            self.exchange.update_leverage(leverage, coin)
            
            # Market order short
            # is_buy=False for short
            order_result = self.exchange.market_open(coin, False, size_eth, None, 0.01) # 1% slippage tolerance
            
            if order_result["status"] == "ok":
                logger.info(f"Short opened successfully: {order_result}")
                return True
            else:
                logger.error(f"Failed to open short: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Error opening short: {e}")
            return False
        
    async def close_short(self, coin, size_eth):
        """
        Closes a short position.
        """
        if not self.private_key:
            logger.error("Cannot close short: No private key provided")
            return False
            
        try:
            logger.info(f"Closing Short on {coin} for {size_eth} ETH")
            # Market order buy to close short
            order_result = self.exchange.market_close(coin, size_eth, None, 0.01)
            
            if order_result["status"] == "ok":
                logger.info(f"Short closed successfully: {order_result}")
                return True
            else:
                logger.error(f"Failed to close short: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Error closing short: {e}")
            return False

if __name__ == "__main__":
    hl = HyperliquidProvider()
    # Test funding rate fetch
    rate = asyncio.run(hl.get_funding_rate("ETH"))
    print(f"Annualized ETH Funding: {rate:.2%}")
