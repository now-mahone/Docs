from abc import ABC, abstractmethod
from typing import Tuple, Dict

class BaseExchange(ABC):
    """
    Abstract base class for all exchange adapters (CEX and DEX).
    Standardizes the interface for hedging and solvency reporting.
    """
    
    @abstractmethod
    def get_market_price(self, symbol: str) -> float:
        """Returns the current mark price for the symbol."""
        pass

    @abstractmethod
    def get_position(self, symbol: str) -> Tuple[float, float]:
        """
        Returns the current position for a symbol.
        Returns: (size, unrealized_pnl)
        """
        pass

    @abstractmethod
    def get_collateral_balance(self) -> float:
        """Returns the available collateral balance in USD/USDC."""
        pass

    @abstractmethod
    def get_total_equity(self) -> float:
        """
        Returns the total account equity (Collateral + Unrealized PnL).
        This is the core value used for solvency bridging.
        """
        pass

    @abstractmethod
    def execute_order(self, symbol: str, size: float, side: str) -> bool:
        """
        Executes a market order.
        side: 'buy' or 'sell'
        """
        pass

    @abstractmethod
    def get_funding_rate(self, symbol: str) -> float:
        """Returns the current hourly funding rate."""
        pass

    @abstractmethod
    def get_liquidation_price(self, symbol: str) -> float:
        """
        Returns the liquidation price for the current position of a symbol.
        Returns 0.0 if no position exists.
        """
        pass

    @abstractmethod
    def get_order_book(self, symbol: str) -> Dict:
        """
        Returns the order book for a symbol.
        """
        pass

