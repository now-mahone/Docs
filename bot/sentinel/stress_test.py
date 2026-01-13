import unittest
from unittest.mock import MagicMock, patch
import sys
import os

# Add the bot directory to sys.path to allow imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from engine import HedgingEngine
from exchange_manager import ExchangeManager
from chain_manager import ChainManager
import time

# Created: 2026-01-12

class ChaosTestSuite(unittest.TestCase):
    """
    Stress tests the HedgingEngine under extreme market conditions.
    Simulates slippage, exchange downtime, and API rate limits.
    """

    def setUp(self):
        self.mock_exchange = MagicMock()
        self.mock_chain = MagicMock()
        self.mock_credits = MagicMock()
        
        # Mock the vault contract and its functions
        self.mock_vault = MagicMock()
        self.mock_chain.vault = self.mock_vault
        
        # Default mock behaviors
        self.mock_vault.functions.paused().call.return_value = False
        self.mock_chain.get_multi_chain_tvl.return_value = {"Base": 100.0}
        self.mock_chain.get_vault_assets.return_value = 100.0
        self.mock_exchange.get_market_price.return_value = 2500.0
        self.mock_exchange.get_short_position.return_value = (100.0, 0.0)
        self.mock_exchange.get_collateral_balance.return_value = 300000.0
        self.mock_exchange.exchange.fetch_ticker.return_value = {'fundingRate': 0.0001}
        
        self.engine = HedgingEngine(self.mock_exchange, self.mock_chain, self.mock_credits)
        # Inject mock exchanges for multi-venue
        self.engine.exchanges = {
            "binance": self.mock_exchange,
            "bybit": MagicMock(),
            "okx": MagicMock()
        }
        for ex in self.engine.exchanges.values():
            ex.get_short_position.return_value = (0.0, 0.0)
            ex.get_collateral_balance.return_value = 100000.0
            ex.exchange.fetch_ticker.return_value = {'fundingRate': 0.0001}

    def test_extreme_slippage_simulation(self):
        """Simulates a scenario where market price moves 10% between calculation and execution."""
        print("\n[CHAOS] Testing Extreme Slippage...")
        self.mock_chain.get_multi_chain_tvl.return_value = {"Base": 110.0} # Need to short 10 more
        self.mock_exchange.get_short_position.return_value = (100.0, 0.0)
        
        # Simulate price jump
        self.mock_exchange.get_market_price.return_value = 2750.0 # 10% jump
        
        self.engine.run_cycle(dry_run=False)
        
        # Verify rebalance was attempted despite price move
        self.assertTrue(any(ex.execute_short.called for ex in self.engine.exchanges.values()))

    def test_exchange_downtime(self):
        """Simulates one exchange being completely offline."""
        print("\n[CHAOS] Testing Exchange Downtime...")
        self.engine.exchanges["binance"].get_short_position.side_effect = Exception("Connection Timeout")
        
        # Should not crash the entire cycle
        try:
            self.engine.run_cycle(dry_run=False)
            print("[CHAOS] Engine handled downtime gracefully.")
        except Exception as e:
            self.fail(f"Engine crashed during exchange downtime: {e}")

    def test_api_rate_limits(self):
        """Simulates hitting API rate limits (429 errors)."""
        print("\n[CHAOS] Testing API Rate Limits...")
        self.mock_exchange.execute_short.side_effect = Exception("Rate limit exceeded (429)")
        
        self.mock_chain.get_multi_chain_tvl.return_value = {"Base": 150.0} # Large delta
        
        # Should log error but continue
        self.engine.run_cycle(dry_run=False)
        self.mock_exchange.execute_short.assert_called()

    def test_negative_funding_panic(self):
        """Simulates extreme negative funding triggering insurance fund draw."""
        print("\n[CHAOS] Testing Negative Funding Response...")
        # Ensure we have some short position to bleed from
        self.mock_exchange.get_short_position.return_value = (100.0, 0.0)
        
        for ex in self.engine.exchanges.values():
            ex.exchange.fetch_ticker.return_value = {'fundingRate': -0.005} # -0.5% per 8h (extreme)
            
        self.engine.run_cycle(dry_run=False)
        
        # Verify insurance fund draw was attempted
        self.mock_chain.draw_from_insurance_fund.assert_called()

    def test_vault_paused_circuit_breaker(self):
        """Ensures engine stops immediately if vault is paused."""
        print("\n[CHAOS] Testing Vault Paused Circuit Breaker...")
        self.mock_chain.vault.functions.paused().call.return_value = True
        
        with patch.object(self.engine, '_trigger_panic') as mock_panic:
            self.engine.run_cycle(dry_run=False)
            mock_panic.assert_called_with("Vault Paused")

if __name__ == "__main__":
    unittest.main()
