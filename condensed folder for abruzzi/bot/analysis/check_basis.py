import requests
import pandas as pd
import numpy as np
from loguru import logger
import time

def check_basis_risk():
    """
    Fetches the last 90 days of price data for stETH and ETH from CoinGecko.
    Calculates the exchange rate, max drawdown, and correlation.
    """
    try:
        logger.info("Fetching price data from CoinGecko...")
        
        # CoinGecko API endpoints
        # stETH: staked-ether
        # ETH: ethereum
        steth_url = "https://api.coingecko.com/api/v3/coins/staked-ether/market_chart?vs_currency=usd&days=90&interval=daily"
        eth_url = "https://api.coingecko.com/api/v3/coins/ethereum/market_chart?vs_currency=usd&days=90&interval=daily"
        
        steth_resp = requests.get(steth_url).json()
        time.sleep(1) # Rate limiting
        eth_resp = requests.get(eth_url).json()
        
        if 'prices' not in steth_resp or 'prices' not in eth_resp:
            logger.error("Failed to fetch data from CoinGecko. Check API limits.")
            return

        steth_prices = pd.DataFrame(steth_resp['prices'], columns=['timestamp', 'steth_price'])
        eth_prices = pd.DataFrame(eth_resp['prices'], columns=['timestamp', 'eth_price'])
        
        # Merge on timestamp
        df = pd.merge(steth_prices, eth_prices, on='timestamp')
        
        # Calculate exchange rate
        df['ratio'] = df['steth_price'] / df['eth_price']
        
        # Calculate Max Deviation (Drawdown from 1.0)
        # Since stETH should be >= ETH (accruing yield), we look for dips below 1.0 or significant drops
        max_ratio = df['ratio'].max()
        min_ratio = df['ratio'].min()
        max_deviation = (1.0 - min_ratio) * 100
        
        # Calculate Correlation
        correlation = df['steth_price'].corr(df['eth_price'])
        
        logger.success("Analysis complete!")
        print("-" * 40)
        print(f"Analysis Period: Last 90 Days")
        print(f"Average Ratio (stETH/ETH): {df['ratio'].mean():.4f}")
        print(f"Max Deviation from Parity: {max_deviation:.2f}%")
        print(f"Correlation Coefficient: {correlation:.6f}")
        print("-" * 40)
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")

if __name__ == "__main__":
    check_basis_risk()
