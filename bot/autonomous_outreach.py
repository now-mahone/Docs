# Created: 2026-02-20
"""
Autonomous Institutional Lead Generation & Outreach Pipeline

This script:
1. Scrapes governance forums (e.g., Aave, Arbitrum) for treasury management proposals.
2. Ingests on-chain whale leads from `docs/institutional_leads.csv`.
3. Ingests curated investor targets from `docs/investor/SEED_INVESTOR_TARGETS.md`.
4. Uses OpenRouter (LLM) to draft highly personalized, context-aware outreach messages.
5. Queues messages for Twitter/LinkedIn DM or sends them autonomously via EmailManager if an email is found.
6. Implements collision avoidance by tracking contacted leads in `bot/data/outreach_log.json`.
"""

import os
import json
import csv
import time
import requests
import re
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger
from dotenv import load_dotenv
from bot.email_manager import EmailManager

load_dotenv(dotenv_path="bot/.env")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OUTREACH_QUEUE_PATH = Path("docs/leads/outreach_queue.json")
CONTACTED_LOG_PATH = Path("bot/data/contacted_leads.json")

# Ensure directories exist
OUTREACH_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
CONTACTED_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

class AutonomousOutreach:
    def __init__(self):
        self.email_mgr = EmailManager()
        self.contacted_leads = self._load_contacted_log()
        self.outreach_queue = self._load_queue()

    def _load_contacted_log(self) -> set:
        if CONTACTED_LOG_PATH.exists():
            try:
                with open(CONTACTED_LOG_PATH, "r") as f:
                    return set(json.load(f))
            except Exception:
                return set()
        return set()

    def _save_contacted_log(self):
        with open(CONTACTED_LOG_PATH, "w") as f:
            json.dump(list(self.contacted_leads), f, indent=2)

    def _load_queue(self) -> List[Dict]:
        if OUTREACH_QUEUE_PATH.exists():
            try:
                with open(OUTREACH_QUEUE_PATH, "r") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_queue(self):
        with open(OUTREACH_QUEUE_PATH, "w") as f:
            json.dump(self.outreach_queue, f, indent=2)

    def _generate_llm_pitch(self, lead_name: str, context: str, platform: str) -> str:
        """Uses OpenRouter to generate a highly personalized outreach message."""
        if not OPENROUTER_API_KEY:
            logger.warning("OPENROUTER_API_KEY not set. Using fallback template.")
            return f"Hi {lead_name}, I saw your work regarding {context}. I'm building Kerne Protocol, a delta-neutral yield infrastructure on Base. Would love to share our Data Room with you."

        prompt = f"""
        You are the Lead Architect of Kerne Protocol, a delta-neutral synthetic dollar protocol on Base generating 15-21% APY via basis trading.
        Write a highly personalized, concise, and professional outreach message (max 4 sentences) for {platform}.
        
        Target: {lead_name}
        Context: {context}
        
        Goal: Get them to review our Institutional Data Room (https://kerne.ai/data-room).
        Tone: Authoritative, institutional, direct. No fluff. Do not use the word "Manifesto" or "Weaponized". Use "we" instead of "I".
        """

        try:
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "meta-llama/llama-3.3-70b-instruct",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.7
                },
                timeout=15
            )
            response.raise_for_status()
            return response.json()["choices"][0]["message"]["content"].strip()
        except Exception as e:
            logger.error(f"LLM generation failed for {lead_name}: {e}")
            return f"Hi {lead_name}, regarding {context} — we are building Kerne Protocol, an institutional delta-neutral yield infrastructure on Base. We'd like to share our Data Room with you: https://kerne.ai/data-room"

    def scrape_governance_forums(self):
        """Scrapes Discourse forums for treasury management proposals."""
        logger.info("Scraping governance forums for treasury leads...")
        forums = [
            {"name": "Aave", "url": "https://governance.aave.com"},
            {"name": "Arbitrum", "url": "https://forum.arbitrum.foundation"}
        ]
        
        keywords = ["treasury", "yield", "diversification", "stablecoin", "idle capital"]
        
        for forum in forums:
            try:
                # Fetch latest topics
                res = requests.get(f"{forum['url']}/latest.json", timeout=10)
                if res.status_code != 200:
                    continue
                
                data = res.json()
                topics = data.get("topic_list", {}).get("topics", [])
                
                for topic in topics:
                    title = topic.get("title", "").lower()
                    if any(kw in title for kw in keywords):
                        author_username = topic.get("last_poster_username", "Unknown")
                        lead_id = f"forum_{forum['name']}_{author_username}"
                        
                        if lead_id in self.contacted_leads:
                            continue
                            
                        logger.success(f"Found governance lead: {author_username} on {forum['name']} (Topic: {title})")
                        
                        context = f"your recent proposal/post on the {forum['name']} forum regarding '{title}'"
                        message = self._generate_llm_pitch(author_username, context, "Forum DM / Twitter")
                        
                        self.outreach_queue.append({
                            "id": lead_id,
                            "name": author_username,
                            "source": f"{forum['name']} Governance",
                            "context": context,
                            "message": message,
                            "status": "queued",
                            "timestamp": time.time()
                        })
                        self.contacted_leads.add(lead_id)
                        
            except Exception as e:
                logger.error(f"Failed to scrape {forum['name']}: {e}")

    def process_investor_targets(self):
        """Parses SEED_INVESTOR_TARGETS.md and drafts personalized DMs."""
        logger.info("Processing curated investor targets...")
        target_file = Path("docs/investor/SEED_INVESTOR_TARGETS.md")
        if not target_file.exists():
            return

        with open(target_file, "r", encoding="utf-8") as f:
            content = f.read()

        # Simple regex to extract table rows
        rows = re.findall(r'\|\s*\d+\s*\|\s*\*\*(.*?)\*\*\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|\s*(.*?)\s*\|', content)
        
        for row in rows:
            fund_name, why_fit, key_person, twitter = [col.strip() for col in row]
            if not twitter or "apply via portal" in key_person.lower():
                continue
                
            lead_id = f"twitter_{twitter}"
            if lead_id in self.contacted_leads:
                continue
                
            logger.success(f"Processing investor target: {key_person} ({fund_name})")
            
            context = f"your investment focus at {fund_name} and {why_fit}"
            message = self._generate_llm_pitch(key_person, context, "Twitter DM")
            
            self.outreach_queue.append({
                "id": lead_id,
                "name": key_person,
                "source": "Curated Investor List",
                "twitter": twitter,
                "context": context,
                "message": message,
                "status": "queued",
                "timestamp": time.time()
            })
            self.contacted_leads.add(lead_id)

    def execute_pipeline(self):
        """Runs the full autonomous pipeline."""
        logger.info("Starting Autonomous Lead Generation Pipeline...")
        
        self.scrape_governance_forums()
        self.process_investor_targets()
        
        self._save_queue()
        self._save_contacted_log()
        
        logger.info(f"Pipeline complete. {len(self.outreach_queue)} leads queued in {OUTREACH_QUEUE_PATH}")
        
        # If any leads have emails, send them autonomously
        emails_to_send = [lead for lead in self.outreach_queue if lead.get("email") and lead["status"] == "queued"]
        if emails_to_send and self.email_mgr.is_configured():
            logger.info(f"Found {len(emails_to_send)} leads with emails. Initiating autonomous dispatch...")
            for lead in emails_to_send:
                success = self.email_mgr.send_email(
                    recipient_email=lead["email"],
                    subject=f"Kerne Protocol Data Room Access - {lead['name']}",
                    body_html=f"<p>{lead['message'].replace(chr(10), '<br>')}</p>"
                )
                if success:
                    lead["status"] = "sent"
                    self._save_queue()
                time.sleep(60) # Rate limit

if __name__ == "__main__":
    pipeline = AutonomousOutreach()
    pipeline.execute_pipeline()