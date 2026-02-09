# Created: 2026-02-06
"""
Kerne Unified API Connector — Free API aggregation layer.

Pulls real-time data from free public APIs (no keys required):
- Prices: CoinGecko, DeFiLlama, Binance public
- Funding Rates: Hyperliquid, Binance, Bybit (public endpoints)
- LST Yields: Lido API, DeFiLlama yields
- Gas: Base RPC on-chain
- DeFi Context: DeFiLlama protocol TVL/yields for comparison

All data is cached with configurable TTLs to respect rate limits.
"""

import os
import sys
import json
import time
import threading
from typing import Dict, Optional, List, Tuple, Any
from dataclasses import dataclass, field
from pathlib import Path
from loguru import logger

try:
    import requests
except ImportError:
    requests = None
    logger.warning("requests not installed — run: pip install requests")


# =============================================================================
# CACHE
# =============================================================================

@dataclass
class CacheEntry:
    data: Any
    timestamp: float
    ttl: float

    @property
    def expired(self) -> bool:
        return (time.time() - self.timestamp) > self.ttl


class TTLCache:
    """Thread-safe TTL cache for API responses."""

    def __init__(self):
        self._store: Dict[str, CacheEntry] = {}
        self._lock = threading.Lock()

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            entry = self._store.get(key)
            if entry and not entry.expired:
                return entry.data
            return None

    def set(self, key: str, data: Any, ttl: float = 30.0):
        with self._lock:
            self._store[key] = CacheEntry(data=data, timestamp=time.time(), ttl=ttl)

    def clear(self):
        with self._lock:
            self._store.clear()


_cache = TTLCache()

