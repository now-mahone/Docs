# Created: 2026-01-19
"""
APY Backtest Engine - Kerne Protocol

Implements the OpenAI APY framework to backtest 6 months of historical data.
Uses real funding rates from Binance/Bybit and LST yields to calculate
what Kerne's realized APY would have been.

Formula:
    r_k = (P_fund + P_stake + P_spr - C_k) / E_{k-1}
    APY = exp((365/Σ Δt_k) × Σ ln(1+r_k)) - 1
"""

import math
import json
import os
import sys
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import time

# Add parent directory to path for imports
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


@dataclass
class PeriodPnL:
    """PnL breakdown for a single period (8h funding interval)"""
    timestamp: datetime
    delta_t_days: float  # Period length in days (typically 1/3 day = 8h)
    
    # PnL Components (in USD)
    funding_pnl: float = 0.0      # P_fund: Perp funding received
    staking_pnl: float = 0.0      # P_stake: LST staking rewards
    spread_pnl: float = 0.0       # P_spr: Trading spread capture
    
    # Costs (in USD)
    trading_fees: float = 0.0     # CEX trading fees
    gas_costs: float = 0.0        # On-chain gas
    slippage: float = 0.0         # Execution slippage
    insurance_contrib: float = 0.0  # 10% to insurance fund
    founder_fee: float = 0.0      # 10% performance fee
    
    # NAV
    nav_start: float = 0.0        # E_{k-1}
    nav_end: float = 0.0          # E_k
    
    @property
    def total_costs(self) -> float:
        return (self.trading_fees + self.gas_costs + self.slippage + 
                self.insurance_contrib + self.founder_fee)
    
    @property
    def gross_pnl(self) -> float:
        return self.funding_pnl + self.staking_pnl + self.spread_pnl
    
    @property
    def net_pnl(self) -> float:
        return self.gross_pnl - self.total_costs
    
    @property
    def period_return(self) -> float:
        """r_k = (P_fund + P_stake + P_spr - C_k) / E_{k-1}"""
        if self.nav_start <= 0:
            return 0.0
        return self.net_pnl / self.nav_start


@dataclass
class BacktestConfig:
    """Configuration for the backtest"""
    # Time range
    start_date: datetime = field(default_factory=lambda: datetime.now() - timedelta(days=180))
    end_date: datetime = field(default_factory=datetime.now)
    
    # Initial capital
    initial_nav_usd: float = 1_000_000.0  # $1M starting capital
    
    # Leverage settings
    leverage: float = 3.0  # L(t) - perp notional leverage
    
    # Yield assumptions
    lst_annual_yield: float = 0.035  # 3.5% annual LST staking yield (cbETH/wstETH)
    spread_capture_bps: float = 2.0  # 2 bps average spread capture per rebalance
    
    # Cost assumptions
    trading_fee_bps: float = 2.0     # 2 bps maker fee (Binance VIP)
    gas_cost_per_tx: float = 0.50    # $0.50 per on-chain tx (Base L2)
    slippage_bps: float = 1.0        # 1 bp average slippage
    rebalances_per_day: float = 0.5  # Rebalance every 2 days on average
    
    # Fee structure
    insurance_fund_bps: float = 1000  # 10% of gross yield
    performance_fee_bps: float = 1000  # 10% of gross yield
    
    # Exchange
    exchange: str = "binance"
    symbol: str = "ETH/USDT:USDT"


