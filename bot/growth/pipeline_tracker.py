# Created: 2026-01-22
"""
Pipeline Tracker
----------------
Maintains CRM-style pipeline operations for growth leads.
"""

from datetime import datetime
from typing import List, Optional

from loguru import logger

from .lead_database import ContactChannel, Lead, LeadDatabase, PipelineStage


class PipelineTracker:
    """CRM-like pipeline tracking for leads."""

    def __init__(self, db: Optional[LeadDatabase] = None):
        self.db = db or LeadDatabase()

    def advance_stage(self, lead_id: str, new_stage: PipelineStage, notes: str = "") -> bool:
        """Advance a lead to a new pipeline stage."""
        lead = self.db.get_lead(lead_id)
        if not lead:
            logger.warning(f"Lead not found: {lead_id}")
            return False

        lead.stage = new_stage
        lead.updated_at = datetime.now().isoformat()
        if notes:
            lead.notes = f"{lead.notes}\n[{lead.updated_at}] {notes}".strip()

        self.db.update_lead(lead)
        logger.info(f"Lead {lead_id} moved to {new_stage.value}")
        return True

    def log_outreach(self, lead_id: str, channel: ContactChannel, template: str = "", notes: str = ""):
        """Log outreach attempt and update pipeline stage."""
        self.db.log_outreach(lead_id, channel, template, notes)

    def mark_meeting(self, lead_id: str, notes: str = ""):
        """Mark meeting scheduled for a lead."""
        return self.advance_stage(lead_id, PipelineStage.MEETING_SCHEDULED, notes)

    def mark_committed(self, lead_id: str, notes: str = ""):
        """Mark lead as committed."""
        return self.advance_stage(lead_id, PipelineStage.COMMITTED, notes)

    def mark_converted(self, lead_id: str, notes: str = ""):
        """Mark lead as converted (deposit/integration)."""
        return self.advance_stage(lead_id, PipelineStage.CONVERTED, notes)

    def mark_dormant(self, lead_id: str, notes: str = ""):
        """Mark lead as dormant."""
        return self.advance_stage(lead_id, PipelineStage.DORMANT, notes)

    def get_next_actions(self, limit: int = 25) -> List[Lead]:
        """Get list of leads needing action."""
        return self.db.get_actionable_leads(limit=limit)