# Created: 2026-01-20
"""
Kerne Protocol - Daily Profit Telemetry & Automated Reporting

This module aggregates profit data from all revenue streams:
- ZIN Pool spread capture (Base + Arbitrum)
- Flash-Arb bot profits (Treasury deposits)
- Hyperliquid funding rate income
- Vault yield accrual

Reports are posted to Discord and saved to docs/reports/.
"""
from __future__ import annotations

import json
import math
import os
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from loguru import logger
from web3 import Web3
from web3.exceptions import ContractLogicError

load_dotenv()


# =============================================================================
# ABI FRAGMENTS FOR ON-CHAIN QUERIES
# =============================================================================

ZIN_POOL_ABI = [
    {
        "inputs": [{"name": "token", "type": "address"}],
        "name": "totalVolumeFilled",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "token", "type": "address"}],
        "name": "totalProfitCaptured",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "totalOrdersFilled",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [{"name": "token", "type": "address"}],
        "name": "getAvailableLiquidity",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    }
]

ERC20_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "stateMutability": "view",
        "type": "function"
    }
]


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class ChainMetrics:
    """Metrics for a single chain."""
    chain_name: str
    chain_id: int
    zin_pool_address: str
    total_orders_filled: int = 0
    total_volume_usd: float = 0.0
    total_profit_usd: float = 0.0
    pool_liquidity_usd: float = 0.0
    tokens_tracked: Dict[str, Dict[str, float]] = field(default_factory=dict)


@dataclass
class ProtocolMetrics:
    """Aggregated metrics across all chains."""
    timestamp: float
    date: str
    
    # ZIN Metrics
    zin_total_orders: int = 0
    zin_total_volume_usd: float = 0.0
    zin_total_profit_usd: float = 0.0
    zin_total_liquidity_usd: float = 0.0
    
    # Flash-Arb Metrics
    arb_total_profit_usd: float = 0.0
    arb_trades_executed: int = 0
    
    # Hyperliquid Metrics
    hl_funding_income_usd: float = 0.0
    hl_position_value_usd: float = 0.0
    
    # Vault Metrics
    vault_tvl_usd: float = 0.0
    vault_yield_accrued_usd: float = 0.0
    
    # Summary
    total_protocol_profit_usd: float = 0.0
    daily_apy_bps: float = 0.0
    annualized_apy_pct: float = 0.0
    
    # Chain breakdown
    chain_metrics: List[ChainMetrics] = field(default_factory=list)


# =============================================================================
# CHAIN CONFIGURATIONS
# =============================================================================

CHAIN_CONFIGS = {
    "base": {
        "chain_id": 8453,
        "rpc_urls": os.getenv("RPC_URL", "https://base.llamarpc.com").split(","),
        "zin_pool": os.getenv("ZIN_POOL_ADDRESS", "0xB9BdF6F3Fc3819b61f6fE799bE1395501822d0c7"),
        "treasury": os.getenv("TREASURY_ADDRESS", "0x0067F4957dea17CF76665F6A6585F6a904362106"),
        "vault": os.getenv("VAULT_ADDRESS", "0x8005bc7A86AD904C20fd62788ABED7546c1cF2AC"),
        "tokens": {
            "USDC": {"address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913", "decimals": 6},
            "WETH": {"address": "0x4200000000000000000000000000000000000006", "decimals": 18},
            "wstETH": {"address": "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452", "decimals": 18},
            "cbETH": {"address": "0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22", "decimals": 18},
        }
    },
    "arbitrum": {
        "chain_id": 42161,
        "rpc_urls": os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc").split(","),
        "zin_pool": os.getenv("ARBITRUM_ZIN_POOL_ADDRESS", "0x5D8ddE6264DF8A0963253693f32e057e1aA37aFD"),
        "treasury": None,  # Arbitrum doesn't have separate treasury yet
        "vault": None,
        "tokens": {
            "USDC": {"address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831", "decimals": 6},
            "USDC.e": {"address": "0xFF970A61A04b1cA14834A43f5dE4533eBDDB5CC8", "decimals": 6},
            "WETH": {"address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1", "decimals": 18},
            "wstETH": {"address": "0x5979D7b546E38E414F7E9822514be443A4800529", "decimals": 18},
        }
    }
}

# Approximate token prices (should be fetched from oracle in production)
TOKEN_PRICES_USD = {
    "USDC": 1.0,
    "USDC.e": 1.0,
    "WETH": 3200.0,
    "wstETH": 3700.0,
    "cbETH": 3400.0,
}


