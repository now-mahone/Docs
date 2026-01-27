import os
from typing import List, Dict
from loguru import logger
from exchanges.base import BaseExchange
from exchanges.hyperliquid import HyperliquidExchange
from exchanges.binance import BinanceExchange
from exchanges.bybit import BybitExchange
from router import SmartRouter

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

        self.router = SmartRouter(self)

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

    def execute_short(self, symbol: str, amount_eth: float) -> bool:
        """Executes a short using the SmartRouter for optimal distribution."""
        distribution = self.router.calculate_distribution(symbol, amount_eth, "sell")
        success = True
        for name, amount in distribution.items():
            if amount < 0.001: continue
            ex = self.exchanges[name]
            ex_symbol = self._map_symbol(name, symbol)
            if not ex.execute_order(ex_symbol, amount, "sell"):
                logger.error(f"Failed to execute short on {name}")
                success = False
        return success

    def execute_buy(self, symbol: str, amount_eth: float) -> bool:
        """Executes a buy using the SmartRouter for optimal distribution."""
        distribution = self.router.calculate_distribution(symbol, amount_eth, "buy")
        success = True
        for name, amount in distribution.items():
            if amount < 0.001: continue
            ex = self.exchanges[name]
            ex_symbol = self._map_symbol(name, symbol)
            if not ex.execute_order(ex_symbol, amount, "buy"):
                logger.error(f"Failed to execute buy on {name}")
                success = False
        return success


    def get_funding_rate(self, symbol: str = "ETH") -> float:
        """Returns the average funding rate."""
        rates = []
        for name, ex in self.exchanges.items():
            ex_symbol = self._map_symbol(name, symbol)
            rate = ex.get_funding_rate(ex_symbol)
            rates.append(rate)
        return sum(rates) / len(rates) if rates else 0.0

    def get_liquidation_price(self, symbol: str = "ETH") -> float:
        """Returns the highest (worst-case) liquidation price across all active exchanges."""
        liq_prices = []
        for name, ex in self.exchanges.items():
            ex_symbol = self._map_symbol(name, symbol)
            liq_price = ex.get_liquidation_price(ex_symbol)
            if liq_price > 0:
                liq_prices.append(liq_price)
        
        # For short positions, higher liquidation price is better (further away)
        # But we want to be conservative, so we might want the lowest one? 
        # Wait, if I'm short, I get liquidated if price goes UP.
        # So liquidation price is ABOVE current price.
        # The lowest liquidation price is the most dangerous one.
        return min(liq_prices) if liq_prices else 0.0

    def get_order_book(self, symbol: str = "ETH") -> Dict[str, Dict]:
        """Returns order books from all active exchanges."""
        books = {}
        for name, ex in self.exchanges.items():
            ex_symbol = self._map_symbol(name, symbol)
            books[name] = ex.get_order_book(ex_symbol)
        return books

    def execute_twap_order(self, symbol: str, amount_eth: float, side: str, duration_mins: int = 10):
        """
        Executes a Time-Weighted Average Price (TWAP) order.
        Splits the total amount into multiple smaller orders over time.
        """
        import asyncio
        async def _twap():
            num_slices = max(5, duration_mins // 2)
            slice_amount = amount_eth / num_slices
            interval = (duration_mins * 60) / num_slices
            
            logger.info(f"⏳ Executing TWAP {side} for {amount_eth} {symbol} over {duration_mins} mins ({num_slices} slices)")
            
            for i in range(num_slices):
                if side.lower() == 'buy':
                    self.execute_buy(symbol, slice_amount)
                else:
                    self.execute_short(symbol, slice_amount)
                
                if i < num_slices - 1:
                    await asyncio.sleep(interval)
            
            logger.success(f"✅ TWAP {side} completed.")

        # Trigger as background task if in async loop, otherwise run sync (not ideal)
        try:
            loop = asyncio.get_running_loop()
            loop.create_task(_twap())
        except RuntimeError:
            # Fallback for sync contexts (running it sync here would block)
            logger.warning("TWAP called outside of event loop, execution might be delayed or blocked.")
            # In a real sync bot, we'd use a thread or similar


    def _map_symbol(self, exchange_name: str, symbol: str) -> str:
        """Maps generic symbols like 'ETH' to exchange-specific formats."""
        if exchange_name == "hyperliquid":
            return symbol
        if exchange_name in ["binance", "bybit"]:
            return f"{symbol}/USDT:USDT"
        return symbol
