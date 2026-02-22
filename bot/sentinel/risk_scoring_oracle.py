# Created: 2026-02-22
"""
Kerne Automated Risk Scoring Oracle

Aggregates DeFiLlama protocol/security data and computes a real-time risk score
(0–100) per supported asset. Scores are used to dynamically adjust on-chain
allocation caps on the KerneYieldRouter contract.

Risk Score Tiers → On-chain maxAllocationBps:
  >= 80  → HEALTHY    → 5000 bps (50%)  — hard ceiling regardless of score
  >= 60  → MODERATE   → 2500 bps (25%)
  >= 40  → ELEVATED   → 1000 bps (10%)
  <  40  → CRITICAL   → 0 bps    (0%, asset deactivated)

Conservative design rationale: Even a perfect protocol gets at most 50%.
The remaining 50%+ must always spread across ≥1 other asset to prevent
single-asset catastrophic loss from an undetected exploit.

Run:
    python -m bot.sentinel.risk_scoring_oracle                   # single pass
    python -m bot.sentinel.risk_scoring_oracle --loop --interval 3600  # hourly daemon
    python -m bot.sentinel.risk_scoring_oracle --dry-run         # score only, no chain writes
"""

import os
import sys
import json
import time
import argparse
import requests
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional
from loguru import logger
from web3 import Web3
from eth_account import Account

# ─────────────────────────────────────────────────────────────────────────────
# Constants & Configuration
# ─────────────────────────────────────────────────────────────────────────────

DEFILLAMA_PROTOCOLS_URL = "https://api.llama.fi/protocols"
DEFILLAMA_POOLS_URL = "https://yields.llama.fi/pools"
DEFILLAMA_PROTOCOL_URL = "https://api.llama.fi/protocol/{slug}"

