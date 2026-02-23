// Created: 2026-02-22
# Bagwell Autonomous Outreach System

## Overview
Autonomous institutional outreach system for Kerne Protocol that generates hyper-personalized messages using LLMs and enriches leads with LinkedIn/governance forum data.

## Components

### 1. Lead Enrichment (`lead_enricher.py`)
- Matches on-chain addresses to LinkedIn profiles
- Scrapes governance forum activity (Snapshot, Discourse, Discords)
- Builds comprehensive lead profiles

### 2. LLM Message Generator (`llm_messenger.py`)
- Uses OpenRouter API to generate personalized outreach
- Tailors messages based on lead's:
  - Investment thesis (from governance activity)
  - Professional background (from LinkedIn)
  - On-chain behavior (from lead scanner)

### 3. Outreach Orchestrator (`orchestrator.py`)
- Coordinates enrichment, generation, and sending
- Manages rate limits and cooldowns
- Tracks all outreach in unified log

### 4. Configuration (`config.py`)
- API keys (OpenRouter, LinkedIn, etc.)
- Message templates and LLM prompts
- Rate limiting parameters

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure `.env`:
```
OPENROUTER_API_KEY=your_key
LINKEDIN_EMAIL=your_email
LINKEDIN_PASSWORD=your_password
SMTP_PASS=your_smtp_key
```

3. Run:
```bash
python orchestrator.py
```

## Architecture

```
Lead Scanner (existing)
        ↓
    [CSV Export]
        ↓
Lead Enricher → LinkedIn/Governance Data
        ↓
LLM Messenger → Personalized Messages
        ↓
Email Manager (existing) → SMTP Send
        ↓
Outreach Log