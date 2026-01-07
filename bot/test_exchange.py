import unittest
from unittest.mock import MagicMock, patch
from exchange_manager import ExchangeManager

# Created: 2025-12-28

class TestExchangeManager(unittest.TestCase):
    def setUp(self):
        # Patch load_dotenv and os.getenv to avoid real env dependency
        with patch('exchange_manager.load_dotenv'), \
             patch('os.getenv', side_effect=lambda k: 'mock_key' if 'API' in k or 'SECRET' in k else None):
            self.manager = ExchangeManager()
            self.manager.exchange = MagicMock()

    def test_get_market_price(self):
        self.manager.exchange.fetch_ticker.return_value = {'last': 2500.0}
        price = self.manager.get_market_price('ETH/USDT:USDT')
        self.assertEqual(price, 2500.0)
        self.manager.exchange.fetch_ticker.assert_called_with('ETH/USDT:USDT')

    def test_get_short_position_exists(self):
        # Mock CCXT position format
        self.manager.exchange.fetch_positions.return_value = [
            {
                'symbol': 'ETH/USDT:USDT',
                'contracts': 1.5,
                'unrealizedPnl': 50.0,
                'side': 'short'
            }
        ]
        contracts, pnl = self.manager.get_short_position('ETH/USDT:USDT')
        self.assertEqual(contracts, 1.5)
        self.assertEqual(pnl, 50.0)

    def test_get_short_position_none(self):
        self.manager.exchange.fetch_positions.return_value = []
        contracts, pnl = self.manager.get_short_position('ETH/USDT:USDT')
        self.assertEqual(contracts, 0.0)
        self.assertEqual(pnl, 0.0)

    def test_execute_short_success(self):
        self.manager.exchange.create_order.return_value = {'id': '12345'}
        result = self.manager.execute_short('ETH/USDT:USDT', 1.0)
        self.assertTrue(result)
        self.manager.exchange.create_order.assert_called_with(
            symbol='ETH/USDT:USDT',
            type='market',
            side='sell',
            amount=1.0
        )

    def test_execute_short_failure(self):
        self.manager.exchange.create_order.side_effect = Exception("API Error")
        result = self.manager.execute_short('ETH/USDT:USDT', 1.0)
        self.assertFalse(result)

    def test_execute_buy_success(self):
        self.manager.exchange.create_order.return_value = {'id': '67890'}
        result = self.manager.execute_buy('ETH/USDT:USDT', 0.5)
        self.assertTrue(result)
        self.manager.exchange.create_order.assert_called_with(
            symbol='ETH/USDT:USDT',
            type='market',
            side='buy',
            amount=0.5
        )

if __name__ == '__main__':
    unittest.main()