MAPPINGS_PATH = Path(__file__).parent / "asset_mappings.json"
YIELD_ROUTER_ABI = [
    {
        "inputs": [
            {"internalType": "address", "name": "asset", "type": "address"},
            {"internalType": "bool", "name": "active", "type": "bool"},
            {"internalType": "uint256", "name": "maxAllocationBps", "type": "uint256"}
        ],
        "name": "updateAsset",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [{"internalType": "address", "name": "", "type": "address"}],
        "name": "assetConfigs",
        "outputs": [
            {"internalType": "address", "name": "vault", "type": "address"},
            {"internalType": "address", "name": "lstToken", "type": "address"},
            {"internalType": "uint256", "name": "lstYieldBps", "type": "uint256"},
            {"internalType": "uint256", "name": "maxAllocationBps", "type": "uint256"},
            {"internalType": "uint256", "name": "minDepositUsd", "type": "uint256"},
            {"internalType": "bool", "name": "active", "type": "bool"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]

# Risk tier thresholds → allocation caps in bps
# Conservative upper cap of 5000 (50%) even for HEALTHY assets
RISK_TIERS = [
    {"min_score": 80, "label": "HEALTHY",  "max_bps": 5000, "active": True},
    {"min_score": 60, "label": "MODERATE", "max_bps": 2500, "active": True},
    {"min_score": 40, "label": "ELEVATED", "max_bps": 1000, "active": True},
    {"min_score":  0, "label": "CRITICAL", "max_bps":    0, "active": False},
]

# DeFiLlama fetch cache TTL seconds
CACHE_TTL = 300  # 5 minutes

# ─────────────────────────────────────────────────────────────────────────────
# Data Classes
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ProtocolMetrics:
    """Raw DeFiLlama protocol data used for risk scoring."""
    slug: str
    tvl_usd: float = 0.0
    tvl_30d_change_pct: float = 0.0  # negative = TVL bled
    audit_count: int = 0
    has_bug_bounty: bool = False
    category: str = "Unknown"
    pool_apy: float = 0.0
    pool_apy_7d_mean: float = 0.0
    pool_il_risk: str = "no"   # "no" | "low" | "high"
    oracle_in_pool: bool = False
    raw_protocol: dict = field(default_factory=dict)
    raw_pool: dict = field(default_factory=dict)


@dataclass
class AssetRiskScore:
    """Final risk assessment for a single asset."""
    symbol: str
    address: str
    score: float          # 0–100
    tier_label: str       # HEALTHY / MODERATE / ELEVATED / CRITICAL
    max_allocation_bps: int
    active: bool
    score_components: dict = field(default_factory=dict)
    metrics: Optional[ProtocolMetrics] = None


# ─────────────────────────────────────────────────────────────────────────────
# DeFiLlama Client
# ─────────────────────────────────────────────────────────────────────────────

class DeFiLlamaClient:
    """Thin wrapper around DeFiLlama public APIs with in-process caching."""

    def __init__(self):
        self._protocols_cache: Optional[list] = None
        self._protocols_ts: float = 0.0
        self._pools_cache: Optional[list] = None
        self._pools_ts: float = 0.0
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "KerneProtocol/1.0 RiskOracle"})

    def _get_protocols(self) -> list:
        now = time.time()
        if self._protocols_cache and now - self._protocols_ts < CACHE_TTL:
            return self._protocols_cache
        try:
            resp = self.session.get(DEFILLAMA_PROTOCOLS_URL, timeout=15)
            resp.raise_for_status()
            self._protocols_cache = resp.json()
            self._protocols_ts = now
            logger.debug(f"Fetched {len(self._protocols_cache)} protocols from DeFiLlama")
        except Exception as e:
            logger.warning(f"DeFiLlama protocols fetch failed: {e}")
            if self._protocols_cache:
                logger.warning("Using stale protocols cache")
            else:
                self._protocols_cache = []
        return self._protocols_cache

    def _get_pools(self) -> list:
        now = time.time()
        if self._pools_cache and now - self._pools_ts < CACHE_TTL:
            return self._pools_cache
        try:
            resp = self.session.get(DEFILLAMA_POOLS_URL, timeout=15)
            resp.raise_for_status()
            data = resp.json()
            self._pools_cache = data.get("data", [])
            self._pools_ts = now
            logger.debug(f"Fetched {len(self._pools_cache)} pools from DeFiLlama")
        except Exception as e:
            logger.warning(f"DeFiLlama pools fetch failed: {e}")
            if self._pools_cache:
                logger.warning("Using stale pools cache")
            else:
                self._pools_cache = []
        return self._pools_cache

    def get_protocol_detail(self, slug: str) -> dict:
        """Fetch individual protocol detail (audit history, bug bounty, etc.)."""
        try:
            url = DEFILLAMA_PROTOCOL_URL.format(slug=slug)
            resp = self.session.get(url, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning(f"Protocol detail fetch failed for {slug}: {e}")
            return {}

    def get_protocol_metrics(self, slug: str, pool_id: str) -> ProtocolMetrics:
        """Aggregate all relevant metrics for a protocol/pool pair."""
        metrics = ProtocolMetrics(slug=slug)

        # ── Protocol-level data ──────────────────────────────────────────────
        protocols = self._get_protocols()
        protocol_entry = next(
            (p for p in protocols if p.get("slug") == slug or p.get("name", "").lower() == slug.lower()),
            None
        )

        if protocol_entry:
            metrics.tvl_usd = float(protocol_entry.get("tvl") or 0)
            metrics.category = protocol_entry.get("category", "Unknown")
            metrics.raw_protocol = protocol_entry

            # 30-day TVL change — use change_7d as proxy if 30d unavailable
            tvl_30d = protocol_entry.get("change_30d")
            tvl_7d  = protocol_entry.get("change_7d")
            if tvl_30d is not None:
                metrics.tvl_30d_change_pct = float(tvl_30d)
            elif tvl_7d is not None:
                metrics.tvl_30d_change_pct = float(tvl_7d)

        # ── Protocol detail (audits, bug bounty) ─────────────────────────────
        detail = self.get_protocol_detail(slug)
        if detail:
            audits = detail.get("audits")
            if audits:
                metrics.audit_count = int(audits) if str(audits).isdigit() else (1 if audits else 0)
            elif detail.get("audit_links"):
                metrics.audit_count = len(detail.get("audit_links", []))
            metrics.has_bug_bounty = bool(detail.get("bugs"))

        # ── Pool-level data ───────────────────────────────────────────────────
        pools = self._get_pools()
        pool_entry = next((p for p in pools if p.get("pool") == pool_id), None)

        if pool_entry:
            metrics.pool_apy = float(pool_entry.get("apy") or 0)
            metrics.pool_apy_7d_mean = float(pool_entry.get("apyMean30d") or pool_entry.get("apy") or 0)
            metrics.pool_il_risk = pool_entry.get("ilRisk", "no")
            metrics.oracle_in_pool = bool(pool_entry.get("rewardTokens"))
            metrics.raw_pool = pool_entry

        logger.debug(
            f"[{slug}] TVL=${metrics.tvl_usd/1e6:.1f}M | "
            f"TVLΔ30d={metrics.tvl_30d_change_pct:.1f}% | "
            f"Audits={metrics.audit_count} | "
            f"BugBounty={metrics.has_bug_bounty} | "
            f"APY={metrics.pool_apy:.2f}%"
        )
        return metrics


# ─────────────────────────────────────────────────────────────────────────────
# Risk Scoring Engine
# ─────────────────────────────────────────────────────────────────────────────

class RiskScoringEngine:
    """
    Converts raw ProtocolMetrics into a normalized 0–100 risk score.

    Scoring Components (total = 100 points):
      1. TVL Size         (20 pts) — larger TVL = battle-tested
      2. TVL Stability    (20 pts) — sustained outflows signal risk
      3. Audit Coverage   (25 pts) — zero audits is disqualifying
      4. Bug Bounty       (10 pts) — program signals security maturity
      5. APY Stability    (15 pts) — extreme APY spikes = exploit risk indicator
      6. IL / Oracle Risk (10 pts) — impermanent loss and oracle manipulation risk

    Design rationale: Audits carry the most single-factor weight (25 pts)
    because unaudited code is the leading cause of protocol exploits.
    """

    # ── Component weight caps ────────────────────────────────────────────────
    W_TVL_SIZE     = 20
    W_TVL_STABLE   = 20
    W_AUDIT        = 25
    W_BUG_BOUNTY   = 10
    W_APY_STABLE   = 15
    W_IL_ORACLE    = 10

    # TVL size breakpoints (USD)
    TVL_TIERS = [
        (1_000_000_000, 20),   # > $1B
        (500_000_000,   17),   # > $500M
        (100_000_000,   13),   # > $100M
        (50_000_000,    10),   # > $50M
        (10_000_000,     6),   # > $10M
        (1_000_000,      3),   # > $1M
        (0,              0),   # < $1M — not investable
    ]

    def score(self, metrics: ProtocolMetrics) -> tuple[float, dict]:
        """Return (total_score, components_dict)."""
        components: dict[str, float] = {}

        # 1. TVL Size
        tvl_score = 0.0
        for threshold, pts in self.TVL_TIERS:
            if metrics.tvl_usd >= threshold:
                tvl_score = float(pts)
                break
        components["tvl_size"] = tvl_score

        # 2. TVL Stability — penalize outflows
        tvl_stable_score = self.W_TVL_STABLE
        change = metrics.tvl_30d_change_pct
        if change < -50:
            tvl_stable_score = 0.0    # >50% bleed is catastrophic
        elif change < -20:
            tvl_stable_score = 5.0    # severe drain
        elif change < -10:
            tvl_stable_score = 10.0   # moderate drain
        elif change < -5:
            tvl_stable_score = 15.0   # mild drain
        # else: unchanged or inflow → full marks
        components["tvl_stability"] = tvl_stable_score

        # 3. Audit Coverage — zero audits → HARD CAP at 35/100 regardless
        if metrics.audit_count == 0:
            audit_score = 0.0
        elif metrics.audit_count == 1:
            audit_score = 15.0
        elif metrics.audit_count == 2:
            audit_score = 20.0
        else:
            audit_score = float(self.W_AUDIT)  # 3+ audits = full marks
        components["audit_coverage"] = audit_score

        # 4. Bug Bounty
        bounty_score = float(self.W_BUG_BOUNTY) if metrics.has_bug_bounty else 0.0
        components["bug_bounty"] = bounty_score

        # 5. APY Stability — anomalous spikes are a classic exploit/rug warning
        apy = metrics.pool_apy
        apy_mean = max(metrics.pool_apy_7d_mean, 0.01)  # avoid div-by-zero
        apy_stable_score = self.W_APY_STABLE
        if apy > 0:
            spike_ratio = apy / apy_mean
            if spike_ratio > 10:
                apy_stable_score = 0.0   # >10x spike — likely exploit or rug
            elif spike_ratio > 5:
                apy_stable_score = 5.0
            elif spike_ratio > 3:
                apy_stable_score = 10.0
            elif apy > 200:
                apy_stable_score = 5.0   # >200% APY is implausibly high
        components["apy_stability"] = apy_stable_score

        # 6. IL + Oracle Risk
        il_oracle_score = float(self.W_IL_ORACLE)
        if metrics.pool_il_risk == "high":
            il_oracle_score -= 7.0
        elif metrics.pool_il_risk == "low":
            il_oracle_score -= 3.0
        if metrics.oracle_in_pool:
            il_oracle_score -= 2.0  # reward token reliance → oracle attack vector
        il_oracle_score = max(0.0, il_oracle_score)
        components["il_oracle_risk"] = il_oracle_score

        total = sum(components.values())

        # Hard cap at 35 for unaudited protocols
        if metrics.audit_count == 0:
            total = min(total, 35.0)

        total = max(0.0, min(100.0, total))
        return total, components

    def classify(self, score: float) -> dict:
        """Map a score to a risk tier dict."""
        for tier in RISK_TIERS:
            if score >= tier["min_score"]:
                return tier
        return RISK_TIERS[-1]  # fallback: CRITICAL


# ─────────────────────────────────────────────────────────────────────────────
# On-Chain Cap Updater
# ─────────────────────────────────────────────────────────────────────────────

class OnChainCapUpdater:
    """Writes risk-scored allocation caps to KerneYieldRouter on-chain."""

    def __init__(self, rpc_url: str, private_key: str, router_address: str, chain_id: int = 8453):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        if not self.w3.is_connected():
            raise ConnectionError(f"Cannot connect to RPC: {rpc_url}")
        self.account = Account.from_key(private_key)
        self.router = self.w3.eth.contract(
            address=Web3.to_checksum_address(router_address),
            abi=YIELD_ROUTER_ABI
        )
        self.chain_id = chain_id
        logger.info(f"OnChainCapUpdater ready | account={self.account.address} | router={router_address}")

    def get_current_config(self, asset_address: str) -> Optional[dict]:
        """Read current on-chain config for an asset."""
        try:
            result = self.router.functions.assetConfigs(
                Web3.to_checksum_address(asset_address)
            ).call()
            return {
                "vault": result[0],
                "lstToken": result[1],
                "lstYieldBps": result[2],
                "maxAllocationBps": result[3],
                "minDepositUsd": result[4],
                "active": result[5]
            }
        except Exception as e:
            logger.warning(f"Could not read assetConfigs for {asset_address}: {e}")
            return None

    def update_cap(self, asset_address: str, active: bool, max_bps: int, dry_run: bool = False) -> bool:
        """Call YieldRouter.updateAsset() with new risk-scored cap."""
        try:
            checksum_addr = Web3.to_checksum_address(asset_address)

            if dry_run:
                logger.info(f"[DRY-RUN] updateAsset({checksum_addr}, active={active}, maxBps={max_bps})")
                return True

            tx = self.router.functions.updateAsset(
                checksum_addr,
                active,
                max_bps
            ).build_transaction({
                "from": self.account.address,
                "gas": 120000,
                "gasPrice": int(self.w3.eth.gas_price * 1.15),  # 15% priority bump
                "nonce": self.w3.eth.get_transaction_count(self.account.address),
                "chainId": self.chain_id
            })

            signed = self.w3.eth.account.sign_transaction(tx, self.account.key)
            tx_hash = self.w3.eth.send_raw_transaction(signed.raw_transaction)
            receipt = self.w3.eth.wait_for_transaction_receipt(tx_hash, timeout=60)

            success = receipt["status"] == 1
            level = "success" if success else "error"
            getattr(logger, level)(
                f"updateAsset({checksum_addr}, {active}, {max_bps}) | "
                f"tx={tx_hash.hex()} | gas={receipt['gasUsed']}"
            )
            return success

        except Exception as e:
            logger.error(f"updateAsset failed for {asset_address}: {e}")
            return False


# ─────────────────────────────────────────────────────────────────────────────
# Main Oracle Orchestrator
# ─────────────────────────────────────────────────────────────────────────────

class RiskScoringOracle:
    """
    Top-level orchestrator that:
      1. Loads asset mappings
      2. Fetches DeFiLlama data
      3. Scores each asset
      4. Updates on-chain caps via KerneYieldRouter.updateAsset()
    """

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        self.llama = DeFiLlamaClient()
        self.scorer = RiskScoringEngine()
        self.updater: Optional[OnChainCapUpdater] = None

        # Load asset mappings
        with open(MAPPINGS_PATH, "r") as f:
            data = json.load(f)
        self.assets = data["assets"]

        # Optionally init on-chain updater (requires env vars)
        rpc_url        = os.getenv("BASE_RPC_URL", "https://mainnet.base.org")
        private_key    = os.getenv("PRIVATE_KEY")
        router_address = os.getenv("YIELD_ROUTER_ADDRESS")

        if private_key and router_address:
            try:
                self.updater = OnChainCapUpdater(rpc_url, private_key, router_address)
            except Exception as e:
                logger.warning(f"OnChainCapUpdater init failed: {e}. Falling back to dry-run.")
                self.dry_run = True
        else:
            logger.warning("PRIVATE_KEY or YIELD_ROUTER_ADDRESS not set — running in dry-run mode.")
            self.dry_run = True

    def run_once(self) -> list[AssetRiskScore]:
        """Execute a full scoring cycle and return results."""
        logger.info(f"{'='*60}")
        logger.info(f"Kerne Risk Scoring Oracle — {time.strftime('%Y-%m-%d %H:%M:%S UTC', time.gmtime())}")
        logger.info(f"Mode: {'DRY-RUN' if self.dry_run else 'LIVE'}")
        logger.info(f"{'='*60}")

        results: list[AssetRiskScore] = []

        for asset_cfg in self.assets:
            symbol   = asset_cfg["symbol"]
            address  = asset_cfg["address"]
            slug     = asset_cfg["defillama_protocol_slug"]
            pool_id  = asset_cfg["defillama_pool_id"]

            logger.info(f"\n── Scoring {symbol} ({address[:10]}…) ──")

            # 1. Fetch metrics from DeFiLlama
            try:
                metrics = self.llama.get_protocol_metrics(slug, pool_id)
            except Exception as e:
                logger.error(f"Metrics fetch failed for {symbol}: {e} — assigning CRITICAL score.")
                metrics = ProtocolMetrics(slug=slug)

            # 2. Score
            score, components = self.scorer.score(metrics)
            tier = self.scorer.classify(score)

            result = AssetRiskScore(
                symbol=symbol,
                address=address,
                score=score,
                tier_label=tier["label"],
                max_allocation_bps=tier["max_bps"],
                active=tier["active"],
                score_components=components,
                metrics=metrics
            )
            results.append(result)

            logger.info(
                f"  Score: {score:.1f}/100 | Tier: {tier['label']} | "
                f"maxBps: {tier['max_bps']} | active: {tier['active']}"
            )
            logger.info(f"  Components: {json.dumps({k: round(v,1) for k,v in components.items()})}")

            # 3. Push on-chain
            if self.updater:
                # Only update if cap would actually change — skip if unregistered (vault=0x0)
                current = self.updater.get_current_config(address)
                if current and current["vault"] != "0x" + "0" * 40:
                    changed = (
                        current["active"] != tier["active"] or
                        current["maxAllocationBps"] != tier["max_bps"]
                    )
                    if changed:
                        logger.info(
                            f"  On-chain update required: "
                            f"active {current['active']}→{tier['active']} | "
                            f"maxBps {current['maxAllocationBps']}→{tier['max_bps']}"
                        )
                        self.updater.update_cap(address, tier["active"], tier["max_bps"], dry_run=self.dry_run)
                    else:
                        logger.info(f"  On-chain config already current — no update needed.")
                else:
                    logger.info(f"  Asset not yet registered in YieldRouter — skipping on-chain update.")
            else:
                self._log_dry_run_cap(symbol, address, tier)

        self._print_summary(results)
        return results

    def _log_dry_run_cap(self, symbol: str, address: str, tier: dict):
        logger.info(
            f"  [DRY-RUN] Would call updateAsset("
            f"{address}, active={tier['active']}, maxBps={tier['max_bps']})"
        )

    def _print_summary(self, results: list[AssetRiskScore]):
        logger.info(f"\n{'='*60}")
        logger.info("RISK SCORING ORACLE — SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(f"{'Symbol':<10} {'Score':>6}  {'Tier':<10}  {'MaxBps':>7}  {'Active'}")
        logger.info(f"{'-'*55}")
        for r in sorted(results, key=lambda x: x.score, reverse=True):
            logger.info(
                f"{r.symbol:<10} {r.score:>6.1f}  {r.tier_label:<10}  {r.max_allocation_bps:>7}  {r.active}"
            )
        logger.info(f"{'='*60}")


# ─────────────────────────────────────────────────────────────────────────────
# Entry Point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Kerne Automated Risk Scoring Oracle")
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Score assets and log results but do NOT write on-chain"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Run continuously (daemon mode)"
    )
    parser.add_argument(
        "--interval", type=int, default=3600,
        help="Loop interval in seconds (default: 3600 = 1 hour)"
    )
    args = parser.parse_args()

    oracle = RiskScoringOracle(dry_run=args.dry_run)

    if args.loop:
        logger.info(f"Starting daemon loop (interval={args.interval}s)")
        while True:
            try:
                oracle.run_once()
            except Exception as e:
                logger.error(f"Oracle cycle error: {e}")
            logger.info(f"Sleeping {args.interval}s until next cycle…")
            time.sleep(args.interval)
    else:
        oracle.run_once()


if __name__ == "__main__":
    main()