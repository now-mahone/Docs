import os
import ccxt
from typing import Tuple
from loguru import logger
from exchanges.base import BaseExchange

class BybitExchange(BaseExchange):
    def __init__(self, use_linear: bool = True):
        self.api_key = os.getenv("BYBIT_API_KEY")
        self.secret = os.getenv("BYBIT_SECRET")
        if not self.api_key or not self.secret:
            raise ValueError("Missing Bybit API credentials")

        self.exchange = ccxt.bybit({
            'apiKey': self.api_key,
            'secret': self.secret,
            'options': {
                'defaultType': 'linear' if use_linear else 'inverse',
            },
            'enableRateLimit': True
        })
        logger.info(f"BybitExchange initialized ({'Linear' if use_linear else 'Inverse'})")

    def get_market_price(self, symbol: str) -> float:
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            return float(ticker['last'])
        except Exception as e:
            logger.error(f"Bybit Error market price: {e}")
            return 0.0

    def get_position(self, symbol: str) -> Tuple[float, float]:
        try:
            positions = self.exchange.fetch_positions([symbol])
            if not positions:
                return 0.0, 0.0
            pos = positions[0]
            size = float(pos['contracts'])
            upnl = float(pos['unrealizedPnl'])
            return size, upnl
        except Exception as e:
            logger.error(f"Bybit Error position: {e}")
            return 0.0, 0.0

    def get_collateral_balance(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            # In Bybit V5, 'total' usually contains equity
            return float(balance.get('USDT', {}).get('free', 0.0))
        except Exception as e:
            logger.error(f"Bybit Error balance: {e}")
            return 0.0

    def get_total_equity(self) -> float:
        try:
            balance = self.exchange.fetch_balance()
            # For Linear, USDT is the key. For Unified, it might be different.
            # CCXT unified balance['total'] usually includes equity for futures.
            return float(balance['total'].get('USDT', 0.0))
        except Exception as e:
            logger.error(f"Bybit Error equity: {e}")
            return 0.0

    def execute_order(self, symbol: str, size: float, side: str) -> bool:
        try:
            order = self.exchange.create_market_order(symbol, side, size)
            return order['status'] == 'closed' or order['status'] == 'ok'
        except Exception as e:
            logger.error(f"Bybit Error execute: {e}")
            return False

    def get_funding_rate(self, symbol: str) -> float:
        try:
            funding = self.exchange.fetch_funding_rate(symbol)
            return float(funding['fundingRate'])
        except Exception as e:
            logger.error(f"Bybit Error funding: {e}")
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
            logger.error(f"Bybit Error liquidation price: {e}")
            return 0.0
