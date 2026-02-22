// Created: 2026-02-22
"""
Configuration for Bagwell Autonomous Outreach System.
"""
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot/.env")

# ─────────────────────────────────────────────────────────────
# API KEYS
# ─────────────────────────────────────────────────────────────
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

# LLM Model Selection
LLM_MODEL = os.getenv("LLM_MODEL", "anthropic/claude-3.5-sonnet")
LLM_FALLBACK_MODEL = "openai/gpt-4o-mini"

# ─────────────────────────────────────────────────────────────
# LINKEDIN CONFIG
# ─────────────────────────────────────────────────────────────
LINKEDIN_EMAIL = os.getenv("LINKEDIN_EMAIL")
LINKEDIN_PASSWORD = os.getenv("LINKEDIN_PASSWORD")
LINKEDIN_ENABLED = bool(LINKEDIN_EMAIL and LINKEDIN_PASSWORD)

# ─────────────────────────────────────────────────────────────
# GOVERNANCE FORUM CONFIG
# ─────────────────────────────────────────────────────────────
FORUM_SOURCES = {
    "snapshot": {
        "enabled": True,
        "base_url": "https://snapshot.org",
    },
    "discourse": {
        "enabled": True,
        "known_forums": [
            "https://gov.uniswap.org",
            "https://gov.aave.com",
            "https://forum.curve.fi",
            "https://governance.aerodrome.finance",
        ]
    },
    "discord": {
        "enabled": False,  # Requires bot token
    }
}

# ─────────────────────────────────────────────────────────────
# RATE LIMITING
# ─────────────────────────────────────────────────────────────
MAX_DAILY_OUTREACH = 25
MINUTES_BETWEEN_EMAILS = 3
MAX_ENRICHMENT_RETRIES = 3

# ─────────────────────────────────────────────────────────────
# LLM PROMPT TEMPLATES
# ─────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """You are a professional business development assistant for Kerne Protocol, 
a delta-neutral yield infrastructure protocol on Base. Your task is to generate personalized, 
professional outreach messages to potential institutional partners and investors.

Key Kerne metrics to reference:
- 99.73% survival rate (Monte Carlo v4, 10,000 simulations)
- 21.78% mean APY
- $86.77M VaR 99% floor
- 9-layer protection architecture
- Non-custodial, on-chain vaults

Guidelines:
- Be concise (under 200 words)
- Reference specific aspects of the recipient's background
- Focus on value proposition relevant to them
- Include a clear call-to-action
- Professional but not overly formal
- Never use "I" - always use "we" (Kerne Protocol Team)
"""

MESSAGE_TEMPLATE = """Generate a personalized outreach email for the following lead:

LEAD PROFILE:
- Name: {name}
- Role: {role}
- Company: {company}
- LinkedIn Headline: {linkedin_headline}
- On-chain Holdings: {on_chain_holdings}
- Governance Activity: {governance_activity}
- Investment Focus: {investment_focus}
- Recent Activity: {recent_activity}

PERSONALIZATION CONTEXT:
{personalization_notes}

Generate a subject line and email body. Format as:
SUBJECT: [subject line]
BODY: [email body]
"""

# ─────────────────────────────────────────────────────────────
# ENRICHMENT QUERIES
# ─────────────────────────────────────────────────────────────
GOVERNANCE_SEARCH_QUERIES = [
    "Kerne Protocol",
    "delta-neutral yield",
    "basis trading",
    "stablecoin yield",
    "DeFi yield",
    "institutional DeFi",
]

# ─────────────────────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────────────────────
DATA_DIR = "bagwell_Autonomus_Outreach/data"
LEADS_CSV_PATH = "docs/institutional_leads.csv"
ENRICHED_LEADS_PATH = f"{DATA_DIR}/enriched_leads.json"
OUTREACH_LOG_PATH = f"{DATA_DIR}/outreach_log.json"