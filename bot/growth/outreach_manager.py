# Created: 2026-01-22
"""
Outreach Manager
----------------
Manages outreach templates and generates personalized messages
for each lead based on category and channel.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

from loguru import logger

from .lead_database import ContactChannel, Lead, LeadCategory


DEFAULT_TEMPLATES = {
    LeadCategory.NARRATIVE_CARTEL.value: {
        ContactChannel.TWITTER_DM.value: (
            "Hey {name}, we’re building Kerne—a delta-neutral LST yield layer on Base. "
            "We’re curating a private Genesis cohort (whitelist + capacity caps). "
            "Would love your feedback and to offer a strategic allocation."
        )
    },
    LeadCategory.CRYPTO_WHALES.value: {
        ContactChannel.TWITTER_DM.value: (
            "Hey {name}, noticed your Base activity and ETH/LST exposure. "
            "Kerne is a delta-neutral yield engine (15-20% APY) with institutional guardrails. "
            "We’re onboarding a few whales for Genesis—can I share the private memo?"
        )
    },
    LeadCategory.DAO_TREASURIES.value: {
        ContactChannel.EMAIL.value: (
            "Hi {name}, I’m with Kerne Protocol. We run a delta-neutral LST yield layer "
            "with proof-of-reserve transparency. We’re onboarding a Senior Tranche for DAO treasuries. "
            "Open to a 15-min discussion on a low-volatility allocation?"
        )
    },
    LeadCategory.LST_PROVIDERS.value: {
        ContactChannel.EMAIL.value: (
            "Hi {name}, we’d like to collaborate on a boosted vault for {org}. "
            "Kerne can drive LST demand via stacked yield + points. Open to a co-marketing call?"
        )
    },
    LeadCategory.DEFI_INTEGRATORS.value: {
        ContactChannel.GOVERNANCE_FORUM.value: (
            "Kerne is a delta-neutral yield layer on Base. We’d like to propose kUSD/rUSD "
            "as collateral with incentives + integration support. Please advise on next steps."
        )
    },
}


@dataclass
class OutreachConfig:
    """Configuration for outreach templates."""
    template_path: str = "docs/leads/outreach_templates.json"


class OutreachManager:
    """Loads templates and generates outreach content."""

    def __init__(self, config: Optional[OutreachConfig] = None):
        self.config = config or OutreachConfig()
        self.templates = DEFAULT_TEMPLATES.copy()
        self._load_templates()

    def _load_templates(self):
        path = Path(self.config.template_path)
        if not path.exists():
            logger.warning(f"No custom template file found: {path}")
            return

        with path.open("r", encoding="utf-8") as f:
            custom_templates = json.load(f)
        self.templates.update(custom_templates)
        logger.info(f"Loaded custom outreach templates from {path}")

    def generate_message(self, lead: Lead, channel: ContactChannel) -> str:
        """Generate a message for a lead and channel."""
        category_templates = self.templates.get(lead.category.value, {})
        template = category_templates.get(channel.value)

        if not template:
            logger.warning(f"No template found for {lead.category.value}:{channel.value}")
            template = "Hi {name}, would love to connect regarding Kerne."  # fallback

        return template.format(
            name=lead.name or lead.twitter_handle or lead.id,
            org=lead.name or "your team",
        )

    def save_default_templates(self):
        """Save default templates to JSON for customization."""
        path = Path(self.config.template_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(self.templates, f, indent=2)
        logger.info(f"Saved templates to {path}")