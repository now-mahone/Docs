# Created: 2026-01-22
# Kerne Growth Automation System

This system automates lead discovery, outreach preparation, CRM-style pipeline tracking, and KPI reporting for the 12-category outreach matrix in `docs/marketing/growth_targets_ranked.md`.

## Core Modules

| Module | Purpose | File |
| --- | --- | --- |
| Lead Database | SQLite-backed lead storage + pipeline stats | `bot/growth/lead_database.py` |
| Discovery Engine | Ingests on-chain leads + curated CSVs | `bot/growth/discovery_engine.py` |
| Outreach Manager | Category/channel templates + message generation | `bot/growth/outreach_manager.py` |
| Pipeline Tracker | CRM stage transitions + outreach logging | `bot/growth/pipeline_tracker.py` |
| KPI Dashboard | Weekly KPI snapshot + report | `bot/growth/kpi_dashboard.py` |
| Growth Runner | Single entrypoint to run tasks | `bot/growth/growth_runner.py` |

## Discovery Inputs

- **On-chain whales**: `docs/institutional_leads.csv` (from `bot/lead_scanner_v3.py`).
- **Whale CSV**: `docs/leads/leads_v2.csv`.
- **Curated target lists**: any `*_targets.csv` in `docs/leads/`.

Template example: `docs/leads/sample_targets_TEMPLATE.csv`

## Templates

Default templates are embedded in `bot/growth/outreach_manager.py` and can be overridden with:
`docs/leads/outreach_templates.json`.

## Running the System

### 1. Run discovery
```bash
python -m bot.growth.growth_runner
```

### 2. Generate outreach queue
The runner exports `docs/leads/outreach_queue.json` (Twitter DM by default).

### 3. Mark pipeline updates
Use `PipelineTracker` to move leads between stages.

```python
from bot.growth.pipeline_tracker import PipelineTracker
from bot.growth.lead_database import PipelineStage

tracker = PipelineTracker()
tracker.advance_stage("lead_id", PipelineStage.RESPONDED, "Replied on X")
```

### 4. Weekly KPI report
```bash
python -m bot.growth.kpi_dashboard
```

Outputs a markdown report in `docs/reports/GROWTH_KPI_YYYY-MM-DD.md`.

## Next Steps

- Add category-specific curated target CSVs (KOLs, funds, LSTs, DAO treasuries, etc.).
- Update `docs/leads/outreach_templates.json` with custom scripts.
- Use `LeadDatabase.export_to_csv()` for sharing with external CRM tools if needed.