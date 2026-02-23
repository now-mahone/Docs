// Created: 2026-02-22
"""
LLM Messenger for Bagwell Autonomous Outreach.

Uses OpenRouter API to generate hyper-personalized outreach messages
based on enriched lead data.
"""
import os
import json
import time
import requests
from typing import Dict, Optional, Tuple
from loguru import logger

from config import (
    OPENROUTER_API_KEY,
    OPENROUTER_BASE_URL,
    LLM_MODEL,
    LLM_FALLBACK_MODEL,
    SYSTEM_PROMPT,
    MESSAGE_TEMPLATE,
)


class LLMMessenger:
    """Generates personalized outreach messages using LLMs."""

    def __init__(self):
        self.api_key = OPENROUTER_API_KEY
        self.base_url = OPENROUTER_BASE_URL
        self.model = LLM_MODEL
        self.fallback_model = LLM_FALLBACK_MODEL

        if not self.api_key:
            logger.warning("OPENROUTER_API_KEY not set. LLM generation will fail.")

    def _build_prompt(self, enriched_lead: Dict) -> str:
        """Build the prompt for the LLM based on enriched lead data."""
        
        # Extract key fields
        name = enriched_lead.get("name", "there")
        role = enriched_lead.get("role", "investor")
        company = enriched_lead.get("company", "")
        headline = enriched_lead.get("headline", "")
        
        # On-chain holdings
        balance = enriched_lead.get("balance", 0)
        asset = enriched_lead.get("asset", "ETH")
        on_chain_holdings = f"{balance:.2f} {asset}" if balance else "Unknown"
        
        # Governance activity
        dao_memberships = enriched_lead.get("dao_memberships", [])
        snapshot_votes = enriched_lead.get("snapshot_votes", [])
        governance_activity = "Active in: " + ", ".join(dao_memberships) if dao_memberships else "Limited public activity"
        
        # Investment focus
        investment_focus = enriched_lead.get("inferred_investment_focus", [])
        investment_focus_str = ", ".join(investment_focus) if investment_focus else "DeFi yield"
        
        # Recent activity summary
        recent_votes = len(snapshot_votes)
        recent_activity = f"Voted on {recent_votes} proposals recently" if recent_votes > 0 else "No recent public activity"
        
        # Build personalization notes
        personalization_notes = []
        
        if dao_memberships:
            personalization_notes.append(f"Active governance participant in {', '.join(dao_memberships[:3])}")
        
        if balance > 100:
            personalization_notes.append(f"Significant {asset} holder on Base")
        
        if investment_focus:
            personalization_notes.append(f"Interest areas: {', '.join(investment_focus[:3])}")
        
        personalization_str = "\n".join(f"- {note}" for note in personalization_notes) if personalization_notes else "- DeFi investor with on-chain presence"

        return MESSAGE_TEMPLATE.format(
            name=name,
            role=role,
            company=company,
            linkedin_headline=headline or "Not available",
            on_chain_holdings=on_chain_holdings,
            governance_activity=governance_activity,
            investment_focus=investment_focus_str,
            recent_activity=recent_activity,
            personalization_notes=personalization_str,
        )

    def _call_openrouter(self, messages: list, model: str) -> Optional[str]:
        """Make API call to OpenRouter."""
        if not self.api_key:
            logger.error("No OpenRouter API key configured")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://kerne.ai",
            "X-Title": "Kerne Protocol Outreach",
        }

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": 500,
            "temperature": 0.7,
        }

        try:
            resp = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=60
            )
            
            if resp.status_code == 200:
                data = resp.json()
                return data.get("choices", [{}])[0].get("message", {}).get("content")
            else:
                logger.error(f"OpenRouter error: {resp.status_code} - {resp.text}")
                return None
                
        except requests.exceptions.Timeout:
            logger.error("OpenRouter request timed out")
            return None
        except Exception as e:
            logger.error(f"OpenRouter request failed: {e}")
            return None

    def generate_message(self, enriched_lead: Dict) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate a personalized outreach message for a lead.
        
        Returns:
            Tuple of (subject, body) or (None, None) on failure
        """
        if not self.api_key:
            logger.warning("Skipping message generation - no API key")
            return self._generate_fallback_message(enriched_lead)

        prompt = self._build_prompt(enriched_lead)
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ]

        logger.info(f"Generating message for {enriched_lead.get('address', 'unknown')[:10]}...")

        # Try primary model
        response = self._call_openrouter(messages, self.model)
        
        # Fallback to secondary model if primary fails
        if not response:
            logger.warning(f"Primary model {self.model} failed, trying fallback...")
            response = self._call_openrouter(messages, self.fallback_model)

        if not response:
            logger.error("Both models failed, using fallback template")
            return self._generate_fallback_message(enriched_lead)

        # Parse response
        try:
            subject, body = self._parse_llm_response(response)
            return subject, body
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            return self._generate_fallback_message(enriched_lead)

    def _parse_llm_response(self, response: str) -> Tuple[str, str]:
        """Parse the LLM response into subject and body."""
        lines = response.strip().split("\n")
        
        subject = "Institutional Yield Infrastructure for Your Portfolio"
        body_lines = []
        in_body = False
        
        for line in lines:
            line = line.strip()
            if line.upper().startswith("SUBJECT:"):
                subject = line[8:].strip()
                in_body = False
            elif line.upper().startswith("BODY:"):
                in_body = True
            elif in_body:
                body_lines.append(line)
        
        body = "\n".join(body_lines).strip()
        
        if not body:
            # If parsing failed, treat whole response as body
            body = response
        
        return subject, body

    def _generate_fallback_message(self, enriched_lead: Dict) -> Tuple[str, str]:
        """Generate a simple template-based message if LLM fails."""
        address = enriched_lead.get("address", "")
        balance = enriched_lead.get("balance", 0)
        asset = enriched_lead.get("asset", "ETH")
        
        # Determine tier
        if balance >= 500:
            tier = "significant institutional"
        elif balance >= 100:
            tier = "substantial"
        else:
            tier = "notable"

        subject = f"Institutional Yield Infrastructure for {asset} Holdings"
        
        body = f"""Hello,

