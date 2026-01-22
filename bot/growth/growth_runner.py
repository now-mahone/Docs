# Created: 2026-01-22
"""
Growth Runner
-------------
Unified entrypoint to run discovery, generate outreach messages,
update pipeline stages, and export KPI dashboards.
"""

import json
from pathlib import Path
from typing import List

from loguru import logger

from .discovery_engine import DiscoveryEngine
from .kpi_dashboard import KPIDashboard
from .lead_database import ContactChannel, LeadDatabase
from .outreach_manager import OutreachManager
from .pipeline_tracker import PipelineTracker


class GrowthRunner:
    """Orchestrates growth automation tasks."""

    def __init__(self):
        self.db = LeadDatabase()
        self.discovery = DiscoveryEngine(self.db)
        self.outreach = OutreachManager()
        self.pipeline = PipelineTracker(self.db)
        self.kpis = KPIDashboard(self.db)

    def run_discovery(self):
        return self.discovery.run_full_discovery()

    def generate_outreach_queue(self, channel: ContactChannel, limit: int = 25) -> List[dict]:
        """Generate an outreach queue of personalized messages."""
        leads = self.db.get_actionable_leads(limit=limit)
        queue = []
        for lead in leads:
            message = self.outreach.generate_message(lead, channel)
            queue.append({
                "lead_id": lead.id,
                "channel": channel.value,
                "message": message,
            })
        return queue

    def export_outreach_queue(self, channel: ContactChannel, limit: int = 25, output: str = "docs/leads/outreach_queue.json"):
        queue = self.generate_outreach_queue(channel, limit)
        path = Path(output)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(queue, indent=2), encoding="utf-8")
        logger.info(f"Outreach queue saved to {path}")
        return path

    def run_kpi_dashboard(self):
        self.kpis.snapshot()
        return self.kpis.generate_markdown()


if __name__ == "__main__":
    runner = GrowthRunner()
    runner.run_discovery()
    runner.export_outreach_queue(ContactChannel.TWITTER_DM)
    runner.run_kpi_dashboard()