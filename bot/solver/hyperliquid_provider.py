# Created: 2026-01-13
import asyncio
from loguru import logger
from hyperliquid.info import Info
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
import eth_account
import os
import json
from dotenv import load_dotenv

load_dotenv()

class HyperliquidProvider:
    def __init__(self, private_key=None, account_address=None):
        self.private_key = private_key or os.getenv("HYPERLIQUID_PRIVATE_KEY")
        self.account_address = account_address or os.getenv("HYPERLIQUID_ADDRESS")
        self.state_file = "bot/solver/hl_positions.json"
        
        # Use mainnet by default
        self.base_url = constants.MAINNET_API_URL
        self.info = Info(self.base_url, skip_ws=True)
        
        if self.private_key:
            self.account = eth_account.Account.from_key(self.private_key)
            self.exchange = Exchange(self.account, self.base_url)
            logger.info(f"Hyperliquid Provider initialized for address: {self.account.address}")
        else:
            logger.warning("Hyperliquid Provider initialized in READ-ONLY mode (no private key)")
            
        self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    self.positions = json.load(f)
            except Exception as e:
                logger.error(f"Error loading HL state: {e}")
                self.positions = {}
        else:
            self.positions = {}

    def _save_state(self):
        try:
            with open(self.state_file, "w") as f:
                json.dump(self.positions, f, indent=4)
        except Exception as e:
            logger.error(f"Error saving HL state: {e}")

    async def get_funding_rate(self, coin="ETH"):
        """
        Fetches the current annualized funding rate for a coin.
        """
        try:
            contexts = self.info.meta_and_asset_ctxs()
            asset_ctxs = contexts[1]
            universe = contexts[0]['universe']
            
            coin_index = next((i for i, asset in enumerate(universe) if asset['name'] == coin), None)
            if coin_index is not None:
                ctx = asset_ctxs[coin_index]
                funding = float(ctx['funding'])
                annualized_funding = funding * 24 * 365
                return annualized_funding
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching funding rate: {e}")
            return 0.0
            
    async def get_account_summary(self):
        """
        Fetches account margin and position summary.
        """
        if not self.account_address and not self.private_key:
            return None
        addr = self.account_address or self.account.address
        try:
            return self.info.user_state(addr)
        except Exception as e:
            logger.error(f"Error fetching account summary: {e}")
            return None

    async def open_short(self, coin, size_eth, leverage):
        """
        Opens a short position on Hyperliquid with state tracking.
        """
        if not self.private_key:
            logger.error("Cannot open short: No private key provided")
            return False
            
        try:
            logger.info(f"Opening {leverage}x Short on {coin} for {size_eth} ETH")
            self.exchange.update_leverage(leverage, coin)
            
            # Market order short
            order_result = self.exchange.market_open(coin, False, size_eth, None, 0.01)
            
            if order_result["status"] == "ok":
                # Track position locally
                if coin not in self.positions:
                    self.positions[coin] = 0.0
                self.positions[coin] += float(size_eth)
                self._save_state()
                logger.info(f"Short opened successfully. Total {coin} short: {self.positions[coin]}")
                return True
            else:
                logger.error(f"Failed to open short: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Error opening short: {e}")
            return False
        
    async def close_short(self, coin, size_eth):
        """
        Closes a short position with state tracking.
        """
        if not self.private_key:
            logger.error("Cannot close short: No private key provided")
            return False
            
        try:
            logger.info(f"Closing Short on {coin} for {size_eth} ETH")
            order_result = self.exchange.market_close(coin, size_eth, None, 0.01)
            
            if order_result["status"] == "ok":
                if coin in self.positions:
                    self.positions[coin] = max(0.0, self.positions[coin] - float(size_eth))
                    self._save_state()
                logger.info(f"Short closed successfully. Remaining {coin} short: {self.positions.get(coin, 0.0)}")
                return True
            else:
                logger.error(f"Failed to close short: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Error closing short: {e}")
            return False

if __name__ == "__main__":
    hl = HyperliquidProvider()
    rate = asyncio.run(hl.get_funding_rate("ETH"))
    print(f"Annualized ETH Funding: {rate:.2%}")
