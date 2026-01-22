# Created: 2026-01-22
"""
Discovery Engine
---------------
Automates lead discovery for all 12 growth categories by ingesting
on-chain scans, curated CSVs, and manual target lists.
"""

import csv
import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger

from .lead_database import Lead, LeadCategory, LeadDatabase, PipelineStage


@dataclass
class DiscoveryConfig:
    """Configuration for discovery inputs."""
    institutional_csv: str = "docs/institutional_leads.csv"
    whales_csv: str = "docs/leads/leads_v2.csv"
    curated_targets_dir: str = "docs/leads"
    output_report: str = "docs/leads/discovery_report.json"


class DiscoveryEngine:
    """Automates lead ingestion into the lead database."""

    def __init__(self, db: Optional[LeadDatabase] = None, config: Optional[DiscoveryConfig] = None):
        self.db = db or LeadDatabase()
        self.config = config or DiscoveryConfig()

    def ingest_institutional_csv(self) -> int:
        """Ingest institutional leads from lead_scanner_v3 output."""
        path = Path(self.config.institutional_csv)
        if not path.exists():
            logger.warning(f"Institutional CSV not found: {path}")
            return 0

        added = 0
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                address = row.get("Address")
                if not address:
                    continue
                lead = Lead(
                    id=address,
                    category=LeadCategory.CRYPTO_WHALES,
                    wallet_address=address,
                    on_chain_balance=float(row.get("Balance", 0) or 0),
                    notes=f"Asset: {row.get('Asset', '')}",
                    source="lead_scanner_v3",
                    priority=1,
                    stage=PipelineStage.DISCOVERED,
                )
                if self.db.add_lead(lead):
                    added += 1
        logger.info(f"Ingested {added} institutional whale leads")
        return added

    def ingest_whale_csv(self) -> int:
        """Ingest whale list from docs/leads/leads_v2.csv."""
        path = Path(self.config.whales_csv)
        if not path.exists():
            logger.warning(f"Whale CSV not found: {path}")
            return 0

        added = 0
        with path.open("r", newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                address = row.get("Address")
                if not address:
                    continue
                lead = Lead(
                    id=address,
                    category=LeadCategory.CRYPTO_WHALES,
                    wallet_address=address,
                    on_chain_balance=float(row.get("Balance_USDC", 0) or 0),
                    source="leads_v2",
                    priority=2,
                    stage=PipelineStage.DISCOVERED,
                )
                if self.db.add_lead(lead):
                    added += 1
        logger.info(f"Ingested {added} whale leads")
        return added

    def ingest_curated_targets(self) -> int:
        """Ingest curated CSVs in docs/leads/ directory."""
        added = 0
        path = Path(self.config.curated_targets_dir)
        if not path.exists():
            logger.warning(f"Curated targets dir not found: {path}")
            return 0

        for csv_path in path.glob("*_targets.csv"):
            logger.info(f"Processing curated targets: {csv_path}")
            with csv_path.open("r", newline="", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    lead_id = row.get("id") or row.get("name")
                    if not lead_id:
                        continue

                    category = LeadCategory(row.get("category", LeadCategory.NARRATIVE_CARTEL.value))
                    lead = Lead(
                        id=lead_id,
                        category=category,
                        name=row.get("name"),
                        twitter_handle=row.get("twitter"),
                        email=row.get("email"),
                        telegram_handle=row.get("telegram"),
                        discord_handle=row.get("discord"),
                        website=row.get("website"),
                        estimated_aum=float(row.get("estimated_aum", 0) or 0),
                        potential_deposit=float(row.get("potential_deposit", 0) or 0),
                        source=csv_path.name,
                        priority=int(row.get("priority", 3) or 3),
                        stage=PipelineStage.DISCOVERED,
                        notes=row.get("notes", ""),
                    )
                    if self.db.add_lead(lead):
                        added += 1

        logger.info(f"Ingested {added} curated targets")
        return added

    def run_full_discovery(self) -> Dict[str, int]:
        """Run full discovery and output a JSON report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "institutional": self.ingest_institutional_csv(),
            "whales": self.ingest_whale_csv(),
            "curated": self.ingest_curated_targets(),
        }

        output = Path(self.config.output_report)
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Discovery report saved to {output}")
        return report


if __name__ == "__main__":
    engine = DiscoveryEngine()
    engine.run_full_discovery()