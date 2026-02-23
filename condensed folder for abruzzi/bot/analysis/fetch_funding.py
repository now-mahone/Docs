import ccxt
import pandas as pd
from loguru import logger
from datetime import datetime, timedelta

def fetch_eth_funding_history():
    """
    Fetches the last 30 days of funding rate history for ETH/USDT:USDT on Binance.
    Calculates and prints the annualized yield.
    """
    try:
        # Initialize Binance exchange
        exchange = ccxt.binance()
        symbol = 'ETH/USDT:USDT'
        
        logger.info(f"Fetching funding rate history for {symbol}...")
        
        # Fetch funding rate history
        # Binance funding rates are usually every 8 hours (3 times a day)
        since = exchange.parse8601((datetime.now() - timedelta(days=30)).isoformat())
        funding_history = exchange.fetch_funding_rate_history(symbol, since=since, limit=1000)
        
        if not funding_history:
            logger.error("No funding history found.")
            return

        # Convert to DataFrame for analysis
        df = pd.DataFrame(funding_history)
        df['datetime'] = pd.to_datetime(df['timestamp'], unit='ms')
        
        # Calculate Average Funding Rate
        avg_funding_rate = df['fundingRate'].mean()
        
        # Annualize the yield
        # Funding is paid 3 times a day (every 8 hours)
        annualized_yield = avg_funding_rate * 3 * 365 * 100
        
        logger.success("Data fetched successfully!")
        print("-" * 40)
        print(f"Analysis Period: Last 30 Days")
        print(f"Average Funding Rate (8h): {avg_funding_rate:.6%}")
        print(f"Annualized Funding Yield (APY): {annualized_yield:.2f}%")
        print("-" * 40)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    fetch_eth_funding_history()