class APYBacktester:
    """
    Backtests Kerne's APY using the OpenAI framework.
    
    Fetches historical funding rates and calculates what the realized APY
    would have been over the specified period.
    """
    
    def __init__(self, config: BacktestConfig):
        self.config = config
        self.periods: List[PeriodPnL] = []
        self.exchange = None
        
        logger.info(f"Initializing APY Backtester")
        logger.info(f"Period: {config.start_date.date()} to {config.end_date.date()}")
        logger.info(f"Initial NAV: ${config.initial_nav_usd:,.0f}")
        logger.info(f"Leverage: {config.leverage}x")
    
    def _init_exchange(self):
        """Initialize CCXT exchange connection"""
        if self.exchange is None:
            if self.config.exchange == "binance":
                self.exchange = ccxt.binance({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'future'}
                })
            elif self.config.exchange == "bybit":
                self.exchange = ccxt.bybit({
                    'enableRateLimit': True,
                    'options': {'defaultType': 'linear'}
                })
            else:
                raise ValueError(f"Unsupported exchange: {self.config.exchange}")
    
    def fetch_funding_history(self) -> pd.DataFrame:
        """
        Fetch historical funding rates from the exchange.
        Returns DataFrame with columns: [timestamp, funding_rate]
        """
        self._init_exchange()
        
        logger.info(f"Fetching funding rate history from {self.config.exchange}...")
        
        all_funding = []
        since = int(self.config.start_date.timestamp() * 1000)
        end = int(self.config.end_date.timestamp() * 1000)
        
        while since < end:
            try:
                # Binance funding history endpoint
                if self.config.exchange == "binance":
                    funding = self.exchange.fetch_funding_rate_history(
                        self.config.symbol,
                        since=since,
                        limit=1000
                    )
                else:
                    # Bybit uses different method
                    funding = self.exchange.fetch_funding_rate_history(
                        self.config.symbol,
                        since=since,
                        limit=200
                    )
                
                if not funding:
                    break
                
                all_funding.extend(funding)
                since = funding[-1]['timestamp'] + 1
                
                logger.debug(f"Fetched {len(funding)} funding records, total: {len(all_funding)}")
                time.sleep(0.5)  # Rate limit
                
            except Exception as e:
                logger.warning(f"Error fetching funding: {e}")
                break
        
        if not all_funding:
            logger.warning("No funding data fetched, using simulated data")
            return self._generate_simulated_funding()
        
        df = pd.DataFrame(all_funding)
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df = df[['timestamp', 'fundingRate']].rename(columns={'fundingRate': 'funding_rate'})
        
        logger.success(f"Fetched {len(df)} funding rate records")
        return df
    
    def _generate_simulated_funding(self) -> pd.DataFrame:
        """
        Generate simulated funding rate data based on historical averages.
        Used when API fetch fails or for testing.
        """
        logger.info("Generating simulated funding rate data...")
        
        # Historical average funding rate for ETH perps: ~0.01% per 8h (positive bias)
        # With volatility clustering
        
        periods = []
        current = self.config.start_date
        
        # Base funding rate with mean reversion
        base_rate = 0.0001  # 0.01% per 8h = ~10.95% APY
        volatility = 0.00015  # Funding rate volatility
        mean_reversion = 0.1  # Speed of mean reversion
        
        current_rate = base_rate
        
        while current < self.config.end_date:
            # Mean-reverting random walk
            shock = np.random.normal(0, volatility)
            current_rate = current_rate + mean_reversion * (base_rate - current_rate) + shock
            
            # Clamp to realistic bounds (-0.1% to 0.3% per 8h)
            current_rate = max(-0.001, min(0.003, current_rate))
            
            periods.append({
                'timestamp': current,
                'funding_rate': current_rate
            })
            
            current += timedelta(hours=8)
        
        df = pd.DataFrame(periods)
        logger.info(f"Generated {len(df)} simulated funding periods")
        logger.info(f"Average funding rate: {df['funding_rate'].mean()*100:.4f}% per 8h")
        
        return df
    
    def calculate_period_pnl(
        self,
        funding_rate: float,
        nav_start: float,
        delta_t_days: float,
        eth_price: float = 2500.0
    ) -> PeriodPnL:
        """
        Calculate PnL for a single period using the OpenAI framework.
        
        Components:
        - P_fund = L * E * f (funding PnL = leverage * equity * funding rate)
        - P_stake = w * E * s * Δt (staking PnL = exposure * equity * yield * time)
        - P_spr = τ * E * e (spread PnL = turnover * equity * edge)
        - C = fees + gas + slippage + insurance + performance
        """
        L = self.config.leverage
        E = nav_start
        
        # Notional position size
        notional = L * E
        
        # 1. Funding PnL
        # P_fund = Notional * funding_rate
        # For short position receiving funding when rate is positive
        funding_pnl = notional * funding_rate
        
        # 2. Staking PnL
        # P_stake = Spot exposure * daily yield * days
        # For delta-neutral: spot exposure ≈ notional
        daily_lst_yield = self.config.lst_annual_yield / 365
        staking_pnl = notional * daily_lst_yield * delta_t_days
        
        # 3. Spread Capture PnL
        # P_spr = Rebalance volume * spread edge
        # Only on rebalance days
        rebalance_prob = self.config.rebalances_per_day * delta_t_days
        if np.random.random() < rebalance_prob:
            rebalance_volume = notional * 0.1  # 10% of position rebalanced
            spread_pnl = rebalance_volume * (self.config.spread_capture_bps / 10000)
        else:
            spread_pnl = 0.0
        
        # 4. Costs
        # Trading fees (on rebalances)
        trading_fees = 0.0
        if spread_pnl > 0:
            trading_fees = rebalance_volume * (self.config.trading_fee_bps / 10000) * 2  # Round trip
        
        # Gas costs
        gas_costs = self.config.gas_cost_per_tx * rebalance_prob
        
        # Slippage
        slippage = 0.0
        if spread_pnl > 0:
            slippage = rebalance_volume * (self.config.slippage_bps / 10000)
        
        # Gross yield for fee calculation
        gross_yield = funding_pnl + staking_pnl + spread_pnl
        
        # Insurance fund contribution (10% of positive yield)
        insurance_contrib = max(0, gross_yield * (self.config.insurance_fund_bps / 10000))
        
        # Performance fee (10% of positive yield after insurance)
        net_after_insurance = gross_yield - insurance_contrib
        founder_fee = max(0, net_after_insurance * (self.config.performance_fee_bps / 10000))
        
        # Calculate NAV end
        total_costs = trading_fees + gas_costs + slippage + insurance_contrib + founder_fee
        net_pnl = gross_yield - total_costs
        nav_end = nav_start + net_pnl
        
        return PeriodPnL(
            timestamp=datetime.now(),  # Will be set by caller
            delta_t_days=delta_t_days,
            funding_pnl=funding_pnl,
            staking_pnl=staking_pnl,
            spread_pnl=spread_pnl,
            trading_fees=trading_fees,
            gas_costs=gas_costs,
            slippage=slippage,
            insurance_contrib=insurance_contrib,
            founder_fee=founder_fee,
            nav_start=nav_start,
            nav_end=nav_end
        )
    
    def run_backtest(self) -> Dict:
        """
        Run the full backtest and calculate realized APY.
        
        Returns dict with:
        - realized_apy: The compounded APY using log returns
        - simple_apy: Simple annualized return
        - sharpe_ratio: Risk-adjusted return
        - max_drawdown: Maximum peak-to-trough decline
        - period_stats: Detailed period statistics
        """
        logger.info("=" * 60)
        logger.info("STARTING APY BACKTEST")
        logger.info("=" * 60)
        
        # Fetch funding rate history
        funding_df = self.fetch_funding_history()
        
        # Initialize
        nav = self.config.initial_nav_usd
        self.periods = []
        nav_history = [nav]
        
        logger.info(f"Processing {len(funding_df)} funding periods...")
        
        for idx, row in funding_df.iterrows():
            timestamp = row['timestamp']
            funding_rate = row['funding_rate']
            
            # Calculate period PnL
            period = self.calculate_period_pnl(
                funding_rate=funding_rate,
                nav_start=nav,
                delta_t_days=1/3,  # 8 hours = 1/3 day
            )
            period.timestamp = timestamp
            
            self.periods.append(period)
            nav = period.nav_end
            nav_history.append(nav)
            
            if idx % 100 == 0:
                logger.debug(f"Period {idx}: NAV=${nav:,.2f}, Funding={funding_rate*100:.4f}%")
        
        # Calculate APY using log returns (OpenAI formula)
        realized_apy = self._calculate_realized_apy()
        
        # Calculate additional metrics
        simple_apy = self._calculate_simple_apy()
        sharpe_ratio = self._calculate_sharpe_ratio()
        max_drawdown = self._calculate_max_drawdown(nav_history)
        
        # Period statistics
        period_returns = [p.period_return for p in self.periods]
        funding_rates = [funding_df.iloc[i]['funding_rate'] for i in range(len(self.periods))]
        
        results = {
            'realized_apy': realized_apy,
            'simple_apy': simple_apy,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'final_nav': nav,
            'total_return': (nav - self.config.initial_nav_usd) / self.config.initial_nav_usd,
            'num_periods': len(self.periods),
            'period_stats': {
                'avg_period_return': np.mean(period_returns),
                'std_period_return': np.std(period_returns),
                'min_period_return': np.min(period_returns),
                'max_period_return': np.max(period_returns),
                'positive_periods': sum(1 for r in period_returns if r > 0),
                'negative_periods': sum(1 for r in period_returns if r < 0),
            },
            'funding_stats': {
                'avg_funding_rate': np.mean(funding_rates),
                'std_funding_rate': np.std(funding_rates),
                'min_funding_rate': np.min(funding_rates),
                'max_funding_rate': np.max(funding_rates),
                'positive_funding_pct': sum(1 for f in funding_rates if f > 0) / len(funding_rates),
            },
            'pnl_breakdown': {
                'total_funding_pnl': sum(p.funding_pnl for p in self.periods),
                'total_staking_pnl': sum(p.staking_pnl for p in self.periods),
                'total_spread_pnl': sum(p.spread_pnl for p in self.periods),
                'total_costs': sum(p.total_costs for p in self.periods),
                'total_insurance': sum(p.insurance_contrib for p in self.periods),
                'total_founder_fee': sum(p.founder_fee for p in self.periods),
            },
            'config': {
                'leverage': self.config.leverage,
                'initial_nav': self.config.initial_nav_usd,
                'lst_yield': self.config.lst_annual_yield,
                'start_date': self.config.start_date.isoformat(),
                'end_date': self.config.end_date.isoformat(),
            }
        }
        
        return results
    
    def _calculate_realized_apy(self) -> float:
        """
        Calculate realized APY using the OpenAI log-return formula:
        APY = exp((365/Σ Δt_k) × Σ ln(1+r_k)) - 1
        """
        if not self.periods:
            return 0.0
        
        total_time_days = sum(p.delta_t_days for p in self.periods)
        if total_time_days <= 0:
            return 0.0
        
        # Sum of log returns (handle negative returns carefully)
        log_return_sum = 0.0
        for p in self.periods:
            if p.period_return > -1:  # Avoid log of negative
                log_return_sum += math.log(1 + p.period_return)
            else:
                # Catastrophic loss - cap at -99%
                log_return_sum += math.log(0.01)
        
        # Annualize
        annualized_log_return = (365 / total_time_days) * log_return_sum
        
        # Convert to APY
        apy = math.exp(annualized_log_return) - 1
        
        return apy
    
    def _calculate_simple_apy(self) -> float:
        """Calculate simple annualized return (non-compounded)"""
        if not self.periods:
            return 0.0
        
        total_return = (self.periods[-1].nav_end - self.config.initial_nav_usd) / self.config.initial_nav_usd
        total_days = sum(p.delta_t_days for p in self.periods)
        
        if total_days <= 0:
            return 0.0
        
        return total_return * (365 / total_days)
    
    def _calculate_sharpe_ratio(self, risk_free_rate: float = 0.05) -> float:
        """Calculate annualized Sharpe ratio"""
        if not self.periods:
            return 0.0
        
        returns = [p.period_return for p in self.periods]
        if len(returns) < 2:
            return 0.0
        
        # Annualize (3 periods per day * 365 days)
        periods_per_year = 3 * 365
        
        avg_return = np.mean(returns) * periods_per_year
        std_return = np.std(returns) * math.sqrt(periods_per_year)
        
        if std_return == 0:
            return 0.0
        
        return (avg_return - risk_free_rate) / std_return
    
    def _calculate_max_drawdown(self, nav_history: List[float]) -> float:
        """Calculate maximum drawdown"""
        if len(nav_history) < 2:
            return 0.0
        
        peak = nav_history[0]
        max_dd = 0.0
        
        for nav in nav_history:
            if nav > peak:
                peak = nav
            dd = (peak - nav) / peak
            if dd > max_dd:
                max_dd = dd
        
        return max_dd
    
    def print_results(self, results: Dict):
        """Print formatted backtest results"""
        print("\n" + "=" * 70)
        print("KERNE APY BACKTEST RESULTS")
        print("Using OpenAI's NAV-Based Log-Return Framework")
        print("=" * 70)
        
        print(f"\n📅 Period: {results['config']['start_date'][:10]} to {results['config']['end_date'][:10]}")
        print(f"💰 Initial NAV: ${results['config']['initial_nav']:,.0f}")
        print(f"⚡ Leverage: {results['config']['leverage']}x")
        print(f"🌿 LST Yield: {results['config']['lst_yield']*100:.1f}%")
        
        print("\n" + "-" * 70)
        print("PERFORMANCE METRICS")
        print("-" * 70)
        
        print(f"\n🎯 REALIZED APY (Log-Return Compounded): {results['realized_apy']*100:.2f}%")
        print(f"📊 Simple APY (Non-Compounded):          {results['simple_apy']*100:.2f}%")
        print(f"💵 Final NAV:                            ${results['final_nav']:,.2f}")
        print(f"📈 Total Return:                         {results['total_return']*100:.2f}%")
        
        print(f"\n📉 Max Drawdown:                         {results['max_drawdown']*100:.2f}%")
        print(f"📐 Sharpe Ratio:                         {results['sharpe_ratio']:.2f}")
        
        print("\n" + "-" * 70)
        print("PnL BREAKDOWN (6 Months)")
        print("-" * 70)
        
        pnl = results['pnl_breakdown']
        print(f"\n💹 Funding PnL:      ${pnl['total_funding_pnl']:>12,.2f}")
        print(f"🌿 Staking PnL:      ${pnl['total_staking_pnl']:>12,.2f}")
        print(f"📊 Spread PnL:       ${pnl['total_spread_pnl']:>12,.2f}")
        print(f"   ─────────────────────────────")
        gross = pnl['total_funding_pnl'] + pnl['total_staking_pnl'] + pnl['total_spread_pnl']
        print(f"   Gross PnL:        ${gross:>12,.2f}")
        print(f"\n💸 Total Costs:      ${pnl['total_costs']:>12,.2f}")
        print(f"   - Insurance:      ${pnl['total_insurance']:>12,.2f}")
        print(f"   - Founder Fee:    ${pnl['total_founder_fee']:>12,.2f}")
        print(f"   ─────────────────────────────")
        net = gross - pnl['total_costs']
        print(f"   Net PnL:          ${net:>12,.2f}")
        
        print("\n" + "-" * 70)
        print("FUNDING RATE STATISTICS")
        print("-" * 70)
        
        fs = results['funding_stats']
        print(f"\n📊 Average Funding Rate:  {fs['avg_funding_rate']*100:.4f}% per 8h")
        print(f"   Annualized:            {fs['avg_funding_rate']*3*365*100:.2f}%")
        print(f"📈 Max Funding Rate:      {fs['max_funding_rate']*100:.4f}% per 8h")
        print(f"📉 Min Funding Rate:      {fs['min_funding_rate']*100:.4f}% per 8h")
        print(f"✅ Positive Funding:      {fs['positive_funding_pct']*100:.1f}% of periods")
        
        print("\n" + "-" * 70)
        print("PERIOD STATISTICS")
        print("-" * 70)
        
        ps = results['period_stats']
        print(f"\n📊 Total Periods:         {results['num_periods']}")
        print(f"✅ Positive Periods:      {ps['positive_periods']} ({ps['positive_periods']/results['num_periods']*100:.1f}%)")
        print(f"❌ Negative Periods:      {ps['negative_periods']} ({ps['negative_periods']/results['num_periods']*100:.1f}%)")
        print(f"📈 Avg Period Return:     {ps['avg_period_return']*100:.4f}%")
        print(f"📊 Std Period Return:     {ps['std_period_return']*100:.4f}%")
        
        print("\n" + "=" * 70)
        print("INTERPRETATION")
        print("=" * 70)
        
        apy = results['realized_apy']
        if apy > 0.20:
            print("\n🚀 EXCELLENT: APY > 20% - Strong funding environment")
        elif apy > 0.10:
            print("\n✅ GOOD: APY 10-20% - Healthy delta-neutral returns")
        elif apy > 0.05:
            print("\n⚠️ MODERATE: APY 5-10% - Below average funding")
        else:
            print("\n❌ POOR: APY < 5% - Challenging funding environment")
        
        print("\n" + "=" * 70)