We noticed your {tier} {asset} position on Base and wanted to introduce Kerne Protocol — institutional-grade delta-neutral yield infrastructure.

What We Offer:
- Delta-Neutral Yield: 8-21% APY through basis trading
- No Directional Risk: Fully hedged positions eliminate price exposure
- Institutional Security: 99.73% survival rate (Monte Carlo v4), 9-layer protection
- Non-Custodial: Your assets remain in on-chain vaults you control

Current Metrics:
- 21.78% mean APY
- $86.77M VaR 99% floor
- Zero oracle manipulation failures

We would welcome the opportunity to discuss how Kerne can optimize yield on your {asset} holdings.

Best regards,
Kerne Protocol Team
https://kerne.ai"""

        return subject, body

    def generate_html_email(self, subject: str, body: str) -> str:
        """Convert plain text email to HTML format."""
        html_body = body.replace("\n", "<br>")
        
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a; padding: 20px;">
    <div style="border-bottom: 2px solid #0a0a0a; padding-bottom: 16px; margin-bottom: 24px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Kerne Protocol</h2>
        <p style="margin: 4px 0 0; font-size: 13px; color: #666;">Delta-Neutral Yield Infrastructure</p>
    </div>
    
    <div style="line-height: 1.6;">
        {html_body}
    </div>
    
    <hr style="border: none; border-top: 1px solid #eee; margin-top: 32px;">
    <p style="font-size: 11px; color: #999;">
        You're receiving this because your on-chain activity indicates potential interest
        in yield optimization. If you'd prefer not to hear from us, simply reply with
        "unsubscribe" and we'll remove you from future communications.
    </p>
</body>
</html>"""
        return html


def test_llm_messenger():
    """Test the LLM messenger with a sample lead."""
    messenger = LLMMessenger()
    
    sample_lead = {
        "address": "0x1234567890abcdef1234567890abcdef12345678",
        "balance": 150.5,
        "asset": "WETH",
        "dao_memberships": ["Uniswap", "Aave"],
        "inferred_investment_focus": ["DeFi", "Lending", "Yield"],
        "snapshot_votes": [{"space": {"name": "Uniswap"}}],
    }
    
    subject, body = messenger.generate_message(sample_lead)
    print(f"\nSubject: {subject}")
    print(f"\nBody:\n{body}")
    
    return subject, body


if __name__ == "__main__":
    test_llm_messenger()