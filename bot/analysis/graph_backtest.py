# Created: 2026-01-30
"""
Bellman-Ford Graph Arbitrage Backtester
=======================================
Simulates the Bellman-Ford negative cycle detection algorithm against 
historical or snapshot DEX data to map the protocol's revenue surface area.
"""

import os
import json
import math
import asyncio
import time
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from web3 import Web3
from loguru import logger
from dotenv import load_dotenv

# Import existing models from scanner
from bot.flash_arb_scanner import GraphArbScanner, Token, Pool, ArbPath

@dataclass
class BacktestResult:
    timestamp: float
    cycles_found: int
    profitable_cycles: int
    total_gross_profit_usd: float
    total_gas_cost_usd: float
    net_profit_usd: float
    best_path: Optional[str] = None

class GraphBacktester:
    def __init__(self):
        load_dotenv()
        self.scanner = GraphArbScanner()
        # Limit pools for backtest to avoid RPC timeouts
        # Only keep Aerodrome and Uniswap V3 pools involving WETH, USDC, or kUSD
        from bot.gas_estimator import DEX
        core_tokens = {self.scanner.WETH.address, self.scanner.USDC.address, self.scanner.KUSD.address}
        self.scanner.pools = [
            p for p in self.scanner.pools 
            if (p.token0.address in core_tokens and p.token1.address in core_tokens)
            and p.dex in [DEX.AERODROME, DEX.UNISWAP_V3]
        ]
        logger.info(f"Backtest limited to {len(self.scanner.pools)} core pools.")
        self.results: List[BacktestResult] = []
        
    async def run_snapshot_backtest(self, iterations: int = 10, interval: int = 5):
        """
        Runs a backtest by taking live snapshots of the DEX graph over time.
        This maps the 'real-time' revenue surface area.
        """
        logger.info(f"🚀 Starting Bellman-Ford Backtest: {iterations} iterations, {interval}s interval")
        
        base_tokens = [self.scanner.WETH, self.scanner.USDC, self.scanner.KUSD]
        eth_price = await self.scanner._get_eth_price()
        
        for i in range(iterations):
            start_time = time.time()
            logger.info(f"--- Iteration {i+1}/{iterations} ---")
            
            iteration_gross = 0.0
            iteration_gas = 0.0
            iteration_profitable = 0
            iteration_cycles = 0
            best_path_str = ""
            max_net = -1.0
            
            for base_token in base_tokens:
                # Use a standard $10k test amount for mapping
                amount_in = 10000 * (10 ** base_token.decimals) if base_token != self.scanner.WETH else int(3 * 1e18)
                
                # 1. Run Bellman-Ford Discovery
                cycles = await self.scanner.find_profitable_cycles_bellman_ford(base_token, amount_in)
                iteration_cycles += len(cycles)
                
                # 2. Evaluate each cycle for net profit
                tasks = [self.scanner.evaluate_cycle(c, base_token, amount_in) for c in cycles]
                eval_results = await asyncio.gather(*tasks)
                
                for res in eval_results:
                    if res and res.profit_usd > 0:
                        iteration_profitable += 1
                        iteration_gross += res.profit_usd # evaluate_cycle returns net, but we'll treat it as gross for breakdown
                        
                        if res.profit_usd > max_net:
                            max_net = res.profit_usd
                            best_path_str = str(res)

            # Estimate gas for the iteration (simplified)
            # In a real run, we'd only execute the best one, so we track the best potential
            
            res = BacktestResult(
                timestamp=time.time(),
                cycles_found=iteration_cycles,
                profitable_cycles=iteration_profitable,
                total_gross_profit_usd=iteration_gross,
                total_gas_cost_usd=0.0, # Gas already subtracted in evaluate_cycle
                net_profit_usd=iteration_gross,
                best_path=best_path_str
            )
            self.results.append(res)
            
            logger.info(f"Found {iteration_cycles} cycles, {iteration_profitable} profitable. Net: ${iteration_gross:.2f}")
            if best_path_str:
                logger.success(f"Best: {best_path_str}")
                
            elapsed = time.time() - start_time
            wait = max(0, interval - elapsed)
            await asyncio.sleep(wait)

    def generate_report(self):
        if not self.results:
            logger.warning("No results to report.")
            return

        total_net = sum(r.net_profit_usd for r in self.results)
        avg_cycles = sum(r.cycles_found for r in self.results) / len(self.results)
        
        report_path = "docs/reports/GRAPH_BACKTEST_REPORT.md"
        with open(report_path, "w") as f:
            f.write("# Bellman-Ford Graph Arbitrage Backtest Report\n")
            f.write(f"**Date:** {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"## Summary\n")
            f.write(f"- **Total Iterations:** {len(self.results)}\n")
            f.write(f"- **Total Potential Profit:** ${total_net:.2f}\n")
            f.write(f"- **Avg Cycles Found/Iter:** {avg_cycles:.2f}\n")
            f.write(f"- **Profitable Opportunities:** {sum(r.profitable_cycles for r in self.results)}\n\n")
            
            f.write("## Iteration Log\n")
            f.write("| Timestamp | Cycles | Profitable | Net Profit | Best Path |\n")
            f.write("|-----------|--------|------------|------------|-----------|\n")
            for r in self.results:
                f.write(f"| {time.strftime('%H:%M:%S', time.localtime(r.timestamp))} | {r.cycles_found} | {r.profitable_cycles} | ${r.net_profit_usd:.2f} | {r.best_path or 'N/A'} |\n")

        logger.success(f"Report generated at {report_path}")

if __name__ == "__main__":
    backtester = GraphBacktester()
    # Reduced iterations for quick concept validation on public RPC
    asyncio.run(backtester.run_snapshot_backtest(iterations=1, interval=1))
    backtester.generate_report()
