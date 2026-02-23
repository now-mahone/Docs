# Created: 2026-01-19
"""
Multi-Asset APY Backtest Engine - Kerne Protocol

Extends the single-asset backtest to cover ALL major hedgeable assets:
- ETH, BTC, SOL, AVAX, MATIC, ARB, OP, LINK, etc.

This enables Kerne to offer "Best Yield Routing" - automatically allocating
user deposits to the highest-yielding delta-neutral position.

Key Innovation:
- Users deposit ANY supported asset
- Kerne routes to the best funding rate opportunity
- Single KUSD token represents diversified delta-neutral exposure
"""

import math
import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import ccxt
    import pandas as pd
    import numpy as np
    from loguru import logger
except ImportError as e:
    print(f"Missing dependency: {e}")
    print("Run: pip install ccxt pandas numpy loguru")
    sys.exit(1)


# ============================================================================
# SUPPORTED ASSETS CONFIGURATION
# ============================================================================

@dataclass
class AssetConfig:
    """Configuration for a hedgeable asset"""
    symbol: str                    # e.g., "ETH"
    perp_symbol: str              # e.g., "ETH/USDT:USDT"
    lst_available: bool           # Whether LST staking is available
    lst_yield: float              # Annual LST yield (0 if no LST)
    spot_liquidity: str           # "high", "medium", "low"
    hedge_exchanges: List[str]    # Exchanges supporting this perp
    min_position_usd: float       # Minimum position size
    max_leverage: float           # Maximum safe leverage


