import ccxt
import os
import time
from dotenv import load_dotenv
from loguru import logger

# Created: 2025-12-28

class ExchangeManager:
    """
    Handles interactions with Centralized Exchanges (CEX) via CCXT.
    Focuses on managing delta-neutral short positions across multiple venues.
    """
    def __init__(self, exchange_id: str = "binance"):
        load_dotenv()
        
        self.exchange_id = exchange_id
        api_key = os.getenv(f"{exchange_id.upper()}_API_KEY") or os.getenv("CEX_API_KEY")
        secret = os.getenv(f"{exchange_id.upper()}_SECRET") or os.getenv("CEX_SECRET")
        
        exchange_class = getattr(ccxt, exchange_id)
        
        config = {
            'apiKey': api_key,
            'secret': secret,
            'enableRateLimit': True,
        }

        if exchange_id == 'binance':
            config['options'] = {'defaultType': 'future'}
        elif exchange_id == 'bybit':
            config['options'] = {'defaultType': 'linear'}
        elif exchange_id == 'okx':
            config['options'] = {'defaultType': 'swap'}

        self.exchange = exchange_class(config)
        logger.info(f"ExchangeManager initialized for {exchange_id}.")

    def get_market_price(self, symbol: str) -> float:
        """
        Fetches the current Mark Price for a given symbol.
        """
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            # For futures, markPrice is often more relevant for PnL
            price = ticker.get('last') or ticker.get('markPrice')
            return float(price)
        except Exception as e:
            logger.error(f"Error fetching market price for {symbol}: {e}")
            raise

    def get_short_position(self, symbol: str):
        """
        Fetches the current open position for a symbol.
        Returns (contracts, unrealizedPnl).
        """
        try:
            positions = self.exchange.fetch_positions([symbol])
            for pos in positions:
                if pos['symbol'] == symbol:
                    contracts = float(pos['contracts'])
                    unrealized_pnl = float(pos['unrealizedPnl'])
                    # Ensure it's a short position (negative side in some APIs, 
                    # but CCXT normalizes 'side')
                    if pos['side'] == 'short' or contracts < 0:
                        return abs(contracts), unrealized_pnl
            
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
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side='sell',
                amount=amount_eth
            )
            logger.success(f"Short order executed: {order['id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute short on {symbol}: {e}")
            return False

    def execute_buy(self, symbol: str, amount_eth: float) -> bool:
        """
        Places a MARKET BUY order to close or reduce a short position.
        """
        try:
            logger.info(f"Executing BUY on {symbol} for {amount_eth} ETH")
            order = self.exchange.create_order(
                symbol=symbol,
                type='market',
                side='buy',
                amount=amount_eth
            )
            logger.success(f"Buy order executed: {order['id']}")
            return True
        except Exception as e:
            logger.error(f"Failed to execute buy on {symbol}: {e}")
            return False

    def get_collateral_balance(self, asset: str = 'USDT') -> float:
        """
        Fetches the available collateral balance in the futures wallet.
        """
        try:
            balance = self.exchange.fetch_balance()
            # CCXT balance format for futures can vary, but 'total' usually has the sum
            return float(balance['total'].get(asset, 0.0))
        except Exception as e:
            logger.error(f"Error fetching collateral balance for {asset}: {e}")
            return 0.0

    def execute_limit_order(self, symbol: str, side: str, amount: float) -> bool:
        """
        Places a LIMIT order with 'postOnly' to ensure we are a Maker.
        If not filled within 30 seconds, it cancels and replaces the order.
        """
        try:
            logger.info(f"Executing LIMIT {side.upper()} on {symbol} for {amount} units (Maker Only)")
            
            # Get current market price to set limit price
            price = self.get_market_price(symbol)
            
            # Adjust price slightly to be at the top of the book (aggressive maker)
            # For sell, we want to be slightly above or at best bid
            # For buy, we want to be slightly below or at best ask
            # For simplicity, we'll use the current mark price
            
            order = self.exchange.create_order(
                symbol=symbol,
                type='limit',
                side=side,
                amount=amount,
                price=price,
                params={'postOnly': True}
            )
            
            order_id = order['id']
            logger.info(f"Limit order placed: {order_id} at {price}")
            
            # Wait and monitor
            start_time = time.time()
            while time.time() - start_time < 30:
                status = self.exchange.fetch_order_status(order_id, symbol)
                if status == 'closed':
                    logger.success(f"Limit order {order_id} filled.")
                    return True
                if status == 'canceled':
                    logger.warning(f"Limit order {order_id} was canceled (likely postOnly failed).")
                    return False
                time.sleep(5)
            
            # Timeout reached, cancel order
            logger.warning(f"Limit order {order_id} timed out. Canceling...")
            self.exchange.cancel_order(order_id, symbol)
            return False
            
        except Exception as e:
            logger.error(f"Error in execute_limit_order: {e}")
            return False
