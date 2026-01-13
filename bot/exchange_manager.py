import os
import time
from dotenv import load_dotenv
from loguru import logger
from hyperliquid.utils import constants
from hyperliquid.exchange import Exchange
from hyperliquid.info import Info
import eth_account

# Created: 2025-12-28
# Updated: 2026-01-13 (Hyperliquid Integration)

class ExchangeManager:
    """
    Handles interactions with Hyperliquid (DeFi Perp) for delta-neutral hedging.
    """
    def __init__(self, use_testnet: bool = False):
        load_dotenv()
        
        self.private_key = os.getenv("HYPERLIQUID_PRIVATE_KEY") or os.getenv("STRATEGIST_PRIVATE_KEY")
        if not self.private_key:
            logger.error("HYPERLIQUID_PRIVATE_KEY not found in .env")
            raise ValueError("Missing Hyperliquid Private Key")

        self.account = eth_account.Account.from_key(self.private_key)
        self.address = self.account.address
        
        self.base_url = constants.TESTNET_API_URL if use_testnet else constants.MAINNET_API_URL
        self.info = Info(self.base_url, skip_ws=True)
        self.exchange = Exchange(self.account, self.base_url)
        
        logger.info(f"ExchangeManager initialized for Hyperliquid. Address: {self.address}")

    def get_market_price(self, symbol: str = "ETH") -> float:
        """
        Fetches the current Mark Price for a given symbol on Hyperliquid.
        """
        try:
            all_mids = self.info.all_mids()
            price = all_mids.get(symbol)
            if not price:
                # Try to find the symbol in the list if not exact match
                logger.warning(f"Symbol {symbol} not found in mids, searching...")
                return 0.0
            return float(price)
        except Exception as e:
            logger.error(f"Error fetching market price for {symbol}: {e}")
            return 0.0

    def get_short_position(self, symbol: str = "ETH"):
        """
        Fetches the current open position for a symbol.
        Returns (contracts, unrealizedPnl).
        """
        try:
            user_state = self.info.user_state(self.address)
            positions = user_state.get("assetPositions", [])
            
            for pos_wrapper in positions:
                pos = pos_wrapper["position"]
                if pos["coin"] == symbol:
                    szi = float(pos["szi"]) # Signed size
                    unrealized_pnl = float(pos["unrealizedPnl"])
                    
                    # If szi is negative, it's a short
                    if szi < 0:
                        return abs(szi), unrealized_pnl
            
            return 0.0, 0.0
        except Exception as e:
            logger.error(f"Error fetching position for {symbol}: {e}")
            return 0.0, 0.0

    def execute_short(self, symbol: str, amount_eth: float) -> bool:
        """
        Places a MARKET SELL order to open or increase a short position.
        """
        try:
            logger.info(f"Executing SHORT on {symbol} for {amount_eth} ETH")
            # Hyperliquid uses 'is_buy=False' for sell
            # We use a large slippage (e.g. 5%) for market orders to ensure fill
            price = self.get_market_price(symbol)
            slippage_price = price * 0.95 
            
            order_result = self.exchange.market_open(
                name=symbol,
                is_buy=False,
                sz=amount_eth,
                px=slippage_price,
                slippage=0.05
            )
            
            if order_result["status"] == "ok":
                logger.success(f"Short order executed on Hyperliquid.")
                return True
            else:
                logger.error(f"Hyperliquid order failed: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Failed to execute short on {symbol}: {e}")
            return False

    def execute_buy(self, symbol: str, amount_eth: float) -> bool:
        """
        Places a MARKET BUY order to close or reduce a short position.
        """
        try:
            logger.info(f"Executing BUY on {symbol} for {amount_eth} ETH")
            price = self.get_market_price(symbol)
            slippage_price = price * 1.05
            
            order_result = self.exchange.market_open(
                name=symbol,
                is_buy=True,
                sz=amount_eth,
                px=slippage_price,
                slippage=0.05
            )
            
            if order_result["status"] == "ok":
                logger.success(f"Buy order executed on Hyperliquid.")
                return True
            else:
                logger.error(f"Hyperliquid order failed: {order_result}")
                return False
        except Exception as e:
            logger.error(f"Failed to execute buy on {symbol}: {e}")
            return False

    def get_collateral_balance(self) -> float:
        """
        Fetches the available USDC margin balance on Hyperliquid.
        """
        try:
            user_state = self.info.user_state(self.address)
            return float(user_state.get("withdrawable", 0.0))
        except Exception as e:
            logger.error(f"Error fetching collateral balance: {e}")
            return 0.0

    def get_funding_rate(self, symbol: str = "ETH") -> float:
        """
        Fetches the current hourly funding rate for a symbol.
        """
        try:
            meta = self.info.meta_and_asset_ctxs()
            # meta[0] is universe, meta[1] is asset contexts
            universe = meta[0]["universe"]
            asset_ctxs = meta[1]
            
            for i, asset in enumerate(universe):
                if asset["name"] == symbol:
                    funding = float(asset_ctxs[i]["funding"])
                    return funding
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching funding rate for {symbol}: {e}")
            return 0.0
