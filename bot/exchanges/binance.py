import os
import ccxt
from typing import Tuple
from loguru import logger
from exchanges.base import BaseExchange

class BinanceExchange(BaseExchange):
    def __init__(self):
        self.api_key = os.getenv("BINANCE_API_KEY")
        self.secret = os.getenv("BINANCE_SECRET")
        if not self.api_key or not self.secret:
            raise ValueError("Missing Binance API credentials")

        self.exchange = ccxt.binance({
            'apiKey': self.api_key,
            'secret': self.secret,
            'options': {
                'defaultType': 'future',
            },
            'enableRateLimit': True
        })
        logger.info("BinanceExchange initialized (Futures)")

    def get_market_price(self, symbol: str) -> float:
        try:
            # CCXT symbol format: ETH/USDT:USDT
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Binance Error market price: {e}")
            return 0.0

    def get_position(self, symbol: str) -> Tuple[float, float]:
        try:
            positions = self.exchange.fetch_positions([symbol])
            if not positions:
                return 0.0, 0.0
            pos = positions[0]
            size = float(pos['contracts'])
            side = pos['side']
            upnl = float(pos['unrealizedPnl'])
            # We want signed size for internal logic, but BaseExchange says (size, upnl)
            # HedgingEngine expects abs(size) and handles delta
            return size, upnl
        except Exception as e:
            logger.error(f"Binance Error position: {e}")
            return 0.0, 0.0

    def get_collateral_balance(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            # For Binance Futures, USDT is the main collateral
            return float(balance.get('USDT', {}).get('free', 0.0))
        except Exception as e:
            logger.error(f"Binance Error balance: {e}")
            return 0.0

    def get_total_equity(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            # totalMarginBalance in raw info
            return float(balance['info'].get('totalMarginBalance', 0.0))
        except Exception as e:
            logger.error(f"Binance Error equity: {e}")
            return 0.0

    def execute_order(self, symbol: str, size: float, side: str) -> bool:
        try:
            order = self.exchange.create_market_order(symbol, side, size)
            return order['status'] == 'closed' or order['status'] == 'ok'
        except Exception as e:
            logger.error(f"Binance Error execute: {e}")
            return False

    def get_funding_rate(self, symbol: str) -> float:
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            return float(funding['fundingRate'])
        except Exception as e:
            logger.error(f"Binance Error funding: {e}")
            return 0.0

    def get_liquidation_price(self, symbol: str) -> float:
        try:
            positions = self.exchange.fetch_positions([symbol])
            if not positions:
                return 0.0
            pos = positions[0]
            liq_price = pos.get('liquidationPrice')
            return float(liq_price) if liq_price else 0.0
        except Exception as e:
            logger.error(f"Binance Error liquidation price: {e}")
            return 0.0

    def get_order_book(self, symbol: str) -> dict:
        try:
            return self.exchange.fetch_order_book(symbol)
        except Exception as e:
            logger.error(f"Binance Error order book: {e}")
            return {"bids": [], "asks": []}

