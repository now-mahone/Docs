import asyncio
import os
import sys
import json
import time
from unittest.mock import MagicMock, patch

# Add bot directory to path
sys.path.append(os.path.join(os.getcwd(), 'bot'))

from sentinel.risk_engine import RiskEngine

async def test_pnl_breaker():
    print("Testing PnL Breaker...")
    
    # Mock Web3 and ChainManager
    mock_w3 = MagicMock()
    mock_w3.eth.chain_id = 1
    mock_w3.eth.gas_price = 10**9
    
    # Initialize RiskEngine with a temporary state file
    state_path = "bot/data/test_pnl_state.json"
    if os.path.exists(state_path): os.remove(state_path)
    
    engine = RiskEngine(w3=mock_w3, private_key="0x" + "1"*64, pnl_state_path=state_path)
    
    # 1. Initial equity
    vault_data = {
        "address": "0x1234567890123456789012345678901234567890",
        "onchain_collateral": 100,
        "cex_short_position": -100,
        "available_margin_usd": 100000,
        "current_price": 2500,
        "liq_onchain": 0.5,
        "liq_cex": 0.3,
        "symbol": "ETH/USDT"
    }
    
    print("Step 1: Setting initial equity to $100,000")
    await engine.analyze_vault(vault_data)
    assert engine.pnl_state["starting_equity"] == 100000
    
    # 2. Trigger Hard Loss Limit ($50k)
    print("Step 2: Setting equity to $40,000 (Loss of $60,000)")
    vault_data["available_margin_usd"] = 40000
    
    try:
        with patch.object(engine, 'trigger_circuit_breaker', return_value=asyncio.Future()) as mock_trigger:
            mock_trigger.return_value.set_result(None)
            await engine.analyze_vault(vault_data)
            if mock_trigger.call_count > 0:
                print(f"Success: Circuit breaker triggered {mock_trigger.call_count} times")
                for i, call in enumerate(mock_trigger.call_args_list):
                    print(f"  Call {i+1} reason: {call[0][1]}")
            else:
                print("Failure: Circuit breaker NOT triggered")
    except Exception as e:
        print(f"Error in Step 2: {e}")
        import traceback
        traceback.print_exc()

    # 3. Trigger Max Drawdown (2%)
    print("Step 3: Resetting and testing 2% drawdown")
    engine.pnl_state["starting_equity"] = 100000
    engine.pnl_state["daily_realized_pnl"] = 0.0
    vault_data["available_margin_usd"] = 97000 # 3% loss
    
    with patch.object(engine, 'trigger_circuit_breaker', return_value=asyncio.Future()) as mock_trigger:
        mock_trigger.return_value.set_result(None)
        await engine.analyze_vault(vault_data)
        mock_trigger.assert_called_once()
        print(f"Success: Circuit breaker triggered with reason: {mock_trigger.call_args[0][1]}")

    if os.path.exists(state_path): os.remove(state_path)
    print("PnL Breaker Test Passed!")

if __name__ == "__main__":
    asyncio.run(test_pnl_breaker())
