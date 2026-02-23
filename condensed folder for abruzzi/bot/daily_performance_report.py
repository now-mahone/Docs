# Created: 2026-02-08
"""
Kerne Protocol - Comprehensive Daily Performance Report

Aggregates ALL protocol data into a single automated daily report:
- Hyperliquid: equity, positions, funding rates, P&L, liquidation prices
- On-chain: wallet balances across Base + Arbitrum (deployer, treasury, vault)
- Solvency: total assets vs liabilities ratio
- Yield: daily/annualized APY from funding rate capture
- Health: hedging position delta, buffer adequacy

Reports are:
1. Posted to Discord (rich embed)
2. Saved as Markdown to docs/reports/
3. Saved as JSON to docs/reports/ for programmatic access
4. Logged to bot/reports/ for local audit trail
"""
from __future__ import annotations

import json
import os
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import math

import requests
from dotenv import load_dotenv
from loguru import logger

load_dotenv()

# =============================================================================
# OPTIONAL IMPORTS (graceful degradation)
# =============================================================================

try:
    from web3 import Web3

    HAS_WEB3 = True
except ImportError:
    HAS_WEB3 = False
    logger.warning("web3 not installed - on-chain data will be unavailable")

try:
    from hyperliquid.info import Info
    from hyperliquid.utils import constants as hl_constants

    HAS_HYPERLIQUID = True
except ImportError:
    HAS_HYPERLIQUID = False
    logger.warning("hyperliquid SDK not installed - CEX data will be unavailable")


# =============================================================================
# CONFIGURATION
# =============================================================================

DEPLOYER_ADDRESS = os.getenv(
    "DEPLOYER_ADDRESS", "0x57D400cED462a01Ed51a5De038F204Df49690A99"
)
TREASURY_ADDRESS = os.getenv(
    "TREASURY_ADDRESS", "0x0067F4957dea17CF76665F6A6585F6a904362106"
)
BASE_VAULT_ADDRESS = os.getenv(
    "VAULT_ADDRESS", "0xDA9765F84208F8E94225889B2C9331DCe940fB20"
)
ARB_VAULT_ADDRESS = os.getenv(
    "ARB_VAULT_ADDRESS",
    os.getenv("ARBITRUM_VAULT_ADDRESS", "0x503D930dF68a68cdFeb8DEa173ADD8DD377841FF"),
)

BASE_RPCS = os.getenv(
    "RPC_URL",
    "https://base.llamarpc.com,https://base.drpc.org,https://1rpc.io/base,https://mainnet.base.org",
).split(",")
ARB_RPCS = os.getenv(
    "ARBITRUM_RPC_URL",
    "https://arb1.arbitrum.io/rpc,https://arbitrum.llamarpc.com,https://rpc.ankr.com/arbitrum",
).split(",")

TOKENS = {
    "base": {
        "ETH": {"address": None, "decimals": 18, "native": True},
        "WETH": {
            "address": "0x4200000000000000000000000000000000000006",
            "decimals": 18,
        },
        "USDC": {
            "address": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
            "decimals": 6,
        },
        "wstETH": {
            "address": "0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
            "decimals": 18,
        },
    },
    "arbitrum": {
        "ETH": {"address": None, "decimals": 18, "native": True},
        "WETH": {
            "address": "0x82aF49447D8a07e3bd95BD0d56f35241523fBab1",
            "decimals": 18,
        },
        "USDC": {
            "address": "0xaf88d065e77c8cC2239327C5EDb3A432268e5831",
            "decimals": 6,
        },
    },
}