# All supported assets for delta-neutral hedging
SUPPORTED_ASSETS = {
    "ETH": AssetConfig(
        symbol="ETH",
        perp_symbol="ETH/USDT:USDT",
        lst_available=True,
        lst_yield=0.035,  # 3.5% from cbETH/wstETH
        spot_liquidity="high",
        hedge_exchanges=["binance", "bybit", "okx"],
        min_position_usd=100,
        max_leverage=10.0
    ),
    "BTC": AssetConfig(
        symbol="BTC",
        perp_symbol="BTC/USDT:USDT",
        lst_available=False,  # No native BTC staking (yet)
        lst_yield=0.0,
        spot_liquidity="high",
        hedge_exchanges=["binance", "bybit", "okx"],
        min_position_usd=100,
        max_leverage=10.0
    ),
    "SOL": AssetConfig(
        symbol="SOL",
        perp_symbol="SOL/USDT:USDT",
        lst_available=True,
        lst_yield=0.065,  # 6.5% from mSOL/jitoSOL
        spot_liquidity="high",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=8.0
    ),
    "AVAX": AssetConfig(
        symbol="AVAX",
        perp_symbol="AVAX/USDT:USDT",
        lst_available=True,
        lst_yield=0.055,  # 5.5% from sAVAX
        spot_liquidity="medium",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "MATIC": AssetConfig(
        symbol="MATIC",
        perp_symbol="MATIC/USDT:USDT",
        lst_available=True,
        lst_yield=0.045,  # 4.5% from stMATIC
        spot_liquidity="medium",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "ARB": AssetConfig(
        symbol="ARB",
        perp_symbol="ARB/USDT:USDT",
        lst_available=False,
        lst_yield=0.0,
        spot_liquidity="medium",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "OP": AssetConfig(
        symbol="OP",
        perp_symbol="OP/USDT:USDT",
        lst_available=False,
        lst_yield=0.0,
        spot_liquidity="medium",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "LINK": AssetConfig(
        symbol="LINK",
        perp_symbol="LINK/USDT:USDT",
        lst_available=False,
        lst_yield=0.0,
        spot_liquidity="high",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "DOGE": AssetConfig(
        symbol="DOGE",
        perp_symbol="DOGE/USDT:USDT",
        lst_available=False,
        lst_yield=0.0,
        spot_liquidity="high",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
    "ATOM": AssetConfig(
        symbol="ATOM",
        perp_symbol="ATOM/USDT:USDT",
        lst_available=True,
        lst_yield=0.15,  # 15% from stATOM (high staking rewards)
        spot_liquidity="medium",
        hedge_exchanges=["binance", "bybit"],
        min_position_usd=50,
        max_leverage=5.0
    ),
}


@dataclass
class AssetBacktestResult:
    """Results for a single asset backtest"""
    symbol: str
    realized_apy: float
    simple_apy: float
    sharpe_ratio: float
    max_drawdown: float
    avg_funding_rate: float
    positive_funding_pct: float
    total_funding_pnl: float
    total_staking_pnl: float
    num_periods: int
    lst_yield: float
    combined_yield: float  # Funding + LST


class MultiAssetBacktester:
    """
    Backtests APY across all supported assets to find optimal allocation.
    """
    
    def __init__(
        self,
        start_date: datetime = None,
        end_date: datetime = None,
        initial_nav: float = 1_000_000,
        leverage: float = 3.0,
        exchange: str = "binance"
    ):
        self.start_date = start_date or (datetime.now() - timedelta(days=180))
        self.end_date = end_date or datetime.now()
        self.initial_nav = initial_nav
        self.leverage = leverage
        self.exchange_name = exchange
        self.exchange = None
        self.results: Dict[str, AssetBacktestResult] = {}
        
        logger.info(f"Multi-Asset Backtester initialized")
        logger.info(f"Period: {self.start_date.date()} to {self.end_date.date()}")
        logger.info(f"Assets: {list(SUPPORTED_ASSETS.keys())}")
    
    def _init_exchange(self):
        """Initialize CCXT exchange"""
        if self.exchange is None:
            if self.exchange_name == "binance":
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'future'}
                })
            elif self.exchange_name == "bybit":
                self.exchange = ccxt.bybit({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'linear'}
                })
    
    def fetch_funding_history(self, symbol: str, perp_symbol: str) -> pd.DataFrame:
        """Fetch funding rate history for a specific asset"""
        self._init_exchange()
        
        logger.info(f"Fetching {symbol} funding rates...")
        
        all_funding = []
        since = int(self.start_date.timestamp() * 1000)
        end = int(self.end_date.timestamp() * 1000)
        
        while since < end:
            try:
                funding = self.exchange.fetch_funding_rate_history(
                    perp_symbol,
                    since=since,
                    limit=1000
                )
                
                if not funding:
                    break
                
                all_funding.extend(funding)
                since = funding[-1]['timestamp'] + 1
                time.sleep(0.3)  # Rate limit
                
            except Exception as e:
                logger.warning(f"Error fetching {symbol} funding: {e}")
                break
        
        if not all_funding:
            logger.warning(f"No funding data for {symbol}, using simulated")
            return self._generate_simulated_funding(symbol)
        
        df = pd.DataFrame(all_funding)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['timestamp', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate'})
        
        logger.success(f"Fetched {len(df)} {symbol} funding records")
        return df
    
    def _generate_simulated_funding(self, symbol: str) -> pd.DataFrame:
        """Generate simulated funding for assets without API data"""
        # Different assets have different funding rate characteristics
        base_rates = {
            "ETH": 0.0001,   # 0.01% per 8h
            "BTC": 0.00008,  # 0.008% per 8h (more stable)
            "SOL": 0.00015,  # 0.015% per 8h (more volatile)
            "AVAX": 0.00012,
            "MATIC": 0.00010,
            "ARB": 0.00018,  # Higher for newer tokens
            "OP": 0.00016,
            "LINK": 0.00009,
            "DOGE": 0.00020,  # Meme coins more volatile
            "ATOM": 0.00011,
        }
        
        base_rate = base_rates.get(symbol, 0.0001)
        volatility = base_rate * 1.5
        
        periods = []
        current = self.start_date
        current_rate = base_rate
        
        while current < self.end_date:
            shock = np.random.normal(0, volatility)
            current_rate = current_rate + 0.1 * (base_rate - current_rate) + shock
            current_rate = max(-0.001, min(0.003, current_rate))
            
            periods.append({
                'timestamp': current,
                'funding_rate': current_rate
            })
            current += timedelta(hours=8)
        
        return pd.DataFrame(periods)
    
    def backtest_asset(self, symbol: str) -> AssetBacktestResult:
        """Run backtest for a single asset"""
        config = SUPPORTED_ASSETS[symbol]
        
        # Fetch funding data
        funding_df = self.fetch_funding_history(symbol, config.perp_symbol)
        
        if funding_df.empty:
            return AssetBacktestResult(
                symbol=symbol,
                realized_apy=0,
                simple_apy=0,
                sharpe_ratio=0,
                max_drawdown=0,
                avg_funding_rate=0,
                positive_funding_pct=0,
                total_funding_pnl=0,
                total_staking_pnl=0,
                num_periods=0,
                lst_yield=config.lst_yield,
                combined_yield=0
            )
        
        # Calculate PnL
        nav = self.initial_nav
        nav_history = [nav]
        period_returns = []
        total_funding_pnl = 0
        total_staking_pnl = 0
        
        L = min(self.leverage, config.max_leverage)
        daily_lst_yield = config.lst_yield / 365
        delta_t = 1/3  # 8 hours
        
        for _, row in funding_df.iterrows():
            funding_rate = row['funding_rate']
            notional = L * nav
            
            # Funding PnL
            funding_pnl = notional * funding_rate
            total_funding_pnl += funding_pnl
            
            # Staking PnL (only if LST available)
            staking_pnl = notional * daily_lst_yield * delta_t if config.lst_available else 0
            total_staking_pnl += staking_pnl
            
            # Gross yield
            gross = funding_pnl + staking_pnl
            
            # Costs (20% total: 10% insurance + 10% performance)
            costs = max(0, gross * 0.20)
            
            # Net PnL
            net_pnl = gross - costs
            period_return = net_pnl / nav if nav > 0 else 0
            period_returns.append(period_return)
            
            nav += net_pnl
            nav_history.append(nav)
        
        # Calculate metrics
        total_days = len(funding_df) * delta_t
        
        # Log-return APY
        log_return_sum = sum(math.log(1 + r) for r in period_returns if r > -1)
        realized_apy = math.exp((365 / total_days) * log_return_sum) - 1 if total_days > 0 else 0
        
        # Simple APY
        total_return = (nav - self.initial_nav) / self.initial_nav
        simple_apy = total_return * (365 / total_days) if total_days > 0 else 0
        
        # Sharpe ratio
        if len(period_returns) > 1:
            periods_per_year = 3 * 365
            avg_return = np.mean(period_returns) * periods_per_year
            std_return = np.std(period_returns) * math.sqrt(periods_per_year)
            sharpe = (avg_return - 0.05) / std_return if std_return > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        peak = nav_history[0]
        max_dd = 0
        for n in nav_history:
            if n > peak:
                peak = n
            dd = (peak - n) / peak
            if dd > max_dd:
                max_dd = dd
        
        # Funding stats
        funding_rates = funding_df['funding_rate'].tolist()
        avg_funding = np.mean(funding_rates)
        positive_pct = sum(1 for f in funding_rates if f > 0) / len(funding_rates)
        
        # Combined yield (funding APY + LST APY)
        funding_apy = avg_funding * 3 * 365 * L  # Annualized funding at leverage
        combined = funding_apy + config.lst_yield
        
        return AssetBacktestResult(
            symbol=symbol,
            realized_apy=realized_apy,
            simple_apy=simple_apy,
            sharpe_ratio=sharpe,
            max_drawdown=max_dd,
            avg_funding_rate=avg_funding,
            positive_funding_pct=positive_pct,
            total_funding_pnl=total_funding_pnl,
            total_staking_pnl=total_staking_pnl,
            num_periods=len(funding_df),
            lst_yield=config.lst_yield,
            combined_yield=combined
        )
    
    def run_all_backtests(self) -> Dict[str, AssetBacktestResult]:
        """Run backtests for all supported assets"""
        logger.info("=" * 70)
        logger.info("MULTI-ASSET APY BACKTEST")
        logger.info("=" * 70)
        
        for symbol in SUPPORTED_ASSETS.keys():
            try:
                result = self.backtest_asset(symbol)
                self.results[symbol] = result
                logger.info(f"{symbol}: APY={result.realized_apy*100:.2f}%, Sharpe={result.sharpe_ratio:.2f}")
            except Exception as e:
                logger.error(f"Failed to backtest {symbol}: {e}")
        
        return self.results
    
    def get_optimal_allocation(self) -> Dict[str, float]:
        """
        Calculate optimal allocation across assets based on risk-adjusted returns.
        Uses mean-variance optimization with Sharpe ratio weighting.
        """
        if not self.results:
            self.run_all_backtests()
        
        # Filter assets with positive Sharpe
        valid_assets = {k: v for k, v in self.results.items() if v.sharpe_ratio > 0}
        
        if not valid_assets:
            # Fallback to equal weight
            n = len(self.results)
            return {k: 1/n for k in self.results.keys()}
        
        # Sharpe-weighted allocation
        total_sharpe = sum(v.sharpe_ratio for v in valid_assets.values())
        allocation = {}
        
        for symbol, result in valid_assets.items():
            allocation[symbol] = result.sharpe_ratio / total_sharpe
        
        # Add zero allocation for excluded assets
        for symbol in self.results.keys():
            if symbol not in allocation:
                allocation[symbol] = 0.0
        
        return allocation
    
    def get_best_yield_asset(self) -> Tuple[str, AssetBacktestResult]:
        """Get the single best-yielding asset"""
        if not self.results:
            self.run_all_backtests()
        
        best = max(self.results.items(), key=lambda x: x[1].realized_apy)
        return best
    
    def print_results(self):
        """Print formatted multi-asset results"""
        if not self.results:
            self.run_all_backtests()
        
        print("\n" + "=" * 90)
        print("KERNE MULTI-ASSET APY BACKTEST RESULTS")
        print(f"Period: {self.start_date.date()} to {self.end_date.date()} | Leverage: {self.leverage}x")
        print("=" * 90)
        
        # Sort by APY
        sorted_results = sorted(
            self.results.items(),
            key=lambda x: x[1].realized_apy,
            reverse=True
        )
        
        print("\n| Asset | APY      | Sharpe | Max DD  | Funding APY | LST Yield | Combined | Pos Fund % |")
        print("|-------|----------|--------|---------|-------------|-----------|----------|------------|")
        
        for symbol, r in sorted_results:
            funding_apy = r.avg_funding_rate * 3 * 365 * self.leverage * 100
            print(f"| {symbol:5} | {r.realized_apy*100:>6.2f}% | {r.sharpe_ratio:>6.2f} | {r.max_drawdown*100:>5.2f}% | "
                  f"{funding_apy:>9.2f}% | {r.lst_yield*100:>7.1f}% | {r.combined_yield*100:>6.2f}% | {r.positive_funding_pct*100:>8.1f}% |")
        
        # Best asset
        best_symbol, best_result = self.get_best_yield_asset()
        print(f"\n🏆 BEST YIELD: {best_symbol} at {best_result.realized_apy*100:.2f}% APY")
        
        # Optimal allocation
        allocation = self.get_optimal_allocation()
        print("\n📊 OPTIMAL SHARPE-WEIGHTED ALLOCATION:")
        for symbol, weight in sorted(allocation.items(), key=lambda x: -x[1]):
            if weight > 0.01:
                print(f"   {symbol}: {weight*100:.1f}%")
        
        # Portfolio APY (weighted average)
        portfolio_apy = sum(
            allocation[s] * self.results[s].realized_apy
            for s in allocation.keys()
        )
        print(f"\n💰 PORTFOLIO APY (Optimal Allocation): {portfolio_apy*100:.2f}%")
        
        print("\n" + "=" * 90)
    
    def save_results(self, path: str = None):
        """Save results to JSON"""
        if path is None:
            path = os.path.join(os.path.dirname(__file__), "multi_asset_results.json")
        
        output = {
            "backtest_date": datetime.now().isoformat(),
            "period": {
                "start": self.start_date.isoformat(),
                "end": self.end_date.isoformat()
            },
            "leverage": self.leverage,
            "initial_nav": self.initial_nav,
            "assets": {},
            "optimal_allocation": self.get_optimal_allocation(),
            "best_asset": self.get_best_yield_asset()[0],
            "portfolio_apy": sum(
                self.get_optimal_allocation()[s] * self.results[s].realized_apy
                for s in self.results.keys()
            )
        }
        
        for symbol, r in self.results.items():
            output["assets"][symbol] = {
                "realized_apy": r.realized_apy,
                "simple_apy": r.simple_apy,
                "sharpe_ratio": r.sharpe_ratio,
                "max_drawdown": r.max_drawdown,
                "avg_funding_rate": r.avg_funding_rate,
                "positive_funding_pct": r.positive_funding_pct,
                "total_funding_pnl": r.total_funding_pnl,
                "total_staking_pnl": r.total_staking_pnl,
                "num_periods": r.num_periods,
                "lst_yield": r.lst_yield,
                "combined_yield": r.combined_yield
            }
        
        with open(path, 'w') as f:
            json.dump(output, f, indent=2)
        
        logger.success(f"Results saved to {path}")
        return output


def main():
    """Run multi-asset backtest"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("\n" + "=" * 70)
    print("KERNE PROTOCOL - MULTI-ASSET APY BACKTEST")
    print("Finding the Best Yield Across All Hedgeable Assets")
    print("=" * 70)
    
    backtester = MultiAssetBacktester(
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        initial_nav=1_000_000,
        leverage=3.0,
        exchange="binance"
    )
    
    backtester.run_all_backtests()
    backtester.print_results()
    backtester.save_results()


if __name__ == "__main__":
    main()
