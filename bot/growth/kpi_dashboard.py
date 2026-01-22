# Created: 2026-01-22
"""
KPI Dashboard
-------------
Generates weekly KPI snapshots and markdown dashboards for growth ops.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger

from .lead_database import LeadDatabase


class KPIDashboard:
    """Generates KPI snapshots and reports."""

    def __init__(self, db: Optional[LeadDatabase] = None, output_dir: str = "docs/reports"):
        self.db = db or LeadDatabase()
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def snapshot(self):
        """Take KPI snapshot in DB."""
        self.db.snapshot_kpis()

    def generate_markdown(self) -> Path:
        """Generate a markdown KPI summary."""
        stats = self.db.get_pipeline_stats()
        timestamp = datetime.now().strftime("%Y-%m-%d")
        filename = f"GROWTH_KPI_{timestamp}.md"
        output_path = self.output_dir / filename

        lines = [
            "# Kerne Growth KPI Dashboard",
            f"Date: {timestamp}",
            "",
            "## Summary",
            f"- Total Leads: {stats['total_leads']}",
            f"- Total Potential TVL: ${stats['total_potential_tvl']:,.2f}",
            f"- Converted TVL: ${stats['converted_tvl']:,.2f}",
            f"- Response Rate: {stats['response_rate']:.2f}%",
            f"- Conversion Rate: {stats['conversion_rate']:.2f}%",
            "",
            "## Leads by Category",
        ]

        for category, count in stats["by_category"].items():
            lines.append(f"- {category}: {count}")

        lines.extend([
            "",
            "## Leads by Stage",
        ])

        for stage, count in stats["by_stage"].items():
            lines.append(f"- {stage}: {count}")

        output_path.write_text("\n".join(lines), encoding="utf-8")
        logger.info(f"Generated KPI dashboard at {output_path}")
        return output_path


if __name__ == "__main__":
    dashboard = KPIDashboard()
    dashboard.snapshot()
    dashboard.generate_markdown()