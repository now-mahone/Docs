// Created: 2026-02-22
"""
Orchestrator for Bagwell Autonomous Outreach.

Coordinates the full pipeline:
1. Load leads from CSV
2. Enrich leads (LinkedIn + Governance)
3. Generate personalized messages (LLM)
4. Send via existing email_manager
5. Track and log all activity
"""
import os
import sys
import json
import time
import argparse
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from loguru import logger

# Add parent directory for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from bagwell_Autonomus_Outreach.config import (
    DATA_DIR,
    ENRICHED_LEADS_PATH,
    OUTREACH_LOG_PATH,
    MAX_DAILY_OUTREACH,
    MINUTES_BETWEEN_EMAILS,
)
from bagwell_Autonomus_Outreach.lead_enricher import LeadEnricher
from bagwell_Autonomus_Outreach.llm_messenger import LLMMessenger
from bot.email_manager import EmailManager


class OutreachOrchestrator:
    """Main orchestrator for autonomous institutional outreach."""

    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run
        Path(DATA_DIR).mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.enricher = LeadEnricher()
        self.messenger = LLMMessenger()
        self.email_manager = EmailManager()
        
        # Load outreach log
        self.outreach_log: Dict = self._load_outreach_log()

    def _load_outreach_log(self) -> Dict:
        """Load the outreach log."""
        if os.path.exists(OUTREACH_LOG_PATH):
            try:
                with open(OUTREACH_LOG_PATH, "r") as f:
                    return json.load(f)
            except:
                return {"campaigns": [], "daily_stats": {}}
        return {"campaigns": [], "daily_stats": {}}

    def _save_outreach_log(self) -> None:
        """Persist the outreach log."""
        with open(OUTREACH_LOG_PATH, "w") as f:
            json.dump(self.outreach_log, f, indent=2, default=str)

    def _get_daily_count(self) -> int:
        """Get today's outreach count."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        return self.outreach_log.get("daily_stats", {}).get(today, 0)

    def _increment_daily_count(self) -> None:
        """Increment today's outreach count."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if "daily_stats" not in self.outreach_log:
            self.outreach_log["daily_stats"] = {}
        self.outreach_log["daily_stats"][today] = self.outreach_log["daily_stats"].get(today, 0) + 1
        self._save_outreach_log()

    def _was_contacted(self, address: str) -> bool:
        """Check if address was already contacted."""
        for campaign in self.outreach_log.get("campaigns", []):
            if campaign.get("address") == address:
                return True
        return False

    def process_lead(self, lead: Dict) -> Optional[Dict]:
        """
        Process a single lead through the full pipeline.
        
        Returns:
            Dict with results or None if skipped
        """
        address = lead.get("address", "")
        
        # Skip if already contacted
        if self._was_contacted(address):
            logger.info(f"Already contacted {address[:10]}... Skipping.")
            return None
        
        # Check daily limit
        if self._get_daily_count() >= MAX_DAILY_OUTREACH:
            logger.warning(f"Daily limit reached ({MAX_DAILY_OUTREACH}). Stopping.")
            return None
        
        # Check if lead has email
        email = lead.get("email")
        if not email:
            logger.debug(f"No email for {address[:10]}... Skipping.")
            return None

        logger.info(f"Processing lead: {address[:10]}...")

        # Step 1: Enrich lead
        enriched = self.enricher.enrich_lead(lead)
        
        # Step 2: Generate personalized message
        subject, body = self.messenger.generate_message(enriched)
        
        if not subject or not body:
            logger.error(f"Failed to generate message for {address[:10]}...")
            return None
        
        # Generate HTML version
        html_body = self.messenger.generate_html_email(subject, body)
        
        # Step 3: Send email (or dry run)
        result = {
            "address": address,
            "email": email,
            "subject": subject,
            "body": body,
            "enrichment_status": enriched.get("enrichment_status", "unknown"),
            "timestamp": datetime.utcnow().isoformat(),
            "status": "pending",
        }
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would send to {email}")
            result["status"] = "dry_run"
            print(f"\n{'='*60}")
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print(f"{'='*60}")
            print(body[:500] + "..." if len(body) > 500 else body)
            print(f"{'='*60}\n")
        else:
            # Send via email manager
            success = self.email_manager.send_email(
                recipient_email=email,
                subject=subject,
                body_html=html_body,
                body_text=body,
            )
            
            if success:
                result["status"] = "sent"
                self._increment_daily_count()
                logger.success(f"Sent to {email}")
            else:
                result["status"] = "failed"
                logger.error(f"Failed to send to {email}")
        
        # Log the campaign
        self.outreach_log["campaigns"].append(result)
        self._save_outreach_log()
        
        return result

    def run_campaign(
        self,
        max_leads: int = 10,
        min_balance: float = 50.0,
        enrichment_only: bool = False,
    ) -> Dict:
        """
        Run a full outreach campaign.
        
        Args:
            max_leads: Maximum number of leads to process
            min_balance: Minimum balance threshold
            enrichment_only: Only enrich, don't send
            
        Returns:
            Dict with campaign statistics
        """
        logger.info("Starting outreach campaign...")
        logger.info(f"Max leads: {max_leads}, Min balance: {min_balance}")
        
        # Load leads
        leads = self.enricher.load_leads_from_csv()
        
        # Filter by balance
        qualified_leads = [
            l for l in leads 
            if l.get("balance", 0) >= min_balance
        ]
        
        logger.info(f"Qualified leads: {len(qualified_leads)} / {len(leads)}")
        
        # Limit
        to_process = qualified_leads[:max_leads]
        
        stats = {
            "total_qualified": len(qualified_leads),
            "processed": 0,
            "sent": 0,
            "skipped": 0,
            "failed": 0,
            "dry_run": self.dry_run,
            "timestamp": datetime.utcnow().isoformat(),
        }
        
        for i, lead in enumerate(to_process):
            logger.info(f"Processing {i+1}/{len(to_process)}")
            
            result = self.process_lead(lead)
            
            if result:
                stats["processed"] += 1
                if result["status"] == "sent":
                    stats["sent"] += 1
                elif result["status"] == "failed":
                    stats["failed"] += 1
                elif result["status"] == "dry_run":
                    stats["sent"] += 1  # Count dry runs as "sent" for stats
            else:
                stats["skipped"] += 1
            
            # Rate limiting between emails
            if not self.dry_run and i < len(to_process) - 1:
                logger.info(f"Waiting {MINUTES_BETWEEN_EMAILS} minutes before next email...")
                time.sleep(MINUTES_BETWEEN_EMAILS * 60)
        
        logger.info(f"Campaign complete: {stats}")
        return stats

    def enrich_only(self, max_leads: int = None) -> List[Dict]:
        """
        Run enrichment only without sending emails.
        Useful for building the lead database.
        """
        logger.info("Running enrichment-only mode...")
        
        leads = self.enricher.load_leads_from_csv()
        
        if max_leads:
            leads = leads[:max_leads]
        
        enriched = []
        for i, lead in enumerate(leads):
            logger.info(f"Enriching {i+1}/{len(leads)}")
            result = self.enricher.enrich_lead(lead)
            enriched.append(result)
            time.sleep(2)  # Rate limiting
        
        logger.info(f"Enriched {len(enriched)} leads")
        return enriched


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Bagwell Autonomous Outreach System"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without sending emails",
    )
    parser.add_argument(
        "--enrich-only",
        action="store_true",
        help="Only enrich leads, don't send",
    )
    parser.add_argument(
        "--max-leads",
        type=int,
        default=10,
        help="Maximum leads to process (default: 10)",
    )
    parser.add_argument(
        "--min-balance",
        type=float,
        default=50.0,
        help="Minimum balance threshold (default: 50)",
    )
    
    args = parser.parse_args()
    
    # Initialize orchestrator
    orchestrator = OutreachOrchestrator(dry_run=args.dry_run)
    
    if args.enrich_only:
        # Enrichment only
        orchestrator.enrich_only(max_leads=args.max_leads)
    else:
        # Full campaign
        stats = orchestrator.run_campaign(
            max_leads=args.max_leads,
            min_balance=args.min_balance,
        )
        print(f"\nCampaign Stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    main()