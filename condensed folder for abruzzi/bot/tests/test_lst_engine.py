# bot/tests/test_lst_engine.py
import pytest
from unittest.mock import MagicMock, AsyncMock
from bot.solver.lst_capture_engine import LSTCaptureEngine

# Created: 2026-01-17

@pytest.fixture
def mock_cm():
    cm = MagicMock()
    cm.w3 = MagicMock()
    cm.account.address = "0x123"
    cm.private_key = "0xabc"
    cm.vault_address = "0xVault"
    return cm

@pytest.mark.asyncio
async def test_fetch_lst_rates(mock_cm):
    engine = LSTCaptureEngine(mock_cm)
    rates = await engine.fetch_lst_rates()
    assert "wstETH" in rates
    assert "cbETH" in rates
    assert rates["wstETH"] > 0

@pytest.mark.asyncio
async def test_update_shadow_yield(mock_cm):
    engine = LSTCaptureEngine(mock_cm)
    engine.hook = MagicMock()
    engine._get_erc20_balance = MagicMock(return_value=100 * 10**18)
    
    # Mock transaction send
    mock_cm.w3.eth.get_transaction_count.return_value = 1
    mock_cm.w3.eth.send_raw_transaction.return_value = b"tx_hash"
    
    await engine.update_shadow_yield()
    
    # Verify hook update was called
    assert engine.hook.functions.updateShadowYield.called