# Persistent disk cache location
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _http_get(url: str, headers: Optional[Dict] = None, timeout: int = 10) -> Optional[Dict]:
    """Safe HTTP GET with error handling."""
    if requests is None:
        return None
    try:
        resp = requests.get(url, headers=headers or {}, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()
        logger.debug(f"HTTP {resp.status_code} from {url[:80]}")
    except requests.exceptions.Timeout:
        logger.debug(f"Timeout: {url[:80]}")
    except Exception as e:
        logger.debug(f"HTTP error for {url[:80]}: {e}")
    return None


# =============================================================================
# PRICE FEEDS (Free, no API key)
# =============================================================================

class PriceFeed:
    """
    Aggregated price feed from multiple free sources.
    Priority: CoinGecko → DeFiLlama → Binance public → fallback.
    """

    # CoinGecko IDs for tokens we care about
    CG_IDS = {
        "ETH": "ethereum",
        "WETH": "ethereum",
        "WSTETH": "wrapped-steth",
        "CBETH": "coinbase-wrapped-staked-eth",
        "RETH": "rocket-pool-eth",
        "USDC": "usd-coin",
        "BTC": "bitcoin",
    }

    # DeFiLlama coin keys (chain:address format)
    LLAMA_KEYS = {
        "ETH": "coingecko:ethereum",
        "WETH": "base:0x4200000000000000000000000000000000000006",
        "WSTETH": "base:0xc1CBa3fCea344f92D9239c08C0568f6F2F0ee452",
        "CBETH": "base:0x2Ae3F1Ec7F1F5012CFEab0185bfc7aa3cf0DEc22",
        "USDC": "coingecko:usd-coin",
    }

    # Binance public ticker symbols
    BINANCE_SYMBOLS = {
        "ETH": "ETHUSDT",
        "BTC": "BTCUSDT",
        "WSTETH": "WSTETHETH",  # wstETH/ETH pair
    }

    @staticmethod
    def get_price(symbol: str = "ETH") -> float:
        """Get price with multi-source fallback. Returns USD price."""
        symbol = symbol.upper()
        cache_key = f"price:{symbol}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        price = 0.0

        # Source 1: CoinGecko (free, 10-30 req/min)
        price = PriceFeed._coingecko_price(symbol)

        # Source 2: DeFiLlama (free, generous limits)
        if price == 0.0:
            price = PriceFeed._defillama_price(symbol)

        # Source 3: Binance public API (free, no key)
        if price == 0.0:
            price = PriceFeed._binance_price(symbol)

        if price > 0:
            _cache.set(cache_key, price, ttl=30.0)  # 30s cache

        return price

    @staticmethod
    def get_prices_batch(symbols: List[str]) -> Dict[str, float]:
        """Batch price fetch — more efficient for multiple tokens."""
        results = {}

        # Try CoinGecko batch first
        cg_ids = []
        symbol_map = {}
        for s in symbols:
            s_upper = s.upper()
            cg_id = PriceFeed.CG_IDS.get(s_upper)
            if cg_id and cg_id not in symbol_map:
                cg_ids.append(cg_id)
                symbol_map[cg_id] = s_upper

        if cg_ids:
            ids_str = ",".join(cg_ids)
            url = f"https://api.coingecko.com/api/v3/simple/price?ids={ids_str}&vs_currencies=usd"
            data = _http_get(url)
            if data:
                for cg_id, s_upper in symbol_map.items():
                    price = data.get(cg_id, {}).get("usd", 0.0)
                    if price > 0:
                        results[s_upper] = price
                        _cache.set(f"price:{s_upper}", price, ttl=30.0)

        # Fill remaining with individual calls
        for s in symbols:
            s_upper = s.upper()
            if s_upper not in results:
                price = PriceFeed.get_price(s_upper)
                if price > 0:
                    results[s_upper] = price

        return results

    @staticmethod
    def _coingecko_price(symbol: str) -> float:
        cg_id = PriceFeed.CG_IDS.get(symbol)
        if not cg_id:
            return 0.0
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={cg_id}&vs_currencies=usd"
        data = _http_get(url)
        if data:
            return data.get(cg_id, {}).get("usd", 0.0)
        return 0.0

    @staticmethod
    def _defillama_price(symbol: str) -> float:
        llama_key = PriceFeed.LLAMA_KEYS.get(symbol)
        if not llama_key:
            return 0.0
        url = f"https://coins.llama.fi/prices/current/{llama_key}"
        data = _http_get(url)
        if data and "coins" in data:
            coin_data = data["coins"].get(llama_key, {})
            return coin_data.get("price", 0.0)
        return 0.0

    @staticmethod
    def _binance_price(symbol: str) -> float:
        bn_sym = PriceFeed.BINANCE_SYMBOLS.get(symbol)
        if not bn_sym:
            return 0.0
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={bn_sym}"
        data = _http_get(url)
        if data and "price" in data:
            price = float(data["price"])
            # Handle ETH-denominated pairs
            if bn_sym.endswith("ETH"):
                eth_price = PriceFeed._binance_price("ETH")
                return price * eth_price if eth_price > 0 else 0.0
            return price
        return 0.0


# =============================================================================
# FUNDING RATE AGGREGATOR (Free public endpoints)
# =============================================================================

class FundingRateAggregator:
    """
    Aggregates funding rates from multiple CEXs using free public APIs.
    No API keys required for market data endpoints.
    """

    @staticmethod
    def get_all_funding_rates(symbol: str = "ETH") -> Dict[str, Dict]:
        """
        Returns funding rates from all available venues.
        {
            "hyperliquid": {"rate": 0.0001, "annual": 0.0876, "interval": "1h"},
            "binance": {"rate": 0.0001, "annual": 0.0876, "interval": "8h"},
            "bybit": {"rate": 0.0001, "annual": 0.0876, "interval": "8h"},
            "average_annual": 0.087,
            "best_venue": "hyperliquid"
        }
        """
        cache_key = f"funding_all:{symbol}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        rates = {}

        # Hyperliquid (1h funding, free API)
        hl_rate = FundingRateAggregator._hyperliquid_funding(symbol)
        if hl_rate is not None:
            annual = hl_rate * 24 * 365
            rates["hyperliquid"] = {"rate": hl_rate, "annual": annual, "interval": "1h"}

        # Binance (8h funding, free public API)
        bn_rate = FundingRateAggregator._binance_funding(symbol)
        if bn_rate is not None:
            annual = bn_rate * 3 * 365  # 3x per day
            rates["binance"] = {"rate": bn_rate, "annual": annual, "interval": "8h"}

        # Bybit (8h funding, free public API)
        bb_rate = FundingRateAggregator._bybit_funding(symbol)
        if bb_rate is not None:
            annual = bb_rate * 3 * 365
            rates["bybit"] = {"rate": bb_rate, "annual": annual, "interval": "8h"}

        # OKX (8h funding, free public API)
        okx_rate = FundingRateAggregator._okx_funding(symbol)
        if okx_rate is not None:
            annual = okx_rate * 3 * 365
            rates["okx"] = {"rate": okx_rate, "annual": annual, "interval": "8h"}

        # Calculate aggregate stats
        if rates:
            annuals = [v["annual"] for v in rates.values() if isinstance(v, dict) and "annual" in v]
            rates["average_annual"] = sum(annuals) / len(annuals) if annuals else 0.0
            rates["best_venue"] = max(
                [(k, v["annual"]) for k, v in rates.items() if isinstance(v, dict) and "annual" in v],
                key=lambda x: x[1],
                default=("none", 0.0)
            )[0]

        _cache.set(cache_key, rates, ttl=60.0)  # 60s cache
        return rates

    @staticmethod
    def get_best_funding_rate(symbol: str = "ETH") -> Tuple[float, str]:
        """Returns (annual_rate, venue_name) for the best funding opportunity."""
        all_rates = FundingRateAggregator.get_all_funding_rates(symbol)
        best_venue = all_rates.get("best_venue", "none")
        if best_venue != "none" and best_venue in all_rates:
            return (all_rates[best_venue]["annual"], best_venue)
        return (0.0, "none")

    @staticmethod
    def _hyperliquid_funding(symbol: str) -> Optional[float]:
        """Hyperliquid funding rate — free API, 1-hour interval."""
        url = "https://api.hyperliquid.xyz/info"
        payload = {"type": "metaAndAssetCtxs"}
        try:
            if requests is None:
                return None
            resp = requests.post(url, json=payload, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if isinstance(data, list) and len(data) >= 2:
                    meta = data[0]
                    asset_ctxs = data[1]
                    # Find ETH index
                    universe = meta.get("universe", [])
                    for i, asset in enumerate(universe):
                        if asset.get("name", "").upper() == symbol.upper():
                            if i < len(asset_ctxs):
                                return float(asset_ctxs[i].get("funding", 0.0))
        except Exception as e:
            logger.debug(f"Hyperliquid funding error: {e}")
        return None

    @staticmethod
    def _binance_funding(symbol: str) -> Optional[float]:
        """Binance funding rate — free public API, 8-hour interval."""
        bn_symbol = f"{symbol.upper()}USDT"
        url = f"https://fapi.binance.com/fapi/v1/fundingRate?symbol={bn_symbol}&limit=1"
        data = _http_get(url)
        if data and isinstance(data, list) and len(data) > 0:
            return float(data[0].get("fundingRate", 0.0))
        return None

    @staticmethod
    def _bybit_funding(symbol: str) -> Optional[float]:
        """Bybit funding rate — free public API, 8-hour interval."""
        bb_symbol = f"{symbol.upper()}USDT"
        url = f"https://api.bybit.com/v5/market/tickers?category=linear&symbol={bb_symbol}"
        data = _http_get(url)
        if data and data.get("retCode") == 0:
            tickers = data.get("result", {}).get("list", [])
            if tickers:
                rate_str = tickers[0].get("fundingRate", "0")
                return float(rate_str)
        return None

    @staticmethod
    def _okx_funding(symbol: str) -> Optional[float]:
        """OKX funding rate — free public API, 8-hour interval."""
        okx_symbol = f"{symbol.upper()}-USDT-SWAP"
        url = f"https://www.okx.com/api/v5/public/funding-rate?instId={okx_symbol}"
        data = _http_get(url)
        if data and data.get("code") == "0":
            rates = data.get("data", [])
            if rates:
                return float(rates[0].get("fundingRate", 0.0))
        return None


# =============================================================================
# LST YIELD DATA (Free APIs)
# =============================================================================

class LSTYieldFeed:
    """
    Fetches real staking yields for LSTs from free APIs.
    Sources: Lido API, DeFiLlama yields.
    """

    @staticmethod
    def get_staking_yields() -> Dict[str, float]:
        """
        Returns current annualized staking yields for supported LSTs.
        {"wstETH": 0.035, "cbETH": 0.033, "rETH": 0.031}
        """
        cache_key = "lst_yields"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        yields = {}

        # Lido stETH/wstETH yield (primary)
        lido_apy = LSTYieldFeed._lido_staking_apy()
        if lido_apy > 0:
            yields["wstETH"] = lido_apy
            yields["stETH"] = lido_apy

        # DeFiLlama yields for all LSTs
        llama_yields = LSTYieldFeed._defillama_lst_yields()
        for token, apy in llama_yields.items():
            if token not in yields or apy > 0:
                yields[token] = apy

        # Fallbacks if APIs fail
        if "wstETH" not in yields:
            yields["wstETH"] = 0.035
        if "cbETH" not in yields:
            yields["cbETH"] = 0.033
        if "rETH" not in yields:
            yields["rETH"] = 0.031

        _cache.set(cache_key, yields, ttl=300.0)  # 5 min cache (yields don't change fast)
        return yields

    @staticmethod
    def get_best_lst_yield() -> Tuple[str, float]:
        """Returns (token_name, apy) for highest yielding LST."""
        yields = LSTYieldFeed.get_staking_yields()
        if not yields:
            return ("wstETH", 0.035)
        best = max(yields.items(), key=lambda x: x[1])
        return best

    @staticmethod
    def _lido_staking_apy() -> float:
        """Fetch current Lido stETH APR from their public API."""
        url = "https://eth-api.lido.fi/v1/protocol/steth/apr/sma"
        data = _http_get(url)
        if data and "data" in data:
            sma_apr = data["data"].get("smaApr")
            if sma_apr is not None:
                return float(sma_apr) / 100.0  # Convert from percentage
        # Fallback: try last APR endpoint
        url2 = "https://eth-api.lido.fi/v1/protocol/steth/apr/last"
        data2 = _http_get(url2)
        if data2 and "data" in data2:
            last_apr = data2["data"].get("apr")
            if last_apr is not None:
                return float(last_apr) / 100.0
        return 0.0

    @staticmethod
    def _defillama_lst_yields() -> Dict[str, float]:
        """Fetch LST yields from DeFiLlama yields API."""
        yields = {}
        url = "https://yields.llama.fi/pools"
        data = _http_get(url, timeout=15)
        if not data or "data" not in data:
            return yields

        # Pool IDs we care about (Ethereum staking pools)
        target_pools = {
            "lido": "wstETH",
            "coinbase-wrapped-staked-eth": "cbETH",
            "rocket-pool": "rETH",
        }

        for pool in data["data"]:
            project = pool.get("project", "").lower()
            chain = pool.get("chain", "").lower()
            symbol = pool.get("symbol", "").upper()

            if chain != "ethereum":
                continue

            for project_key, token_name in target_pools.items():
                if project_key in project and token_name.upper() in symbol:
                    apy = pool.get("apy", 0.0)
                    if apy > 0:
                        yields[token_name] = apy / 100.0  # Convert percentage
                        break

        return yields


# =============================================================================
# DEFI CONTEXT (DeFiLlama for protocol comparisons)
# =============================================================================

class DeFiContext:
    """
    Pulls broader DeFi context from DeFiLlama for yield comparison
    and competitive analysis.
    """

    @staticmethod
    def get_top_yields(chain: str = "Base", count: int = 10) -> List[Dict]:
        """Get top yielding pools on a chain from DeFiLlama."""
        cache_key = f"top_yields:{chain}:{count}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = "https://yields.llama.fi/pools"
        data = _http_get(url, timeout=15)
        if not data or "data" not in data:
            return []

        pools = [
            {
                "project": p.get("project"),
                "symbol": p.get("symbol"),
                "tvl": p.get("tvlUsd", 0),
                "apy": p.get("apy", 0),
                "apy_base": p.get("apyBase", 0),
                "apy_reward": p.get("apyReward", 0),
            }
            for p in data["data"]
            if p.get("chain", "").lower() == chain.lower()
            and p.get("tvlUsd", 0) > 10000
            and p.get("apy", 0) > 0
        ]

        pools.sort(key=lambda x: x["apy"], reverse=True)
        result = pools[:count]
        _cache.set(cache_key, result, ttl=300.0)
        return result

    @staticmethod
    def get_protocol_tvl(protocol: str = "kerne") -> float:
        """Get protocol TVL from DeFiLlama."""
        cache_key = f"protocol_tvl:{protocol}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"https://api.llama.fi/tvl/{protocol}"
        try:
            if requests is None:
                return 0.0
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                tvl = float(resp.text)
                _cache.set(cache_key, tvl, ttl=300.0)
                return tvl
        except Exception:
            pass
        return 0.0

    @staticmethod
    def get_stablecoin_yields(min_tvl: float = 100000) -> List[Dict]:
        """Get stablecoin yield opportunities for delta-neutral comparison."""
        cache_key = f"stable_yields:{min_tvl}"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        url = "https://yields.llama.fi/pools"
        data = _http_get(url, timeout=15)
        if not data or "data" not in data:
            return []

        stable_symbols = {"USDC", "USDT", "DAI", "FRAX", "KUSD", "USDE", "GHO"}

        pools = []
        for p in data["data"]:
            symbol = p.get("symbol", "").upper()
            if any(s in symbol for s in stable_symbols):
                tvl = p.get("tvlUsd", 0)
                if tvl >= min_tvl:
                    pools.append({
                        "project": p.get("project"),
                        "chain": p.get("chain"),
                        "symbol": symbol,
                        "tvl": tvl,
                        "apy": p.get("apy", 0),
                    })

        pools.sort(key=lambda x: x["apy"], reverse=True)
        result = pools[:20]
        _cache.set(cache_key, result, ttl=300.0)
        return result


# =============================================================================
# GAS TRACKER
# =============================================================================

class GasTracker:
    """Track gas prices across chains using free public RPCs."""

    @staticmethod
    def get_base_gas_gwei() -> float:
        """Get current Base gas price in gwei via public RPC."""
        cache_key = "gas:base"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        rpc_urls = [
            os.getenv("BASE_RPC_URL", "https://mainnet.base.org"),
            "https://base.llamarpc.com",
            "https://base.drpc.org",
        ]

        for rpc in rpc_urls:
            try:
                payload = {
                    "jsonrpc": "2.0",
                    "method": "eth_gasPrice",
                    "params": [],
                    "id": 1
                }
                if requests is None:
                    return 0.01
                resp = requests.post(rpc, json=payload, timeout=5)
                if resp.status_code == 200:
                    result = resp.json().get("result", "0x0")
                    gas_wei = int(result, 16)
                    gas_gwei = gas_wei / 1e9
                    _cache.set(cache_key, gas_gwei, ttl=15.0)
                    return gas_gwei
            except Exception:
                continue

        return 0.01  # Base typically has very low gas

    @staticmethod
    def get_arbitrum_gas_gwei() -> float:
        """Get current Arbitrum gas price in gwei."""
        cache_key = "gas:arbitrum"
        cached = _cache.get(cache_key)
        if cached is not None:
            return cached

        rpc = os.getenv("ARBITRUM_RPC_URL", "https://arb1.arbitrum.io/rpc")
        if "," in rpc:
            rpc = rpc.split(",")[0].strip()
        try:
            payload = {"jsonrpc": "2.0", "method": "eth_gasPrice", "params": [], "id": 1}
            if requests is None:
                return 0.1
            resp = requests.post(rpc, json=payload, timeout=5)
            if resp.status_code == 200:
                result = resp.json().get("result", "0x0")
                gas_gwei = int(result, 16) / 1e9
                _cache.set(cache_key, gas_gwei, ttl=15.0)
                return gas_gwei
        except Exception:
            pass
        return 0.1


# =============================================================================
# UNIFIED PROTOCOL SNAPSHOT
# =============================================================================

class ProtocolSnapshot:
    """
    Generates a complete protocol health snapshot by combining all API data.
    This is the single source of truth for the stats server and monitors.
    """

    @staticmethod
    def generate() -> Dict:
        """Generate full protocol snapshot from all free API sources."""
        snapshot_start = time.time()

        # 1. Prices
        prices = PriceFeed.get_prices_batch(["ETH", "WSTETH", "CBETH", "RETH", "USDC", "BTC"])

        # 2. Funding rates
        funding = FundingRateAggregator.get_all_funding_rates("ETH")

        # 3. LST yields
        lst_yields = LSTYieldFeed.get_staking_yields()
        best_lst, best_lst_apy = LSTYieldFeed.get_best_lst_yield()

        # 4. Gas
        base_gas = GasTracker.get_base_gas_gwei()
        arb_gas = GasTracker.get_arbitrum_gas_gwei()

        # 5. Best funding opportunity
        best_funding_annual, best_venue = FundingRateAggregator.get_best_funding_rate("ETH")

        # 6. Expected APY calculation (using real data)
        eth_price = prices.get("ETH", 0.0)
        staking_yield = lst_yields.get("wstETH", 0.035)

        # Convert annualized funding back to per-hour rate for APYCalculator
        avg_annual_funding = funding.get("average_annual", 0.0)
        funding_per_hour = avg_annual_funding / (24 * 365) if avg_annual_funding else 0.0

        from apy_calculator import APYCalculator
        leverage = 3.0
        expected_apy = APYCalculator.calculate_expected_apy(
            leverage=leverage,
            funding_rate=funding_per_hour,
            staking_yield=staking_yield,
            spread_edge=0.0005,
            turnover_rate=0.1,
            cost_rate=0.01,
            funding_interval_hours=1,  # Using per-hour rate
        )

        snapshot = {
            "timestamp": time.time(),
            "timestamp_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "prices": prices,
            "funding_rates": funding,
            "lst_yields": lst_yields,
            "gas": {
                "base_gwei": round(base_gas, 4),
                "arbitrum_gwei": round(arb_gas, 4),
            },
            "strategy": {
                "leverage": leverage,
                "staking_yield": staking_yield,
                "avg_annual_funding": round(avg_annual_funding, 6),
                "best_funding_venue": best_venue,
                "best_funding_annual": round(best_funding_annual, 6),
                "expected_apy": round(expected_apy, 6),
                "expected_apy_pct": f"{expected_apy * 100:.2f}%",
                "best_lst": best_lst,
                "best_lst_apy": round(best_lst_apy, 6),
            },
            "meta": {
                "generation_ms": round((time.time() - snapshot_start) * 1000, 1),
                "sources": ["coingecko", "defillama", "binance", "bybit", "okx", "hyperliquid", "lido"],
            },
        }

        # Persist to disk for offline access
        try:
            snapshot_path = DATA_DIR / "protocol_snapshot.json"
            with open(snapshot_path, "w") as f:
                json.dump(snapshot, f, indent=2)
        except Exception as e:
            logger.debug(f"Failed to persist snapshot: {e}")

        return snapshot


# =============================================================================
# STATS SERVER (Lightweight HTTP for protocol data)
# =============================================================================

class StatsServer:
    """
    Minimal HTTP server serving protocol stats as JSON.
    Runs on a background thread, serves cached snapshot data.
    Used by: frontend, aggregators, partners, institutional leads.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 8787):
        self.host = host
        self.port = port
        self._snapshot: Dict = {}
        self._lock = threading.Lock()

    def update_snapshot(self, snapshot: Dict):
        with self._lock:
            self._snapshot = snapshot

    def _get_snapshot(self) -> Dict:
        with self._lock:
            return self._snapshot.copy()

    def start(self):
        """Start the stats server in a background thread."""
        thread = threading.Thread(target=self._run, daemon=True)
        thread.start()
        logger.info(f"📊 Stats server started on http://{self.host}:{self.port}")

    def _run(self):
        """Run a minimal HTTP server using stdlib."""
        from http.server import HTTPServer, BaseHTTPRequestHandler

        server_ref = self

        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                if self.path == "/stats" or self.path == "/api/stats":
                    data = server_ref._get_snapshot()
                    self._json_response(200, data)
                elif self.path == "/health":
                    self._json_response(200, {"status": "ok", "timestamp": time.time()})
                elif self.path == "/prices":
                    data = server_ref._get_snapshot()
                    self._json_response(200, data.get("prices", {}))
                elif self.path == "/funding":
                    data = server_ref._get_snapshot()
                    self._json_response(200, data.get("funding_rates", {}))
                elif self.path == "/apy":
                    data = server_ref._get_snapshot()
                    self._json_response(200, data.get("strategy", {}))
                elif self.path == "/yields":
                    data = server_ref._get_snapshot()
                    self._json_response(200, data.get("lst_yields", {}))
                else:
                    self._json_response(404, {"error": "not found", "endpoints": [
                        "/stats", "/health", "/prices", "/funding", "/apy", "/yields"
                    ]})

            def _json_response(self, code: int, data: Any):
                body = json.dumps(data, indent=2).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, format, *args):
                pass  # Suppress default access logs

        httpd = HTTPServer((self.host, self.port), Handler)
        httpd.serve_forever()


# =============================================================================
# BACKGROUND REFRESH LOOP
# =============================================================================

class APIRefreshLoop:
    """
    Background loop that periodically refreshes all API data.
    Designed to be started once alongside the main bot.
    """

    def __init__(self, refresh_interval: float = 30.0, serve_stats: bool = True, stats_port: int = 8787):
        self.refresh_interval = refresh_interval
        self.stats_server: Optional[StatsServer] = None
        if serve_stats:
            self.stats_server = StatsServer(port=stats_port)
        self._running = False

    def start(self):
        """Start the refresh loop and optional stats server."""
        self._running = True
        if self.stats_server:
            self.stats_server.start()
        thread = threading.Thread(target=self._loop, daemon=True)
        thread.start()
        logger.info(f"🔄 API refresh loop started (interval={self.refresh_interval}s)")

    def stop(self):
        self._running = False

    def _loop(self):
        while self._running:
            try:
                snapshot = ProtocolSnapshot.generate()
                if self.stats_server:
                    self.stats_server.update_snapshot(snapshot)

                apy_pct = snapshot.get("strategy", {}).get("expected_apy_pct", "N/A")
                eth_price = snapshot.get("prices", {}).get("ETH", 0)
                gen_ms = snapshot.get("meta", {}).get("generation_ms", 0)
                logger.info(f"📊 Snapshot refreshed | ETH=${eth_price:,.0f} | APY={apy_pct} | {gen_ms}ms")

            except Exception as e:
                logger.error(f"Snapshot refresh error: {e}")

            time.sleep(self.refresh_interval)


# =============================================================================
# CLI TEST
# =============================================================================

def _test_all():
    """Quick test of all API connectors — run with: python api_connector.py"""
    logger.info("=" * 60)
    logger.info("Kerne API Connector — Testing All Free APIs")
    logger.info("=" * 60)

    # 1. Prices
    logger.info("\n--- PRICE FEEDS ---")
    prices = PriceFeed.get_prices_batch(["ETH", "WSTETH", "CBETH", "RETH", "BTC", "USDC"])
    for symbol, price in prices.items():
        logger.info(f"  {symbol}: ${price:,.2f}")

    # 2. Funding Rates
    logger.info("\n--- FUNDING RATES ---")
    funding = FundingRateAggregator.get_all_funding_rates("ETH")
    for venue, data in funding.items():
        if isinstance(data, dict) and "annual" in data:
            logger.info(f"  {venue}: {data['rate']:.6f} ({data['interval']}) → {data['annual']*100:.2f}% APR")
        elif venue == "average_annual":
            logger.info(f"  Average Annual: {data*100:.2f}%")
        elif venue == "best_venue":
            logger.info(f"  Best Venue: {data}")

    # 3. LST Yields
    logger.info("\n--- LST STAKING YIELDS ---")
    yields = LSTYieldFeed.get_staking_yields()
    for token, apy in yields.items():
        logger.info(f"  {token}: {apy*100:.2f}%")

    # 4. Gas
    logger.info("\n--- GAS PRICES ---")
    logger.info(f"  Base: {GasTracker.get_base_gas_gwei():.4f} gwei")
    logger.info(f"  Arbitrum: {GasTracker.get_arbitrum_gas_gwei():.4f} gwei")

    # 5. Full Snapshot
    logger.info("\n--- FULL PROTOCOL SNAPSHOT ---")
    snapshot = ProtocolSnapshot.generate()
    strategy = snapshot.get("strategy", {})
    logger.info(f"  Expected APY: {strategy.get('expected_apy_pct', 'N/A')}")
    logger.info(f"  Best Funding: {strategy.get('best_funding_venue', 'N/A')} ({strategy.get('best_funding_annual', 0)*100:.2f}%)")
    logger.info(f"  Best LST: {strategy.get('best_lst', 'N/A')} ({strategy.get('best_lst_apy', 0)*100:.2f}%)")
    logger.info(f"  Generation: {snapshot.get('meta', {}).get('generation_ms', 0):.0f}ms")

    # 6. DeFi Context
    logger.info("\n--- TOP BASE YIELDS (DeFiLlama) ---")
    top = DeFiContext.get_top_yields("Base", 5)
    for p in top:
        logger.info(f"  {p['project']}/{p['symbol']}: {p['apy']:.2f}% APY (${p['tvl']:,.0f} TVL)")

    logger.info("\n" + "=" * 60)
    logger.info("All API tests complete.")
    logger.info("=" * 60)


if __name__ == "__main__":
    # Add bot/ to path for imports
    sys.path.insert(0, os.path.dirname(__file__))
    _test_all()
