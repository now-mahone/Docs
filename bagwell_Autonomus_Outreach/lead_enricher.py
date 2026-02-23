// Created: 2026-02-22
"""
Lead Enricher for Bagwell Autonomous Outreach.

Enriches on-chain leads with:
1. LinkedIn profile data (professional background)
2. Governance forum activity (investment thesis)
3. Social media presence
"""
import os
import json
import time
import csv
import requests
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from loguru import logger
from bs4 import BeautifulSoup

from config import (
    DATA_DIR,
    LEADS_CSV_PATH,
    ENRICHED_LEADS_PATH,
    LINKEDIN_ENABLED,
    FORUM_SOURCES,
    GOVERNANCE_SEARCH_QUERIES,
    MAX_ENRICHMENT_RETRIES,
)


class LeadEnricher:
    """Enriches on-chain leads with off-chain data."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        self.enriched_leads: Dict = self._load_enriched_leads()

    def _load_enriched_leads(self) -> Dict:
        """Load previously enriched leads."""
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        if os.path.exists(ENRICHED_LEADS_PATH):
            try:
                with open(ENRICHED_LEADS_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return {}
        return {}

    def _save_enriched_leads(self) -> None:
        """Persist enriched leads to disk."""
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        with open(ENRICHED_LEADS_PATH, "w") as f:
            json.dump(self.enriched_leads, f, indent=2, default=str)

    def load_leads_from_csv(self) -> List[Dict]:
        """Load leads from the institutional leads CSV."""
        leads = []
        if not os.path.exists(LEADS_CSV_PATH):
            logger.error(f"Leads CSV not found at {LEADS_CSV_PATH}")
            return leads

        with open(LEADS_CSV_PATH, "r") as f:
            reader = csv.DictReader(f)
            for row in reader:
                leads.append({
                    "address": row.get("Address", ""),
                    "asset": row.get("Asset", ""),
                    "balance": float(row.get("Balance", 0)),
                    "category": row.get("Category", ""),
                    "email": row.get("Email", ""),
                    "basescan_link": row.get("Basescan_Link", ""),
                })
        logger.info(f"Loaded {len(leads)} leads from CSV")
        return leads

    def enrich_linkedin(self, lead: Dict) -> Dict:
        """
        Attempt to find LinkedIn profile for a lead.
        Uses public search and profile scraping.
        """
        enrichment = {
            "linkedin_url": None,
            "name": None,
            "role": None,
            "company": None,
            "headline": None,
            "investment_focus": [],
        }

        if not LINKEDIN_ENABLED:
            logger.debug("LinkedIn enrichment disabled")
            return enrichment

        # Strategy 1: Check if ENS/name is available from on-chain
        # Strategy 2: Search via Google dorking (limited)
        # Note: Full LinkedIn scraping requires selenium/playwright

        # Placeholder for LinkedIn integration
        # In production, use a service like:
        # - Proxycurl API
        # - PhantomBuster
        # - Custom Selenium with cookies

        logger.debug(f"LinkedIn enrichment not implemented for {lead['address'][:10]}...")
        return enrichment

    def enrich_governance_activity(self, lead: Dict) -> Dict:
        """
        Search governance forums for the lead's wallet address or ENS.
        Identifies investment thesis and voting patterns.
        """
        enrichment = {
            "snapshot_votes": [],
            "forum_posts": [],
            "investment_thesis": [],
            "dao_memberships": [],
        }

        address = lead.get("address", "")
        if not address:
            return enrichment

        # Snapshot API query
        if FORUM_SOURCES["snapshot"]["enabled"]:
            try:
                snapshot_data = self._query_snapshot(address)
                enrichment["snapshot_votes"] = snapshot_data.get("votes", [])
                enrichment["dao_memberships"] = snapshot_data.get("daos", [])
            except Exception as e:
                logger.warning(f"Snapshot query failed: {e}")

        # Discourse forum search
        if FORUM_SOURCES["discourse"]["enabled"]:
            try:
                forum_data = self._search_discourse_forums(address)
                enrichment["forum_posts"] = forum_data.get("posts", [])
                enrichment["investment_thesis"] = forum_data.get("thesis", [])
            except Exception as e:
                logger.warning(f"Discourse search failed: {e}")

        return enrichment

    def _query_snapshot(self, address: str) -> Dict:
        """Query Snapshot API for voter history."""
        # Snapshot GraphQL API
        query = {
            "query": f"""
            {{
                votes(
                    first: 10
                    where: {{ voter: "{address.lower()}" }}
                    orderBy: created
                    orderDirection: desc
                ) {{
                    id
                    proposal {{
                        space {{ id name }}
                        title
                    }}
                    choice
                    created
                }}
            }}
            """
        }

        try:
            resp = self.session.post(
                "https://hub.snapshot.org/graphql",
                json=query,
                timeout=10
            )
            data = resp.json()
            votes = data.get("data", {}).get("votes", [])

            # Extract DAO memberships
            daos = list(set(v["proposal"]["space"]["name"] for v in votes if v.get("proposal")))

            return {"votes": votes[:10], "daos": daos}
        except Exception as e:
            logger.debug(f"Snapshot query error: {e}")
            return {"votes": [], "daos": []}

    def _search_discourse_forums(self, address: str) -> Dict:
        """Search known Discourse forums for address mentions."""
        results = {"posts": [], "thesis": []}

        for forum_url in FORUM_SOURCES["discourse"]["known_forums"]:
            try:
                # Discourse search endpoint
                search_url = f"{forum_url}/search.json"
                params = {"q": address}

                resp = self.session.get(search_url, params=params, timeout=10)
                if resp.status_code == 200:
                    data = resp.json()
                    posts = data.get("posts", [])[:5]
                    for post in posts:
                        results["posts"].append({
                            "forum": forum_url,
                            "topic_id": post.get("topic_id"),
                            "excerpt": post.get("blurb", "")[:200],
                        })

                time.sleep(1)  # Rate limiting
            except Exception as e:
                logger.debug(f"Forum search error for {forum_url}: {e}")

        return results

    def enrich_lead(self, lead: Dict) -> Dict:
        """
        Full enrichment pipeline for a single lead.
        """
        address = lead.get("address", "")

        # Check if already enriched recently
        if address in self.enriched_leads:
            cached = self.enriched_leads[address]
            # Re-enrich if older than 7 days
            last_updated = cached.get("last_updated", "")
            if last_updated:
                try:
                    last_dt = datetime.fromisoformat(last_updated)
                    if (datetime.utcnow() - last_dt).days < 7:
                        logger.debug(f"Using cached enrichment for {address[:10]}...")
                        return cached
                except:
                    pass

        logger.info(f"Enriching lead: {address[:10]}...")

        enriched = {
            **lead,
            "last_updated": datetime.utcnow().isoformat(),
            "enrichment_status": "partial",
        }

        # LinkedIn enrichment
        linkedin_data = self.enrich_linkedin(lead)
        enriched.update(linkedin_data)

        # Governance enrichment
        gov_data = self.enrich_governance_activity(lead)
        enriched.update(gov_data)

        # Determine investment focus from governance activity
        investment_focus = self._infer_investment_focus(enriched)
        enriched["inferred_investment_focus"] = investment_focus

        # Mark as fully enriched if we have good data
        if enriched.get("snapshot_votes") or enriched.get("forum_posts"):
            enriched["enrichment_status"] = "good"
        if enriched.get("name") or enriched.get("linkedin_url"):
            enriched["enrichment_status"] = "excellent"

        # Cache and save
        self.enriched_leads[address] = enriched
        self._save_enriched_leads()

        return enriched

    def _infer_investment_focus(self, enriched: Dict) -> List[str]:
        """Infer investment focus from governance activity."""
        focus_areas = []

        daos = enriched.get("dao_memberships", [])
        if not daos:
            return ["DeFi", "Yield"]

        # Map DAOs to investment themes
        dao_themes = {
            "Uniswap": ["DEX", "Liquidity", "Governance"],
            "Aave": ["Lending", "Borrowing", "DeFi"],
            "Curve": ["Stablecoins", "Yield", "AMM"],
            "Aerodrome": ["Base", "DEX", "Yield"],
            "Lido": ["Staking", "ETH", "Liquid Staking"],
            "Maker": ["Stablecoins", "DAI", "Governance"],
            "Compound": ["Lending", "DeFi"],
            "Ethereum": ["ETH", "Layer 1", "Governance"],
        }

        for dao in daos:
            for dao_name, themes in dao_themes.items():
                if dao_name.lower() in dao.lower():
                    focus_areas.extend(themes)

        return list(set(focus_areas))[:5] if focus_areas else ["DeFi", "Yield"]

    def enrich_all_leads(self) -> List[Dict]:
        """Enrich all leads from CSV."""
        leads = self.load_leads_from_csv()
        enriched = []

        for i, lead in enumerate(leads):
            logger.info(f"Enriching lead {i+1}/{len(leads)}")
            enriched_lead = self.enrich_lead(lead)
            enriched.append(enriched_lead)
            time.sleep(2)  # Rate limiting

        logger.info(f"Enriched {len(enriched)} leads")
        return enriched


def run_enrichment():
    """Standalone entry point."""
    enricher = LeadEnricher()
    enriched = enricher.enrich_all_leads()
    return enriched


if __name__ == "__main__":
    run_enrichment()