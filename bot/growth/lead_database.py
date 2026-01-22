# Created: 2026-01-22
"""
Lead Database - Central storage for all growth leads across 12 categories.
Uses SQLite for persistence with JSON export capabilities.
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, asdict, field
from enum import Enum
from loguru import logger


class LeadCategory(Enum):
    """The 12 growth categories from the ranked matrix."""
    NARRATIVE_CARTEL = "1_narrative_cartel"  # KOLs, Alpha Callers, Media
    CRYPTO_WHALES = "2_crypto_whales"  # HNW Individuals
    DAO_TREASURIES = "3_dao_treasuries"  # Protocol Treasuries
    LST_PROVIDERS = "4_lst_providers"  # Liquid Staking Providers
    CRYPTO_FUNDS = "5_crypto_funds"  # VCs, Strategic Investors
    L2_FOUNDATIONS = "6_l2_foundations"  # Grants Programs
    CEX_LAUNCHPOOL = "7_cex_launchpool"  # Exchanges
    MARKET_MAKERS = "8_market_makers"  # Liquidity Providers
    DEFI_INTEGRATORS = "9_defi_integrators"  # Money Legos
    INSTITUTIONAL_RWA = "10_institutional_rwa"  # TradFi, RWA
    SOVEREIGN_WEALTH = "11_sovereign_wealth"  # Family Offices, SWFs
    ECOSYSTEM_BUILDERS = "12_ecosystem_builders"  # Developers


class PipelineStage(Enum):
    """CRM pipeline stages."""
    DISCOVERED = "discovered"  # Just found, no contact
    RESEARCHED = "researched"  # Social/contact info found
    CONTACTED = "contacted"  # First outreach sent
    RESPONDED = "responded"  # Got a reply
    MEETING_SCHEDULED = "meeting_scheduled"  # Call/meeting booked
    NEGOTIATING = "negotiating"  # Active discussions
    COMMITTED = "committed"  # Verbal/written commitment
    CONVERTED = "converted"  # Deposited/signed/integrated
    CHURNED = "churned"  # Lost/declined
    DORMANT = "dormant"  # No response after follow-ups


class ContactChannel(Enum):
    """Available outreach channels."""
    TWITTER_DM = "twitter_dm"
    TELEGRAM = "telegram"
    DISCORD = "discord"
    EMAIL = "email"
    FARCASTER = "farcaster"
    LINKEDIN = "linkedin"
    ONCHAIN_MESSAGE = "onchain_message"
    GOVERNANCE_FORUM = "governance_forum"
    WARM_INTRO = "warm_intro"
    CONFERENCE = "conference"


@dataclass
class Lead:
    """A single lead in the database."""
    id: str  # Unique identifier (wallet address or handle)
    category: LeadCategory
    name: Optional[str] = None  # Human name or entity name
    
    # Contact Information
    wallet_address: Optional[str] = None
    twitter_handle: Optional[str] = None
    telegram_handle: Optional[str] = None
    discord_handle: Optional[str] = None
    email: Optional[str] = None
    farcaster_handle: Optional[str] = None
    linkedin_url: Optional[str] = None
    website: Optional[str] = None
    ens_name: Optional[str] = None
    
    # Financial Metrics
    estimated_aum: Optional[float] = None  # In USD
    on_chain_balance: Optional[float] = None  # In USD
    potential_deposit: Optional[float] = None  # Expected deposit size
    
    # Pipeline Status
    stage: PipelineStage = PipelineStage.DISCOVERED
    priority: int = 3  # 1=highest, 5=lowest
    
    # Outreach Tracking
    first_contact_date: Optional[str] = None
    last_contact_date: Optional[str] = None
    contact_channel: Optional[ContactChannel] = None
    outreach_count: int = 0
    response_received: bool = False
    
    # Notes and Context
    notes: str = ""
    tags: List[str] = field(default_factory=list)
    research_links: List[str] = field(default_factory=list)
    
    # Metadata
    source: str = ""  # How we found them
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        d = asdict(self)
        d['category'] = self.category.value
        d['stage'] = self.stage.value
        d['contact_channel'] = self.contact_channel.value if self.contact_channel else None
        d['tags'] = json.dumps(self.tags)
        d['research_links'] = json.dumps(self.research_links)
        return d
    
    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> 'Lead':
        """Create from dictionary."""
        d['category'] = LeadCategory(d['category'])
        d['stage'] = PipelineStage(d['stage'])
        d['contact_channel'] = ContactChannel(d['contact_channel']) if d.get('contact_channel') else None
        d['tags'] = json.loads(d['tags']) if isinstance(d['tags'], str) else d['tags']
        d['research_links'] = json.loads(d['research_links']) if isinstance(d['research_links'], str) else d['research_links']
        return cls(**d)


class LeadDatabase:
    """SQLite-backed lead database with full CRUD operations."""
    
    def __init__(self, db_path: str = "bot/growth/leads.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize the database schema."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS leads (
                id TEXT PRIMARY KEY,
                category TEXT NOT NULL,
                name TEXT,
                wallet_address TEXT,
                twitter_handle TEXT,
                telegram_handle TEXT,
                discord_handle TEXT,
                email TEXT,
                farcaster_handle TEXT,
                linkedin_url TEXT,
                website TEXT,
                ens_name TEXT,
                estimated_aum REAL,
                on_chain_balance REAL,
                potential_deposit REAL,
                stage TEXT NOT NULL DEFAULT 'discovered',
                priority INTEGER DEFAULT 3,
                first_contact_date TEXT,
                last_contact_date TEXT,
                contact_channel TEXT,
                outreach_count INTEGER DEFAULT 0,
                response_received INTEGER DEFAULT 0,
                notes TEXT,
                tags TEXT,
                research_links TEXT,
                source TEXT,
                created_at TEXT,
                updated_at TEXT
            )
        ''')
        
        # Create indexes for common queries
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_category ON leads(category)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_stage ON leads(stage)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_priority ON leads(priority)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_wallet ON leads(wallet_address)')
        
        # Outreach history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS outreach_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                lead_id TEXT NOT NULL,
                channel TEXT NOT NULL,
                message_template TEXT,
                sent_at TEXT NOT NULL,
                response_received INTEGER DEFAULT 0,
                response_at TEXT,
                notes TEXT,
                FOREIGN KEY (lead_id) REFERENCES leads(id)
            )
        ''')
        
        # KPI snapshots table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS kpi_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                snapshot_date TEXT NOT NULL,
                category TEXT NOT NULL,
                total_leads INTEGER,
                discovered INTEGER,
                researched INTEGER,
                contacted INTEGER,
                responded INTEGER,
                meeting_scheduled INTEGER,
                negotiating INTEGER,
                committed INTEGER,
                converted INTEGER,
                churned INTEGER,
                dormant INTEGER,
                total_potential_tvl REAL,
                converted_tvl REAL
            )
        ''')
        
        conn.commit()
        conn.close()
        logger.info(f"Lead database initialized at {self.db_path}")
    
    def add_lead(self, lead: Lead) -> bool:
        """Add a new lead to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            d = lead.to_dict()
            columns = ', '.join(d.keys())
            placeholders = ', '.join(['?' for _ in d])
            cursor.execute(f'INSERT INTO leads ({columns}) VALUES ({placeholders})', list(d.values()))
            conn.commit()
            logger.info(f"Added lead: {lead.id} ({lead.category.value})")
            return True
        except sqlite3.IntegrityError:
            logger.warning(f"Lead already exists: {lead.id}")
            return False
        finally:
            conn.close()
    
    def update_lead(self, lead: Lead) -> bool:
        """Update an existing lead."""
        lead.updated_at = datetime.now().isoformat()
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        d = lead.to_dict()
        set_clause = ', '.join([f'{k} = ?' for k in d.keys() if k != 'id'])
        values = [v for k, v in d.items() if k != 'id'] + [lead.id]
        
        cursor.execute(f'UPDATE leads SET {set_clause} WHERE id = ?', values)
        conn.commit()
        conn.close()
        logger.info(f"Updated lead: {lead.id}")
        return True
    
    def get_lead(self, lead_id: str) -> Optional[Lead]:
        """Get a single lead by ID."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE id = ?', (lead_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return Lead.from_dict(dict(row))
        return None
    
    def get_leads_by_category(self, category: LeadCategory) -> List[Lead]:
        """Get all leads in a category."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE category = ? ORDER BY priority, created_at', (category.value,))
        rows = cursor.fetchall()
        conn.close()
        
        return [Lead.from_dict(dict(row)) for row in rows]
    
    def get_leads_by_stage(self, stage: PipelineStage) -> List[Lead]:
        """Get all leads at a pipeline stage."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads WHERE stage = ? ORDER BY priority, created_at', (stage.value,))
        rows = cursor.fetchall()
        conn.close()
        
        return [Lead.from_dict(dict(row)) for row in rows]
    
    def get_actionable_leads(self, limit: int = 50) -> List[Lead]:
        """Get leads that need action (discovered or researched, not contacted recently)."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM leads 
            WHERE stage IN ('discovered', 'researched', 'contacted')
            AND (last_contact_date IS NULL OR last_contact_date < date('now', '-3 days'))
            ORDER BY priority, estimated_aum DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        
        return [Lead.from_dict(dict(row)) for row in rows]
    
    def search_leads(self, query: str) -> List[Lead]:
        """Search leads by name, handle, or wallet."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        search_term = f'%{query}%'
        cursor.execute('''
            SELECT * FROM leads 
            WHERE name LIKE ? OR twitter_handle LIKE ? OR wallet_address LIKE ? 
            OR ens_name LIKE ? OR notes LIKE ?
            ORDER BY priority
        ''', (search_term, search_term, search_term, search_term, search_term))
        rows = cursor.fetchall()
        conn.close()
        
        return [Lead.from_dict(dict(row)) for row in rows]
    
    def log_outreach(self, lead_id: str, channel: ContactChannel, template: str = "", notes: str = ""):
        """Log an outreach attempt."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO outreach_history (lead_id, channel, message_template, sent_at, notes)
            VALUES (?, ?, ?, ?, ?)
        ''', (lead_id, channel.value, template, now, notes))
        
        # Update lead's outreach count and last contact date
        cursor.execute('''
            UPDATE leads SET 
                outreach_count = outreach_count + 1,
                last_contact_date = ?,
                contact_channel = ?,
                stage = CASE WHEN stage = 'discovered' OR stage = 'researched' THEN 'contacted' ELSE stage END,
                updated_at = ?
            WHERE id = ?
        ''', (now, channel.value, now, lead_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Logged outreach to {lead_id} via {channel.value}")
    
    def mark_response(self, lead_id: str, notes: str = ""):
        """Mark that a lead responded."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        now = datetime.now().isoformat()
        cursor.execute('''
            UPDATE leads SET 
                response_received = 1,
                stage = 'responded',
                updated_at = ?
            WHERE id = ?
        ''', (now, lead_id))
        
        # Update the most recent outreach record
        cursor.execute('''
            UPDATE outreach_history SET 
                response_received = 1,
                response_at = ?,
                notes = notes || ' | Response: ' || ?
            WHERE lead_id = ? 
            ORDER BY sent_at DESC LIMIT 1
        ''', (now, notes, lead_id))
        
        conn.commit()
        conn.close()
        logger.info(f"Marked response from {lead_id}")
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get current pipeline statistics."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        stats = {
            'total_leads': 0,
            'by_category': {},
            'by_stage': {},
            'total_potential_tvl': 0,
            'converted_tvl': 0,
            'response_rate': 0,
            'conversion_rate': 0
        }
        
        # Total leads
        cursor.execute('SELECT COUNT(*) FROM leads')
        stats['total_leads'] = cursor.fetchone()[0]
        
        # By category
        cursor.execute('SELECT category, COUNT(*) FROM leads GROUP BY category')
        stats['by_category'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # By stage
        cursor.execute('SELECT stage, COUNT(*) FROM leads GROUP BY stage')
        stats['by_stage'] = {row[0]: row[1] for row in cursor.fetchall()}
        
        # Potential TVL
        cursor.execute('SELECT SUM(potential_deposit) FROM leads WHERE potential_deposit IS NOT NULL')
        result = cursor.fetchone()[0]
        stats['total_potential_tvl'] = result if result else 0
        
        # Converted TVL
        cursor.execute('SELECT SUM(potential_deposit) FROM leads WHERE stage = "converted" AND potential_deposit IS NOT NULL')
        result = cursor.fetchone()[0]
        stats['converted_tvl'] = result if result else 0
        
        # Response rate
        cursor.execute('SELECT COUNT(*) FROM leads WHERE outreach_count > 0')
        contacted = cursor.fetchone()[0]
        cursor.execute('SELECT COUNT(*) FROM leads WHERE response_received = 1')
        responded = cursor.fetchone()[0]
        stats['response_rate'] = (responded / contacted * 100) if contacted > 0 else 0
        
        # Conversion rate
        cursor.execute('SELECT COUNT(*) FROM leads WHERE stage = "converted"')
        converted = cursor.fetchone()[0]
        stats['conversion_rate'] = (converted / stats['total_leads'] * 100) if stats['total_leads'] > 0 else 0
        
        conn.close()
        return stats
    
    def snapshot_kpis(self):
        """Take a snapshot of current KPIs for historical tracking."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        today = datetime.now().strftime('%Y-%m-%d')
        
        for category in LeadCategory:
            cursor.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN stage = 'discovered' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'researched' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'contacted' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'responded' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'meeting_scheduled' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'negotiating' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'committed' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'converted' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'churned' THEN 1 ELSE 0 END),
                    SUM(CASE WHEN stage = 'dormant' THEN 1 ELSE 0 END),
                    SUM(potential_deposit),
                    SUM(CASE WHEN stage = 'converted' THEN potential_deposit ELSE 0 END)
                FROM leads WHERE category = ?
            ''', (category.value,))
            
            row = cursor.fetchone()
            cursor.execute('''
                INSERT INTO kpi_snapshots (
                    snapshot_date, category, total_leads, discovered, researched,
                    contacted, responded, meeting_scheduled, negotiating, committed,
                    converted, churned, dormant, total_potential_tvl, converted_tvl
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (today, category.value, *row))
        
        conn.commit()
        conn.close()
        logger.info(f"KPI snapshot saved for {today}")
    
    def export_to_csv(self, filepath: str = "docs/leads/all_leads_export.csv"):
        """Export all leads to CSV."""
        import csv
        
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads ORDER BY category, priority')
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            logger.warning("No leads to export")
            return
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            for row in rows:
                writer.writerow(dict(row))
        
        logger.info(f"Exported {len(rows)} leads to {filepath}")
    
    def export_to_json(self, filepath: str = "docs/leads/all_leads_export.json"):
        """Export all leads to JSON."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM leads ORDER BY category, priority')
        rows = cursor.fetchall()
        conn.close()
        
        leads = [dict(row) for row in rows]
        
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(leads, f, indent=2)
        
        logger.info(f"Exported {len(leads)} leads to {filepath}")


if __name__ == "__main__":
    # Test the database
    db = LeadDatabase()
    
    # Add a test lead
    test_lead = Lead(
        id="test_whale_0x1234",
        category=LeadCategory.CRYPTO_WHALES,
        name="Test Whale",
        wallet_address="0x1234567890abcdef",
        twitter_handle="@testwhale",
        estimated_aum=5000000,
        potential_deposit=1000000,
        priority=1,
        source="on_chain_scanner",
        notes="High-value ETH holder on Base"
    )
    
    db.add_lead(test_lead)
    
    # Get stats
    stats = db.get_pipeline_stats()
    print(json.dumps(stats, indent=2))
