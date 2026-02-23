import os
import sys
from loguru import logger
from dotenv import load_dotenv

# Add bot directory to path to import exchanges
sys.path.append(os.path.join(os.getcwd(), 'bot'))

from exchanges.hyperliquid import HyperliquidExchange

def main():
    load_dotenv('bot/.env')
    try:
        hl = HyperliquidExchange()
        status = hl.get_api_status()
        print(f"Status: {status['status']}")
        print(f"Address: {status['address']}")
        
        equity = hl.get_total_equity()
        withdrawable = hl.get_collateral_balance()
        
        print(f"Total Equity: ${equity}")
        print(f"Withdrawable: ${withdrawable}")
        
        user_state = hl.info.user_state(hl.address)
        print(f"User State: {user_state}")
        
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()