ERC20_BALANCE_ABI = [
    {
        "inputs": [{"name": "account", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    }
]

VAULT_ABI = [
    {
        "inputs": [],
        "name": "totalAssets",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
    {
        "inputs": [],
        "name": "totalSupply",
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view",
        "type": "function",
    },
]

DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL", "")
ETH_PRICE_FALLBACK = float(os.getenv("ETH_PRICE_USD", "2100"))


# =============================================================================
# DATA CLASSES
# =============================================================================


@dataclass
class HyperliquidData:
    connected: bool = False
    account_value_usd: float = 0.0
    total_margin_used: float = 0.0
    withdrawable_usd: float = 0.0
    positions: List[Dict[str, Any]] = field(default_factory=list)
    eth_funding_rate: float = 0.0
    eth_mark_price: float = 0.0
    eth_open_interest: float = 0.0
    total_position_notional_usd: float = 0.0
    total_unrealized_pnl: float = 0.0
    error: str = ""


@dataclass
class WalletBalance:
    address: str
    chain: str
    label: str
    balances: Dict[str, float] = field(default_factory=dict)
    total_usd: float = 0.0


@dataclass
class OnChainData:
    connected_rpcs: Dict[str, str] = field(default_factory=dict)
    wallets: List[WalletBalance] = field(default_factory=list)
    vault_total_assets: Dict[str, float] = field(default_factory=dict)
    vault_total_supply: Dict[str, float] = field(default_factory=dict)
    vault_share_price: Dict[str, float] = field(default_factory=dict)
    total_onchain_usd: float = 0.0
    error: str = ""


@dataclass
class PerformanceReport:
    timestamp: float = 0.0
    date: str = ""
    hyperliquid: HyperliquidData = field(default_factory=HyperliquidData)
    onchain: OnChainData = field(default_factory=OnChainData)
    eth_price_usd: float = 0.0
    total_assets_usd: float = 0.0
    total_liabilities_usd: float = 0.0
    solvency_ratio: float = 0.0
    net_delta_eth: float = 0.0
    daily_funding_income_usd: float = 0.0
    annualized_funding_apy: float = 0.0
    health_status: str = "UNKNOWN"
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# DATA COLLECTORS
# =============================================================================


def fetch_hyperliquid_data() -> HyperliquidData:
    """Fetch all relevant data from Hyperliquid."""
    data = HyperliquidData()

    if not HAS_HYPERLIQUID:
        data.error = "hyperliquid SDK not installed"
        return data

    try:
        info = Info(hl_constants.MAINNET_API_URL, skip_ws=True)

        state = info.user_state(DEPLOYER_ADDRESS)
        ms = state.get("marginSummary", {})

        data.connected = True
        data.account_value_usd = float(ms.get("accountValue", 0))
        data.total_margin_used = float(ms.get("totalMarginUsed", 0))
        data.withdrawable_usd = float(state.get("withdrawable", 0))

        for p in state.get("assetPositions", []):
            pos = p["position"]
            position_data = {
                "coin": pos["coin"],
                "size": float(pos["szi"]),
                "entry_price": float(pos.get("entryPx", 0)),
                "mark_price": 0.0,
                "unrealized_pnl": float(pos["unrealizedPnl"]),
                "liquidation_price": float(pos.get("liquidationPx", 0))
                if pos.get("liquidationPx")
                else 0.0,
                "leverage": pos.get("leverage", {}),
                "notional_usd": 0.0,
            }
            data.positions.append(position_data)
            data.total_unrealized_pnl += position_data["unrealized_pnl"]

        meta = info.meta_and_asset_ctxs()
        universe = meta[0]["universe"]
        ctxs = meta[1]
        for i, asset in enumerate(universe):
            if asset["name"] == "ETH":
                data.eth_funding_rate = float(ctxs[i]["funding"])
                data.eth_mark_price = float(ctxs[i]["markPx"])
                data.eth_open_interest = float(ctxs[i].get("openInterest", 0))
                break

        for pos in data.positions:
            if pos["coin"] == "ETH":
                pos["mark_price"] = data.eth_mark_price
                pos["notional_usd"] = abs(pos["size"]) * data.eth_mark_price
            data.total_position_notional_usd += pos["notional_usd"]

        logger.info(
            f"Hyperliquid: ${data.account_value_usd:.2f} equity, "
            f"{len(data.positions)} positions, "
            f"funding={data.eth_funding_rate:.8f}"
        )

    except Exception as e:
        data.error = str(e)
        logger.error(f"Hyperliquid fetch failed: {e}")

    return data


def _connect_web3(rpcs: List[str]) -> Tuple[Optional[Any], str]:
    """Try connecting to RPCs with fallback rotation."""
    if not HAS_WEB3:
        return None, ""

    for rpc in rpcs:
        rpc = rpc.strip()
        if not rpc:
            continue
        try:
            w3 = Web3(Web3.HTTPProvider(rpc, request_kwargs={"timeout": 10}))
            if w3.is_connected():
                return w3, rpc
        except Exception:
            continue
    return None, ""


def _get_wallet_balances(
    w3, chain: str, address: str, label: str, eth_price: float
) -> WalletBalance:
    """Fetch all token balances for a wallet."""
    wallet = WalletBalance(address=address, chain=chain, label=label)
    checksum_addr = Web3.to_checksum_address(address)

    for symbol, token_info in TOKENS.get(chain, {}).items():
        try:
            if token_info.get("native"):
                raw = w3.eth.get_balance(checksum_addr)
                balance = raw / (10 ** token_info["decimals"])
            else:
                contract = w3.eth.contract(
                    address=Web3.to_checksum_address(token_info["address"]),
                    abi=ERC20_BALANCE_ABI,
                )
                raw = contract.functions.balanceOf(checksum_addr).call()
                balance = raw / (10 ** token_info["decimals"])

            if balance > 0:
                wallet.balances[symbol] = balance
                if "USD" in symbol.upper():
                    wallet.total_usd += balance
                else:
                    wallet.total_usd += balance * eth_price

        except Exception as e:
            logger.debug(f"Error fetching {symbol} for {label} on {chain}: {e}")
            if "429" in str(e):
                logger.warning(
                    f"Rate limited on {chain}, skipping remaining tokens for {label}"
                )
                time.sleep(1)
                break

    return wallet


def _try_read_vault(
    w3, vault_address: str, chain: str
) -> Tuple[float, float, float]:
    """Try to read ERC-4626 vault data."""
    try:
        checksum = Web3.to_checksum_address(vault_address)
        code = w3.eth.get_code(checksum)
        if code == b"" or code == b"0x" or len(code) < 10:
            logger.debug(f"No contract code at vault {vault_address} on {chain}")
            return 0.0, 0.0, 0.0

        vault = w3.eth.contract(address=checksum, abi=VAULT_ABI)
        total_assets = vault.functions.totalAssets().call() / 1e18
        total_supply = vault.functions.totalSupply().call() / 1e18
        share_price = total_assets / total_supply if total_supply > 0 else 0.0
        return total_assets, total_supply, share_price
    except Exception as e:
        logger.debug(f"Vault read failed on {chain}: {e}")
        return 0.0, 0.0, 0.0


def fetch_onchain_data(eth_price: float) -> OnChainData:
    """Fetch all on-chain data across Base and Arbitrum."""
    data = OnChainData()

    if not HAS_WEB3:
        data.error = "web3 not installed"
        return data

    wallet_configs = {
        "base": [
            (DEPLOYER_ADDRESS, "Deployer"),
            (TREASURY_ADDRESS, "Treasury"),
        ],
        "arbitrum": [
            (DEPLOYER_ADDRESS, "Deployer"),
        ],
    }

    vault_configs = {
        "base": BASE_VAULT_ADDRESS,
        "arbitrum": ARB_VAULT_ADDRESS,
    }

    rpc_configs = {
        "base": BASE_RPCS,
        "arbitrum": ARB_RPCS,
    }

    for chain, rpcs in rpc_configs.items():
        w3, rpc_used = _connect_web3(rpcs)
        if not w3:
            logger.warning(f"Could not connect to any {chain} RPC")
            continue

        data.connected_rpcs[chain] = rpc_used
        logger.info(f"Connected to {chain}: {rpc_used}")

        for address, label in wallet_configs.get(chain, []):
            wallet = _get_wallet_balances(w3, chain, address, label, eth_price)
            if wallet.balances:
                data.wallets.append(wallet)
                data.total_onchain_usd += wallet.total_usd
            time.sleep(0.3)

        vault_addr = vault_configs.get(chain)
        if vault_addr:
            ta, ts, sp = _try_read_vault(w3, vault_addr, chain)
            if ta > 0:
                data.vault_total_assets[chain] = ta
                data.vault_total_supply[chain] = ts
                data.vault_share_price[chain] = sp
                data.total_onchain_usd += ta * eth_price

    return data


# =============================================================================
# MULTI-VENUE FUNDING RATE FETCHERS (mirrors frontend /api/apy)
# =============================================================================


def _fetch_binance_funding(symbol: str = "ETH") -> Optional[Dict[str, Any]]:
    """Fetch latest funding rate from Binance Futures."""
    try:
        res = requests.get(
            f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={symbol.upper()}USDT&limit=1",
            timeout=10,
        )
        if res.ok:
            data = res.json()
            if isinstance(data, list) and len(data) > 0:
                rate = float(data[0].get("fundingRate", 0))
                return {"rate": rate, "annual": rate * 3 * 365, "interval": "8h"}
    except Exception as e:
        logger.debug(f"Binance funding fetch failed: {e}")
    return None


def _fetch_bybit_funding(symbol: str = "ETH") -> Optional[Dict[str, Any]]:
    """Fetch latest funding rate from Bybit."""
    try:
        res = requests.get(
            f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={symbol.upper()}USDT",
            timeout=10,
        )
        if res.ok:
            data = res.json()
            if data.get("retCode") == 0:
                tickers = data.get("result", {}).get("list", [])
                if tickers:
                    rate = float(tickers[0].get("fundingRate", 0))
                    return {"rate": rate, "annual": rate * 3 * 365, "interval": "8h"}
    except Exception as e:
        logger.debug(f"Bybit funding fetch failed: {e}")
    return None


def _fetch_okx_funding(symbol: str = "ETH") -> Optional[Dict[str, Any]]:
    """Fetch latest funding rate from OKX."""
    try:
        res = requests.get(
            f"https://www.okx.com/api/v5/public/funding-rate?instId={symbol.upper()}-USDT-SWAP",
            timeout=10,
        )
        if res.ok:
            data = res.json()
            if data.get("code") == "0":
                rates = data.get("data", [])
                if rates:
                    rate = float(rates[0].get("fundingRate", 0))
                    return {"rate": rate, "annual": rate * 3 * 365, "interval": "8h"}
    except Exception as e:
        logger.debug(f"OKX funding fetch failed: {e}")
    return None


def _fetch_multi_venue_funding() -> Dict[str, Dict[str, Any]]:
    """Fetch funding rates from Binance, Bybit, OKX. HL is added separately."""
    venues: Dict[str, Dict[str, Any]] = {}

    bn = _fetch_binance_funding()
    if bn:
        venues["binance"] = bn

    bb = _fetch_bybit_funding()
    if bb:
        venues["bybit"] = bb

    okx = _fetch_okx_funding()
    if okx:
        venues["okx"] = okx

    logger.info(
        f"Multi-venue funding rates: "
        + ", ".join(f"{k}={v['rate']*100:.6f}% ({v['interval']})" for k, v in venues.items())
    )
    return venues


def _fetch_staking_yield() -> float:
    """Fetch wstETH staking APY from Lido API. Returns decimal (e.g. 0.035)."""
    # Try SMA APR
    try:
        res = requests.get(
            "https://eth-api.lido.fi/v1/protocol/steth/apr/sma",
            timeout=10,
        )
        if res.ok:
            data = res.json()
            sma_apr = data.get("data", {}).get("smaApr")
            if sma_apr is not None:
                yield_val = float(sma_apr) / 100
                logger.info(f"Lido staking APY (SMA): {yield_val*100:.2f}%")
                return yield_val
    except Exception:
        pass

    # Fallback: last APR
    try:
        res = requests.get(
            "https://eth-api.lido.fi/v1/protocol/steth/apr/last",
            timeout=10,
        )
        if res.ok:
            data = res.json()
            apr = data.get("data", {}).get("apr")
            if apr is not None:
                yield_val = float(apr) / 100
                logger.info(f"Lido staking APY (last): {yield_val*100:.2f}%")
                return yield_val
    except Exception:
        pass

    logger.warning("Could not fetch Lido staking yield, using 3.5% fallback")
    return 0.035


# =============================================================================
# REPORT GENERATION
# =============================================================================


def generate_report() -> PerformanceReport:
    """Collect all data and generate the performance report."""
    now = datetime.now(tz=timezone.utc)

    report = PerformanceReport(
        timestamp=now.timestamp(),
        date=now.strftime("%Y-%m-%d"),
    )

    # 1. Fetch Hyperliquid data
    report.hyperliquid = fetch_hyperliquid_data()
    report.eth_price_usd = report.hyperliquid.eth_mark_price or ETH_PRICE_FALLBACK

    # 2. Fetch on-chain data
    report.onchain = fetch_onchain_data(report.eth_price_usd)

    # 3. Calculate derived metrics
    report.total_assets_usd = (
        report.hyperliquid.account_value_usd + report.onchain.total_onchain_usd
    )

    # Net delta calculation
    onchain_eth_exposure = 0.0
    for wallet in report.onchain.wallets:
        for symbol, amount in wallet.balances.items():
            if symbol in ("ETH", "WETH", "wstETH", "cbETH"):
                onchain_eth_exposure += amount

    for chain, ta in report.onchain.vault_total_assets.items():
        onchain_eth_exposure += ta

    hl_short_eth = 0.0
    for pos in report.hyperliquid.positions:
        if pos["coin"] == "ETH" and pos["size"] < 0:
            hl_short_eth += abs(pos["size"])

    report.net_delta_eth = onchain_eth_exposure - hl_short_eth

    # Solvency ratio
    total_vault_assets_eth = sum(report.onchain.vault_total_assets.values())
    if total_vault_assets_eth > 0:
        total_backing = (
            report.hyperliquid.account_value_usd / report.eth_price_usd
        ) + onchain_eth_exposure
        report.solvency_ratio = total_backing / total_vault_assets_eth
    else:
        report.solvency_ratio = 1.0

    # ── Yield Calculation (mirrors frontend /api/apy exactly) ──────────────
    # The frontend picks the BEST funding rate across 4 venues (HL, Binance,
    # Bybit, OKX), applies 3x leverage to BOTH funding AND staking yield,
    # and uses exponential compounding: APY = exp(logReturn) - 1
    #
    # NOTE: Hyperliquid funding is per 1h (annual = rate * 24 * 365)
    #       Other venues are per 8h (annual = rate * 3 * 365)

    LEVERAGE = 3.0
    SPREAD_EDGE = 0.0005
    TURNOVER_RATE = 0.1
    COST_RATE = 0.01

    # Fetch multi-venue funding rates
    multi_venue_rates = _fetch_multi_venue_funding()

    # Add Hyperliquid from our already-fetched data
    if report.hyperliquid.eth_funding_rate != 0:
        hl_annual = report.hyperliquid.eth_funding_rate * 24 * 365  # HL is 1h interval
        multi_venue_rates["hyperliquid"] = {
            "rate": report.hyperliquid.eth_funding_rate,
            "annual": hl_annual,
            "interval": "1h",
        }

    # Fetch staking yield
    staking_yield = _fetch_staking_yield()

    # Find best positive funding venue
    best_venue = "none"
    best_annual_funding = 0.0
    for name, data in multi_venue_rates.items():
        if data["annual"] > best_annual_funding:
            best_annual_funding = data["annual"]
            best_venue = name

    if best_annual_funding < 0:
        best_annual_funding = 0.0

    # Calculate protocol APY using same formula as frontend
    log_return = (
        LEVERAGE * best_annual_funding
        + LEVERAGE * staking_yield
        + TURNOVER_RATE * SPREAD_EDGE
        - COST_RATE
    )
    protocol_apy = (math.exp(log_return) - 1) * 100  # as percentage

    # Daily funding income from our actual HL position
    total_short_notional = sum(
        abs(p["size"]) * report.eth_price_usd
        for p in report.hyperliquid.positions
        if p["coin"] == "ETH" and p["size"] < 0
    )
    if total_short_notional > 0 and report.hyperliquid.eth_funding_rate != 0:
        # HL funding is per 1h, so daily = rate * 24
        report.daily_funding_income_usd = (
            total_short_notional * abs(report.hyperliquid.eth_funding_rate) * 24
        )
    else:
        report.daily_funding_income_usd = 0.0

    # Effective leverage on our actual position
    effective_leverage = LEVERAGE
    if report.hyperliquid.total_margin_used > 0 and total_short_notional > 0:
        effective_leverage = total_short_notional / report.hyperliquid.total_margin_used

    report.annualized_funding_apy = protocol_apy

    # Store detailed breakdown
    hl_annual_pct = (report.hyperliquid.eth_funding_rate * 24 * 365 * 100) if report.hyperliquid.eth_funding_rate else 0
    report._raw_funding_apy = hl_annual_pct
    report._best_venue = best_venue
    report._best_annual_funding_pct = best_annual_funding * 100
    report._leveraged_funding_apy = best_annual_funding * LEVERAGE * 100
    report._effective_leverage = effective_leverage
    report._staking_apy = staking_yield * 100
    report._funding_apy_on_total = protocol_apy
    report._all_venues = multi_venue_rates

    # Health assessment
    report.warnings = []
    if not report.hyperliquid.connected:
        report.warnings.append("Hyperliquid API unreachable")
    if not report.onchain.connected_rpcs:
        report.warnings.append("No on-chain RPCs connected")
    if report.net_delta_eth > 0.01:
        report.warnings.append(
            f"Net long delta: {report.net_delta_eth:.4f} ETH (not fully hedged)"
        )
    if report.solvency_ratio < 1.0:
        report.warnings.append(
            f"Solvency ratio below 100%: {report.solvency_ratio*100:.1f}%"
        )

    for pos in report.hyperliquid.positions:
        if pos["liquidation_price"] > 0 and pos["coin"] == "ETH":
            distance_pct = (
                abs(pos["liquidation_price"] - report.eth_price_usd)
                / report.eth_price_usd
                * 100
            )
            if distance_pct < 20:
                report.warnings.append(
                    f"ETH liquidation within {distance_pct:.1f}% (${pos['liquidation_price']:.0f})"
                )

    if not report.warnings:
        report.health_status = "HEALTHY"
    elif any(
        "solvency" in w.lower() or "liquidation" in w.lower()
        for w in report.warnings
    ):
        report.health_status = "WARNING"
    else:
        report.health_status = "MONITORING"

    return report


# =============================================================================
# OUTPUT FORMATTERS
# =============================================================================


def format_markdown(report: PerformanceReport) -> str:
    """Generate detailed Markdown report."""
    lines = [
        "# Kerne Protocol Daily Performance Report",
        f"**Date:** {report.date}",
        f"**Generated:** {datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"**ETH Price:** ${report.eth_price_usd:,.2f}",
        f"**Health:** {report.health_status}",
        "",
    ]

    if report.warnings:
        lines.append("### Warnings")
        for w in report.warnings:
            lines.append(f"- {w}")
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Portfolio Summary",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Total Assets (USD)** | ${report.total_assets_usd:,.2f} |",
            f"| **On-Chain Assets** | ${report.onchain.total_onchain_usd:,.2f} |",
            f"| **Hyperliquid Equity** | ${report.hyperliquid.account_value_usd:,.2f} |",
            f"| **Net Delta (ETH)** | {report.net_delta_eth:+.6f} |",
            f"| **Solvency Ratio** | {report.solvency_ratio*100:.1f}% |",
            "",
            "---",
            "",
            "## Hyperliquid (Off-Chain)",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **Account Value** | ${report.hyperliquid.account_value_usd:,.2f} |",
            f"| **Margin Used** | ${report.hyperliquid.total_margin_used:,.2f} |",
            f"| **Withdrawable** | ${report.hyperliquid.withdrawable_usd:,.2f} |",
            f"| **Unrealized P&L** | ${report.hyperliquid.total_unrealized_pnl:+,.2f} |",
            f"| **ETH Funding Rate (HL)** | {report.hyperliquid.eth_funding_rate*100:.6f}% (1h) |",
            f"| **Effective Leverage** | {getattr(report, '_effective_leverage', 0):.1f}x |",
            f"| **Annualized Protocol APY** | {report.annualized_funding_apy:.2f}% |",
            "",
        ]
    )

    if report.hyperliquid.positions:
        lines.extend(
            [
                "### Open Positions",
                "",
                "| Coin | Size | Entry | Mark | uPnL | Liq Price |",
                "|------|------|-------|------|------|-----------|",
            ]
        )
        for pos in report.hyperliquid.positions:
            direction = "SHORT" if pos["size"] < 0 else "LONG"
            lines.append(
                f"| {pos['coin']} | {pos['size']:+.4f} ({direction}) | "
                f"${pos['entry_price']:,.2f} | ${pos['mark_price']:,.2f} | "
                f"${pos['unrealized_pnl']:+,.2f} | "
                f"${pos['liquidation_price']:,.2f} |"
            )
        lines.append("")
    else:
        lines.append("*No open positions*")
        lines.append("")

    lines.extend(["---", "", "## On-Chain Assets", ""])

    for chain, rpc in report.onchain.connected_rpcs.items():
        lines.append(f"**{chain.upper()}** (via `{rpc}`)")
        lines.append("")

    if report.onchain.wallets:
        lines.extend(
            [
                "### Wallet Balances",
                "",
                "| Wallet | Chain | Token | Amount | USD Value |",
                "|--------|-------|-------|--------|-----------|",
            ]
        )
        for wallet in report.onchain.wallets:
            for symbol, amount in wallet.balances.items():
                if "USD" in symbol.upper():
                    usd_val = amount
                else:
                    usd_val = amount * report.eth_price_usd
                lines.append(
                    f"| {wallet.label} | {wallet.chain} | {symbol} | "
                    f"{amount:.6f} | ${usd_val:,.2f} |"
                )
        lines.append("")

    if report.onchain.vault_total_assets:
        lines.extend(
            [
                "### Vault Status",
                "",
                "| Chain | Total Assets | Total Supply | Share Price |",
                "|-------|-------------|-------------|-------------|",
            ]
        )
        for chain in report.onchain.vault_total_assets:
            ta = report.onchain.vault_total_assets[chain]
            ts = report.onchain.vault_total_supply.get(chain, 0)
            sp = report.onchain.vault_share_price.get(chain, 0)
            lines.append(
                f"| {chain} | {ta:.6f} ETH | {ts:.6f} | {sp:.6f} |"
            )
        lines.append("")

    lines.extend(
        [
            "---",
            "",
            "## Yield Metrics",
            "",
            "| Metric | Value |",
            "|--------|-------|",
            f"| **HL Funding Rate (1h)** | {report.hyperliquid.eth_funding_rate*100:.6f}% |",
            f"| **HL Funding APY (annualized)** | {getattr(report, '_raw_funding_apy', 0):.2f}% |",
            f"| **Best Venue** | {getattr(report, '_best_venue', 'none')} ({getattr(report, '_best_annual_funding_pct', 0):.2f}% annual) |",
            f"| **Best Venue × 3x Leverage** | {getattr(report, '_leveraged_funding_apy', 0):.2f}% |",
            f"| **wstETH Staking APY** | {getattr(report, '_staking_apy', 3.5):.1f}% |",
            f"| **Combined Protocol APY** | **{report.annualized_funding_apy:.2f}%** |",
            f"| **Est. Daily Funding Income (HL)** | ${report.daily_funding_income_usd:,.4f} |",
            "",
            "> *Formula: APY = exp(3 × best_funding + 3 × staking + spread - costs) - 1. Matches kerne.ai live APY.*",
            "",
            "---",
            "",
            "*Report generated by Kerne Daily Performance Reporter v2.1*",
        ]
    )

    return "\n".join(lines)


def format_discord_embed(report: PerformanceReport) -> Dict[str, Any]:
    """Generate Discord webhook payload with rich embed."""
    color_map = {
        "HEALTHY": 0x00FF00,
        "MONITORING": 0xFFAA00,
        "WARNING": 0xFF0000,
        "UNKNOWN": 0x808080,
    }
    color = color_map.get(report.health_status, 0x808080)

    status_emoji = {
        "HEALTHY": "🟢",
        "MONITORING": "🟡",
        "WARNING": "🔴",
        "UNKNOWN": "⚪",
    }.get(report.health_status, "⚪")

    fields = [
        {
            "name": "💰 Total Assets",
            "value": f"${report.total_assets_usd:,.2f}",
            "inline": True,
        },
        {
            "name": "🔮 HL Equity",
            "value": f"${report.hyperliquid.account_value_usd:,.2f}",
            "inline": True,
        },
        {
            "name": "⛓️ On-Chain",
            "value": f"${report.onchain.total_onchain_usd:,.2f}",
            "inline": True,
        },
        {
            "name": "📊 Net Delta",
            "value": f"{report.net_delta_eth:+.6f} ETH",
            "inline": True,
        },
        {
            "name": "🛡️ Solvency",
            "value": f"{report.solvency_ratio*100:.1f}%",
            "inline": True,
        },
        {
            "name": "💵 ETH Price",
            "value": f"${report.eth_price_usd:,.2f}",
            "inline": True,
        },
        {
            "name": "📈 Funding Rate (1h)",
            "value": f"{report.hyperliquid.eth_funding_rate*100:.6f}%",
            "inline": True,
        },
        {
            "name": "🔥 Protocol APY",
            "value": f"{report.annualized_funding_apy:.2f}%\n(Best: {getattr(report, '_best_venue', '?')} | Staking: {getattr(report, '_staking_apy', 3.5):.1f}%)",
            "inline": True,
        },
        {
            "name": "💸 Daily Funding Income",
            "value": f"${report.daily_funding_income_usd:,.4f}",
            "inline": True,
        },
    ]

    # Positions summary
    if report.hyperliquid.positions:
        pos_lines = []
        for pos in report.hyperliquid.positions:
            direction = "SHORT" if pos["size"] < 0 else "LONG"
            pos_lines.append(
                f"{pos['coin']}: {pos['size']:+.4f} ({direction}) | "
                f"uPnL: ${pos['unrealized_pnl']:+,.2f}"
            )
        fields.append(
            {
                "name": "📋 Positions",
                "value": "\n".join(pos_lines) or "None",
                "inline": False,
            }
        )
    else:
        fields.append(
            {"name": "📋 Positions", "value": "No open positions", "inline": False}
        )

    # Wallet breakdown
    if report.onchain.wallets:
        wallet_lines = []
        for wallet in report.onchain.wallets:
            tokens = ", ".join(
                f"{amt:.4f} {sym}" for sym, amt in wallet.balances.items()
            )
            wallet_lines.append(
                f"**{wallet.label}** ({wallet.chain}): {tokens}"
            )
        fields.append(
            {
                "name": "👛 Wallets",
                "value": "\n".join(wallet_lines[:5]) or "None",
                "inline": False,
            }
        )

    # Warnings
    if report.warnings:
        fields.append(
            {
                "name": "⚠️ Warnings",
                "value": "\n".join(f"• {w}" for w in report.warnings),
                "inline": False,
            }
        )

    embed = {
        "title": f"{status_emoji} Daily Performance Report - {report.date}",
        "color": color,
        "fields": fields,
        "footer": {
            "text": f"Kerne Protocol | {datetime.now(tz=timezone.utc).strftime('%H:%M UTC')}"
        },
        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
    }

    return {"embeds": [embed], "username": "Kerne Performance Bot"}


def format_json(report: PerformanceReport) -> Dict[str, Any]:
    """Convert report to JSON-serializable dict."""
    return {
        "timestamp": report.timestamp,
        "date": report.date,
        "eth_price_usd": report.eth_price_usd,
        "health_status": report.health_status,
        "summary": {
            "total_assets_usd": report.total_assets_usd,
            "onchain_assets_usd": report.onchain.total_onchain_usd,
            "hyperliquid_equity_usd": report.hyperliquid.account_value_usd,
            "net_delta_eth": report.net_delta_eth,
            "solvency_ratio": report.solvency_ratio,
        },
        "yield": {
            "hl_funding_rate_1h": report.hyperliquid.eth_funding_rate,
            "hl_funding_apy_pct": getattr(report, '_raw_funding_apy', 0),
            "best_venue": getattr(report, '_best_venue', 'none'),
            "best_venue_annual_funding_pct": getattr(report, '_best_annual_funding_pct', 0),
            "leveraged_funding_apy_pct": getattr(report, '_leveraged_funding_apy', 0),
            "staking_apy_pct": getattr(report, '_staking_apy', 3.5),
            "effective_leverage": getattr(report, '_effective_leverage', 0),
            "combined_protocol_apy_pct": report.annualized_funding_apy,
            "daily_funding_income_usd": report.daily_funding_income_usd,
            "all_venues": {k: {"rate": v["rate"], "annual_pct": v["annual"] * 100, "interval": v["interval"]} for k, v in getattr(report, '_all_venues', {}).items()},
        },
        "hyperliquid": {
            "connected": report.hyperliquid.connected,
            "account_value_usd": report.hyperliquid.account_value_usd,
            "margin_used": report.hyperliquid.total_margin_used,
            "withdrawable_usd": report.hyperliquid.withdrawable_usd,
            "unrealized_pnl": report.hyperliquid.total_unrealized_pnl,
            "eth_mark_price": report.hyperliquid.eth_mark_price,
            "eth_open_interest": report.hyperliquid.eth_open_interest,
            "positions": report.hyperliquid.positions,
        },
        "onchain": {
            "connected_rpcs": report.onchain.connected_rpcs,
            "wallets": [
                {
                    "label": w.label,
                    "chain": w.chain,
                    "address": w.address,
                    "balances": w.balances,
                    "total_usd": w.total_usd,
                }
                for w in report.onchain.wallets
            ],
            "vaults": {
                chain: {
                    "total_assets": report.onchain.vault_total_assets.get(chain, 0),
                    "total_supply": report.onchain.vault_total_supply.get(chain, 0),
                    "share_price": report.onchain.vault_share_price.get(chain, 0),
                }
                for chain in report.onchain.vault_total_assets
            },
        },
        "warnings": report.warnings,
    }


# =============================================================================
# RUNNER
# =============================================================================


class DailyPerformanceReporter:
    """Main runner that generates, saves, and posts the daily report."""

    def __init__(
        self,
        report_dir: str = "docs/reports",
        local_dir: str = "bot/reports",
    ):
        self.report_dir = Path(report_dir)
        self.local_dir = Path(local_dir)
        self.report_dir.mkdir(parents=True, exist_ok=True)
        self.local_dir.mkdir(parents=True, exist_ok=True)

    def post_to_discord(self, report: PerformanceReport) -> bool:
        """Post report to Discord webhook."""
        webhook = DISCORD_WEBHOOK_URL
        if not webhook or "your_discord_webhook_url" in webhook:
            logger.warning("Discord webhook not configured, skipping post")
            return False

        try:
            payload = format_discord_embed(report)
            response = requests.post(webhook, json=payload, timeout=10)
            response.raise_for_status()
            logger.success("Posted daily performance report to Discord")
            return True
        except Exception as e:
            logger.error(f"Failed to post to Discord: {e}")
            return False

    def save_markdown(self, report: PerformanceReport) -> Path:
        """Save Markdown report."""
        content = format_markdown(report)
        filepath = self.report_dir / f"DAILY_PERFORMANCE_{report.date}.md"
        filepath.write_text(content, encoding="utf-8")
        logger.success(f"Saved markdown report: {filepath}")
        return filepath

    def save_json(self, report: PerformanceReport) -> Path:
        """Save JSON metrics."""
        data = format_json(report)
        filepath = self.report_dir / f"daily_performance_{report.date}.json"
        filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")
        logger.info(f"Saved JSON metrics: {filepath}")

        # Also save to local bot/reports/ for audit trail
        local_path = self.local_dir / f"performance_{report.date}.json"
        local_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return filepath

    def run(
        self,
        post_discord: bool = True,
        save_files: bool = True,
    ) -> PerformanceReport:
        """Run the full report generation pipeline."""
        logger.info("=" * 60)
        logger.info("KERNE DAILY PERFORMANCE REPORT")
        logger.info("=" * 60)

        report = generate_report()

        logger.info(
            f"Report: ${report.total_assets_usd:,.2f} total | "
            f"HL: ${report.hyperliquid.account_value_usd:,.2f} | "
            f"On-chain: ${report.onchain.total_onchain_usd:,.2f} | "
            f"Delta: {report.net_delta_eth:+.6f} ETH | "
            f"Health: {report.health_status}"
        )

        if save_files:
            self.save_markdown(report)
            self.save_json(report)

        if post_discord:
            self.post_to_discord(report)

        logger.info("=" * 60)
        return report


# =============================================================================
# CLI ENTRY POINT
# =============================================================================


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Kerne Daily Performance Report")
    parser.add_argument(
        "--no-discord", action="store_true", help="Skip Discord posting"
    )
    parser.add_argument(
        "--no-save", action="store_true", help="Skip saving report files"
    )
    parser.add_argument(
        "--console", action="store_true", help="Print report to console"
    )
    args = parser.parse_args()

    reporter = DailyPerformanceReporter()

    if args.console:
        report = generate_report()
        print(format_markdown(report))
    else:
        reporter.run(
            post_discord=not args.no_discord,
            save_files=not args.no_save,
        )


if __name__ == "__main__":
    main()