# =============================================================================
# TELEMETRY ENGINE
# =============================================================================

class ProfitTelemetry:
    """
    Aggregates and reports protocol profit metrics across all chains and revenue streams.
    """
    
    def __init__(self, output_dir: str = "docs/reports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.discord_webhook = os.getenv("DISCORD_WEBHOOK_URL", "")
        self.web3_instances: Dict[str, Web3] = {}
        self._init_web3_connections()
    
    def _init_web3_connections(self) -> None:
        """Initialize Web3 connections for all configured chains."""
        for chain_name, config in CHAIN_CONFIGS.items():
            for rpc_url in config["rpc_urls"]:
                try:
                    w3 = Web3(Web3.HTTPProvider(rpc_url.strip()))
                    if w3.is_connected():
                        self.web3_instances[chain_name] = w3
                        logger.info(f"Connected to {chain_name}: {rpc_url}")
                        break
                except Exception as e:
                    logger.warning(f"Failed to connect to {chain_name} via {rpc_url}: {e}")
            
            if chain_name not in self.web3_instances:
                logger.error(f"Failed to connect to {chain_name} - no working RPC")
    
    def _get_token_price(self, symbol: str) -> float:
        """Get token price in USD. TODO: Integrate Chainlink/Pyth oracle."""
        return TOKEN_PRICES_USD.get(symbol, 0.0)
    
    def _fetch_zin_metrics(self, chain_name: str) -> Optional[ChainMetrics]:
        """Fetch ZIN Pool metrics for a single chain."""
        if chain_name not in self.web3_instances:
            return None
        
        w3 = self.web3_instances[chain_name]
        config = CHAIN_CONFIGS[chain_name]
        pool_address = config["zin_pool"]
        
        try:
            pool_checksum = Web3.to_checksum_address(pool_address)
            
            # Verify contract exists at address
            code = w3.eth.get_code(pool_checksum)
            if code == b'' or code == '0x':
                logger.warning(f"No contract code at {pool_address} on {chain_name}")
                return None
            
            pool = w3.eth.contract(
                address=pool_checksum,
                abi=ZIN_POOL_ABI
            )
            
            metrics = ChainMetrics(
                chain_name=chain_name,
                chain_id=config["chain_id"],
                zin_pool_address=pool_address,
            )
            
            # Fetch total orders
            try:
                metrics.total_orders_filled = pool.functions.totalOrdersFilled().call()
            except (ContractLogicError, Exception) as e:
                logger.debug(f"Could not fetch totalOrdersFilled on {chain_name}: {e}")
                metrics.total_orders_filled = 0
            
            # Fetch per-token metrics
            for symbol, token_info in config["tokens"].items():
                token_addr = Web3.to_checksum_address(token_info["address"])
                decimals = token_info["decimals"]
                price = self._get_token_price(symbol)
                
                try:
                    volume_raw = pool.functions.totalVolumeFilled(token_addr).call()
                    profit_raw = pool.functions.totalProfitCaptured(token_addr).call()
                    liquidity_raw = pool.functions.getAvailableLiquidity(token_addr).call()
                    
                    volume = volume_raw / (10 ** decimals)
                    profit = profit_raw / (10 ** decimals)
                    liquidity = liquidity_raw / (10 ** decimals)
                    
                    metrics.tokens_tracked[symbol] = {
                        "volume": volume,
                        "profit": profit,
                        "liquidity": liquidity,
                        "volume_usd": volume * price,
                        "profit_usd": profit * price,
                        "liquidity_usd": liquidity * price,
                    }
                    
                    metrics.total_volume_usd += volume * price
                    metrics.total_profit_usd += profit * price
                    metrics.pool_liquidity_usd += liquidity * price
                    
                except ContractLogicError as e:
                    logger.debug(f"Token {symbol} not supported on {chain_name}: {e}")
                except Exception as e:
                    logger.warning(f"Error fetching {symbol} on {chain_name}: {e}")
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to fetch ZIN metrics for {chain_name}: {e}")
            return None
    
    def _fetch_treasury_balance(self, chain_name: str) -> float:
        """Fetch Treasury balance (flash-arb profits accumulate here)."""
        if chain_name not in self.web3_instances:
            return 0.0
        
        config = CHAIN_CONFIGS[chain_name]
        treasury = config.get("treasury")
        if not treasury:
            return 0.0
        
        w3 = self.web3_instances[chain_name]
        total_usd = 0.0
        
        for symbol, token_info in config["tokens"].items():
            try:
                token = w3.eth.contract(
                    address=Web3.to_checksum_address(token_info["address"]),
                    abi=ERC20_ABI
                )
                balance_raw = token.functions.balanceOf(
                    Web3.to_checksum_address(treasury)
                ).call()
                balance = balance_raw / (10 ** token_info["decimals"])
                price = self._get_token_price(symbol)
                total_usd += balance * price
            except Exception as e:
                logger.debug(f"Error fetching treasury balance for {symbol}: {e}")
        
        return total_usd
    
    def _fetch_vault_tvl(self, chain_name: str) -> float:
        """Fetch KerneVault TVL."""
        if chain_name not in self.web3_instances:
            return 0.0
        
        config = CHAIN_CONFIGS[chain_name]
        vault = config.get("vault")
        if not vault:
            return 0.0
        
        w3 = self.web3_instances[chain_name]
        total_usd = 0.0
        
        for symbol, token_info in config["tokens"].items():
            try:
                token = w3.eth.contract(
                    address=Web3.to_checksum_address(token_info["address"]),
                    abi=ERC20_ABI
                )
                balance_raw = token.functions.balanceOf(
                    Web3.to_checksum_address(vault)
                ).call()
                balance = balance_raw / (10 ** token_info["decimals"])
                price = self._get_token_price(symbol)
                total_usd += balance * price
            except Exception as e:
                logger.debug(f"Error fetching vault balance for {symbol}: {e}")
        
        return total_usd
    
    def collect_metrics(self) -> ProtocolMetrics:
        """Collect all protocol metrics across chains."""
        now = datetime.now(tz=timezone.utc)
        
        metrics = ProtocolMetrics(
            timestamp=now.timestamp(),
            date=now.strftime("%Y-%m-%d"),
        )
        
        # Fetch ZIN metrics for each chain
        for chain_name in CHAIN_CONFIGS.keys():
            chain_metrics = self._fetch_zin_metrics(chain_name)
            if chain_metrics:
                metrics.chain_metrics.append(chain_metrics)
                metrics.zin_total_orders += chain_metrics.total_orders_filled
                metrics.zin_total_volume_usd += chain_metrics.total_volume_usd
                metrics.zin_total_profit_usd += chain_metrics.total_profit_usd
                metrics.zin_total_liquidity_usd += chain_metrics.pool_liquidity_usd
        
        # Fetch Treasury (flash-arb profits)
        metrics.arb_total_profit_usd = self._fetch_treasury_balance("base")
        
        # Fetch Vault TVL
        metrics.vault_tvl_usd = self._fetch_vault_tvl("base")
        
        # Calculate totals
        metrics.total_protocol_profit_usd = (
            metrics.zin_total_profit_usd +
            metrics.arb_total_profit_usd +
            metrics.hl_funding_income_usd +
            metrics.vault_yield_accrued_usd
        )
        
        # Calculate APY (if we have TVL)
        if metrics.vault_tvl_usd > 0:
            daily_return = metrics.total_protocol_profit_usd / metrics.vault_tvl_usd
            metrics.daily_apy_bps = daily_return * 10000
            # Annualize using compound formula
            metrics.annualized_apy_pct = ((1 + daily_return) ** 365 - 1) * 100
        
        return metrics
    
    def generate_markdown_report(self, metrics: ProtocolMetrics) -> str:
        """Generate a detailed Markdown report."""
        lines = [
            f"# Kerne Protocol Daily Profit Report",
            f"**Date:** {metrics.date}",
            f"**Generated:** {datetime.now(tz=timezone.utc).isoformat()}",
            "",
            "---",
            "",
            "## 📊 Summary",
            "",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| **Total Protocol Profit** | ${metrics.total_protocol_profit_usd:,.2f} |",
            f"| **ZIN Orders Filled** | {metrics.zin_total_orders:,} |",
            f"| **ZIN Volume** | ${metrics.zin_total_volume_usd:,.2f} |",
            f"| **ZIN Pool Liquidity** | ${metrics.zin_total_liquidity_usd:,.2f} |",
            f"| **Treasury Balance** | ${metrics.arb_total_profit_usd:,.2f} |",
            f"| **Vault TVL** | ${metrics.vault_tvl_usd:,.2f} |",
            f"| **Daily APY (bps)** | {metrics.daily_apy_bps:.2f} |",
            f"| **Annualized APY** | {metrics.annualized_apy_pct:.2f}% |",
            "",
            "---",
            "",
            "## 🔗 Chain Breakdown",
            "",
        ]
        
        for chain in metrics.chain_metrics:
            lines.extend([
                f"### {chain.chain_name.upper()} (Chain ID: {chain.chain_id})",
                "",
                f"- **ZIN Pool:** `{chain.zin_pool_address}`",
                f"- **Orders Filled:** {chain.total_orders_filled:,}",
                f"- **Volume:** ${chain.total_volume_usd:,.2f}",
                f"- **Profit Captured:** ${chain.total_profit_usd:,.2f}",
                f"- **Pool Liquidity:** ${chain.pool_liquidity_usd:,.2f}",
                "",
                "**Token Breakdown:**",
                "",
                "| Token | Volume | Profit | Liquidity |",
                "|-------|--------|--------|-----------|",
            ])
            
            for symbol, data in chain.tokens_tracked.items():
                lines.append(
                    f"| {symbol} | ${data['volume_usd']:,.2f} | ${data['profit_usd']:,.2f} | ${data['liquidity_usd']:,.2f} |"
                )
            
            lines.append("")
        
        lines.extend([
            "---",
            "",
            "## 📈 Revenue Streams",
            "",
            f"1. **ZIN Spread Capture:** ${metrics.zin_total_profit_usd:,.2f}",
            f"2. **Flash-Arb Profits:** ${metrics.arb_total_profit_usd:,.2f}",
            f"3. **Hyperliquid Funding:** ${metrics.hl_funding_income_usd:,.2f}",
            f"4. **Vault Yield:** ${metrics.vault_yield_accrued_usd:,.2f}",
            "",
            "---",
            "",
            f"*Report generated automatically by Kerne Profit Telemetry v1.0*",
        ])
        
        return "\n".join(lines)
    
    def generate_discord_embed(self, metrics: ProtocolMetrics) -> Dict[str, Any]:
        """Generate a Discord webhook payload with rich embed."""
        # Determine color based on profitability
        color = 0x00FF00 if metrics.total_protocol_profit_usd > 0 else 0xFF0000
        
        embed = {
            "title": f"📊 Daily Profit Report - {metrics.date}",
            "color": color,
            "fields": [
                {
                    "name": "💰 Total Profit",
                    "value": f"${metrics.total_protocol_profit_usd:,.2f}",
                    "inline": True
                },
                {
                    "name": "📈 Annualized APY",
                    "value": f"{metrics.annualized_apy_pct:.2f}%",
                    "inline": True
                },
                {
                    "name": "🏦 Vault TVL",
                    "value": f"${metrics.vault_tvl_usd:,.2f}",
                    "inline": True
                },
                {
                    "name": "⚡ ZIN Orders",
                    "value": f"{metrics.zin_total_orders:,}",
                    "inline": True
                },
                {
                    "name": "📦 ZIN Volume",
                    "value": f"${metrics.zin_total_volume_usd:,.2f}",
                    "inline": True
                },
                {
                    "name": "💧 ZIN Liquidity",
                    "value": f"${metrics.zin_total_liquidity_usd:,.2f}",
                    "inline": True
                },
            ],
            "footer": {
                "text": f"Kerne Protocol | Generated at {datetime.now(tz=timezone.utc).strftime('%H:%M UTC')}"
            },
            "timestamp": datetime.now(tz=timezone.utc).isoformat()
        }
        
        # Add chain breakdown
        chain_details = []
        for chain in metrics.chain_metrics:
            chain_details.append(
                f"**{chain.chain_name.upper()}**: {chain.total_orders_filled} orders, "
                f"${chain.total_profit_usd:,.2f} profit"
            )
        
        if chain_details:
            embed["fields"].append({
                "name": "🔗 Chain Breakdown",
                "value": "\n".join(chain_details),
                "inline": False
            })
        
        return {"embeds": [embed], "username": "Kerne Telemetry"}
    
    def post_to_discord(self, metrics: ProtocolMetrics) -> bool:
        """Post report to Discord webhook."""
        if not self.discord_webhook or "your_discord_webhook_url" in self.discord_webhook:
            logger.warning("Discord webhook not configured, skipping Discord post")
            return False
        
        try:
            payload = self.generate_discord_embed(metrics)
            response = requests.post(
                self.discord_webhook,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            logger.success("Posted daily report to Discord")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Discord: {e}")
            return False
    
    def save_report(self, metrics: ProtocolMetrics) -> Path:
        """Save Markdown report to docs/reports/."""
        report_content = self.generate_markdown_report(metrics)
        filename = f"DAILY_PROFIT_{metrics.date}.md"
        filepath = self.output_dir / filename
        
        with filepath.open("w", encoding="utf-8") as f:
            f.write(report_content)
        
        logger.success(f"Saved report to {filepath}")
        return filepath
    
    def save_json(self, metrics: ProtocolMetrics) -> Path:
        """Save raw metrics to JSON for programmatic access."""
        filename = f"daily_metrics_{metrics.date}.json"
        filepath = self.output_dir / filename
        
        # Convert to serializable dict
        data = {
            "timestamp": metrics.timestamp,
            "date": metrics.date,
            "zin": {
                "total_orders": metrics.zin_total_orders,
                "total_volume_usd": metrics.zin_total_volume_usd,
                "total_profit_usd": metrics.zin_total_profit_usd,
                "total_liquidity_usd": metrics.zin_total_liquidity_usd,
            },
            "arb": {
                "total_profit_usd": metrics.arb_total_profit_usd,
            },
            "vault": {
                "tvl_usd": metrics.vault_tvl_usd,
            },
            "summary": {
                "total_profit_usd": metrics.total_protocol_profit_usd,
                "daily_apy_bps": metrics.daily_apy_bps,
                "annualized_apy_pct": metrics.annualized_apy_pct,
            },
            "chains": [
                {
                    "name": c.chain_name,
                    "chain_id": c.chain_id,
                    "orders": c.total_orders_filled,
                    "volume_usd": c.total_volume_usd,
                    "profit_usd": c.total_profit_usd,
                    "liquidity_usd": c.pool_liquidity_usd,
                }
                for c in metrics.chain_metrics
            ]
        }
        
        with filepath.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved JSON metrics to {filepath}")
        return filepath
    
    def run(self, post_discord: bool = True, save_files: bool = True) -> ProtocolMetrics:
        """
        Run the full telemetry collection and reporting pipeline.
        
        Args:
            post_discord: Whether to post to Discord webhook
            save_files: Whether to save report files
            
        Returns:
            ProtocolMetrics: Collected metrics
        """
        logger.info("Starting profit telemetry collection...")
        
        metrics = self.collect_metrics()
        
        logger.info(f"Collected metrics: {metrics.zin_total_orders} orders, "
                   f"${metrics.total_protocol_profit_usd:.2f} profit")
        
        if save_files:
            self.save_report(metrics)
            self.save_json(metrics)
        
        if post_discord:
            self.post_to_discord(metrics)
        
        return metrics


# =============================================================================
# CLI ENTRY POINT
# =============================================================================

def main():
    """CLI entry point for profit telemetry."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Kerne Profit Telemetry")
    parser.add_argument("--no-discord", action="store_true", help="Skip Discord posting")
    parser.add_argument("--no-save", action="store_true", help="Skip saving report files")
    parser.add_argument("--metrics-only", action="store_true", help="Print metrics to console only")
    args = parser.parse_args()
    
    telemetry = ProfitTelemetry()
    
    if args.metrics_only:
        metrics = telemetry.collect_metrics()
        print("\n" + "=" * 60)
        print("KERNE PROTOCOL PROFIT TELEMETRY")
        print("=" * 60)
        print(f"Date: {metrics.date}")
        print(f"ZIN Orders Filled: {metrics.zin_total_orders}")
        print(f"ZIN Volume (USD): ${metrics.zin_total_volume_usd:,.2f}")
        print(f"ZIN Profit (USD): ${metrics.zin_total_profit_usd:,.2f}")
        print(f"ZIN Liquidity (USD): ${metrics.zin_total_liquidity_usd:,.2f}")
        print(f"Treasury Balance (USD): ${metrics.arb_total_profit_usd:,.2f}")
        print(f"Vault TVL (USD): ${metrics.vault_tvl_usd:,.2f}")
        print(f"Total Profit (USD): ${metrics.total_protocol_profit_usd:,.2f}")
        print(f"Daily APY (bps): {metrics.daily_apy_bps:.2f}")
        print(f"Annualized APY: {metrics.annualized_apy_pct:.2f}%")
        print("=" * 60)
        
        for chain in metrics.chain_metrics:
            print(f"\n{chain.chain_name.upper()}:")
            print(f"  Pool: {chain.zin_pool_address}")
            print(f"  Orders: {chain.total_orders_filled}")
            print(f"  Volume: ${chain.total_volume_usd:,.2f}")
            print(f"  Profit: ${chain.total_profit_usd:,.2f}")
            print(f"  Liquidity: ${chain.pool_liquidity_usd:,.2f}")
    else:
        telemetry.run(
            post_discord=not args.no_discord,
            save_files=not args.no_save
        )


if __name__ == "__main__":
    main()
