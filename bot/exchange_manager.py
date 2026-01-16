import os
from typing import List, Dict
from loguru import logger
from exchanges.base import BaseExchange
from exchanges.hyperliquid import HyperliquidExchange
from exchanges.binance import BinanceExchange
from exchanges.bybit import BybitExchange

class ExchangeManager:
    """
    Factory and Aggregator for multiple exchanges.
    Manages a collection of BaseExchange implementations.
    """
    def __init__(self, use_testnet: bool = False):
        self.exchanges: Dict[str, BaseExchange] = {}
        
        # Initialize Hyperliquid (Primary)
        try:
            self.exchanges["hyperliquid"] = HyperliquidExchange(use_testnet)
        except Exception as e:
            logger.warning(f"Could not initialize Hyperliquid: {e}")

        # Initialize Binance (Optional)
        if os.getenv("BINANCE_API_KEY"):
            try:
                self.exchanges["binance"] = BinanceExchange()
            except Exception as e:
                logger.warning(f"Could not initialize Binance: {e}")

        # Initialize Bybit (Optional)
        if os.getenv("BYBIT_API_KEY"):
            try:
                self.exchanges["bybit"] = BybitExchange()
            except Exception as e:
                logger.warning(f"Could not initialize Bybit: {e}")

        if not self.exchanges:
            logger.error("No exchanges initialized!")
            raise ValueError("No valid exchange configurations found")

    def get_exchange(self, name: str) -> BaseExchange:
        return self.exchanges.get(name.lower())

    def get_market_price(self, symbol: str = "ETH") -> float:
        """Returns the average market price across all active exchanges."""
        prices = []
        for name, ex in self.exchanges.items():
            # Handle symbol mapping if needed (e.g. ETH vs ETH/USDT:USDT)
            ex_symbol = self._map_symbol(name, symbol)
            price = ex.get_market_price(ex_symbol)
            if price > 0:
                prices.append(price)
        
        return sum(prices) / len(prices) if prices else 0.0

    def get_total_equity(self) -> float:
        """Returns the aggregate equity (USD) across all exchanges."""
        total = 0.0
        for ex in self.exchanges.values():
            total += ex.get_total_equity()
        return total

    def get_aggregate_position(self, symbol: str = "ETH") -> Dict:
        """Returns the total short position and aggregate unrealized PnL."""
        total_size = 0.0
        total_upnl = 0.0
        
        for name, ex in self.exchanges.items():
            ex_symbol = self._map_symbol(name, symbol)
            size, upnl = ex.get_position(ex_symbol)
            total_size += size
            total_upnl += upnl
            
        return {
            "size": total_size,
            "upnl": total_upnl
        }

    def execute_short(self, symbol: str, amount_eth: float, preferred_exchange: str = "hyperliquid") -> bool:
        """Executes a short on the preferred exchange or the one with most collateral."""
        ex = self.get_exchange(preferred_exchange) or list(self.exchanges.values())[0]
        ex_symbol = self._map_symbol(preferred_exchange, symbol)
        return ex.execute_order(ex_symbol, amount_eth, "sell")

    def execute_buy(self, symbol: str, amount_eth: float, preferred_exchange: str = "hyperliquid") -> bool:
        """Executes a buy on the preferred exchange."""
        ex = self.get_exchange(preferred_exchange) or list(self.exchanges.values())[0]
        ex_symbol = self._map_symbol(preferred_exchange, symbol)
        return ex.execute_order(ex_symbol, amount_eth, "buy")

    def get_funding_rate(self, symbol: str = "ETH") -> float:
        """Returns the average funding rate."""
        rates = []
        for name, ex in self.exchanges.items():
            ex_symbol = self._map_symbol(name, symbol)
            rate = ex.get_funding_rate(ex_symbol)
            rates.append(rate)
        return sum(rates) / len(rates) if rates else 0.0

    def _map_symbol(self, exchange_name: str, symbol: str) -> str:
        """Maps generic symbols like 'ETH' to exchange-specific formats."""
        if exchange_name == "hyperliquid":
            return symbol
        if exchange_name in ["binance", "bybit"]:
            return f"{symbol}/USDT:USDT"
        return symbol
