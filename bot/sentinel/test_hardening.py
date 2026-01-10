# Created: 2026-01-10
import unittest
from unittest.mock import MagicMock, patch
from bot.sentinel.risk_engine import RiskEngine

class TestSentinelHardening(unittest.TestCase):
    def setUp(self):
        self.mock_w3 = MagicMock()
        self.mock_w3.eth.get_transaction_count.return_value = 1
        self.mock_w3.eth.gas_price = 1000000000
        self.mock_w3.eth.chain_id = 8453
        self.private_key = "0x" + "1" * 64
        self.engine = RiskEngine(w3=self.mock_w3, private_key=self.private_key)

    def test_health_score_calculation(self):
        # Perfect neutrality
        data = {"net_delta": 0.0, "liq_onchain": 0.5, "liq_cex": 0.5}
        score = self.engine.calculate_health_score(data)
        self.assertEqual(score, 100.0)

        # High delta penalty
        data = {"net_delta": 0.10, "liq_onchain": 0.5, "liq_cex": 0.5}
        score = self.engine.calculate_health_score(data)
        self.assertTrue(score < 100.0)

    @patch("bot.sentinel.risk_engine.Web3.to_checksum_address")
    def test_circuit_breaker_trigger(self, mock_checksum):
        mock_checksum.side_effect = lambda x: x
        vault_address = "0x1234567890123456789012345678901234567890"
        
        # Mock the contract and build_transaction
        mock_contract = MagicMock()
        self.mock_w3.eth.contract.return_value = mock_contract
        # Ensure pause() returns a mock that has build_transaction
        mock_pause_call = mock_contract.functions.pause.return_value
        mock_pause_call.build_transaction.return_value = {'data': '0x'}
        
        # Mock signing and sending
        self.mock_w3.eth.account.sign_transaction.return_value.raw_transaction = b'raw_tx'
        self.mock_w3.eth.send_raw_transaction.return_value.hex.return_value = "0xhash"

        # Trigger critical risk
        critical_data = {
            "address": vault_address,
            "onchain_collateral": 100.0,
            "cex_short_position": -120.0, # 20% delta (limit is 5%)
            "liq_onchain": 0.05, # 5% distance (limit is 20%)
            "liq_cex": 0.05
        }
        
        profile = self.engine.analyze_vault(critical_data)
        
        # Verify health score is critical
        self.assertTrue(profile.health_score < self.engine.risk_thresholds["critical_health_score"])
        
        # Verify pause() was called
        mock_contract.functions.pause.assert_called()

if __name__ == "__main__":
    unittest.main()