def run_sensitivity_analysis():
    """Run backtest with different leverage levels"""
    print("\n" + "=" * 70)
    print("LEVERAGE SENSITIVITY ANALYSIS")
    print("=" * 70)
    
    leverages = [1.0, 2.0, 3.0, 5.0, 8.0, 10.0]
    results = []
    
    for lev in leverages:
        config = BacktestConfig(leverage=lev)
        backtester = APYBacktester(config)
        result = backtester.run_backtest()
        results.append({
            'leverage': lev,
            'apy': result['realized_apy'],
            'sharpe': result['sharpe_ratio'],
            'max_dd': result['max_drawdown']
        })
    
    print("\n| Leverage | APY      | Sharpe | Max DD  |")
    print("|----------|----------|--------|---------|")
    for r in results:
        print(f"| {r['leverage']:>6.1f}x | {r['apy']*100:>6.2f}% | {r['sharpe']:>6.2f} | {r['max_dd']*100:>5.2f}% |")
    
    # Find optimal leverage (max Sharpe)
    optimal = max(results, key=lambda x: x['sharpe'])
    print(f"\n🎯 Optimal Leverage (Max Sharpe): {optimal['leverage']}x")
    print(f"   Expected APY: {optimal['apy']*100:.2f}%")
    print(f"   Sharpe Ratio: {optimal['sharpe']:.2f}")


def main():
    """Main entry point"""
    logger.remove()
    logger.add(sys.stderr, level="INFO")
    
    print("\n" + "=" * 70)
    print("KERNE PROTOCOL - APY BACKTEST ENGINE")
    print("Implementing OpenAI's NAV-Based Log-Return Framework")
    print("=" * 70)
    
    # Default 6-month backtest with 3x leverage
    config = BacktestConfig(
        start_date=datetime.now() - timedelta(days=180),
        end_date=datetime.now(),
        initial_nav_usd=1_000_000,
        leverage=3.0,
        lst_annual_yield=0.035,
    )
    
    backtester = APYBacktester(config)
    results = backtester.run_backtest()
    backtester.print_results(results)
    
    # Save results to JSON
    output_path = os.path.join(os.path.dirname(__file__), "backtest_results.json")
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.success(f"Results saved to {output_path}")
    
    # Run sensitivity analysis
    run_sensitivity_analysis()


if __name__ == "__main__":
    main()
