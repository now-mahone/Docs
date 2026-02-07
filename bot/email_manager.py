# Created: 2026-02-07
"""
Autonomous ProtonMail Outreach Manager for Kerne Protocol.

Uses ProtonMail Bridge SMTP to send institutional outreach emails
to whale leads discovered by the lead scanner.

Requirements:
- ProtonMail Bridge running locally (https://proton.me/mail/bridge)
- Bridge generates an app-specific password for SMTP auth
- Environment variables configured in bot/.env

Environment Variables:
    PROTON_SMTP_HOST: ProtonMail Bridge SMTP host (default: 127.0.0.1)
    PROTON_SMTP_PORT: ProtonMail Bridge SMTP port (default: 1025)
    PROTON_EMAIL: Your ProtonMail address (default: contact@kerne.systems)
    PROTON_PASSWORD: Bridge-generated app password (REQUIRED)
    AUTONOMOUS_OUTREACH: Set to "true" to enable autonomous sending
"""

import os
import ssl
import json
import smtplib
import hashlib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

load_dotenv(dotenv_path="bot/.env")

# Outreach tracking file to prevent duplicate sends
OUTREACH_LOG_PATH = Path("bot/data/outreach_log.json")
# Rate limiting: max emails per day
MAX_EMAILS_PER_DAY = 20
# Cooldown between emails (seconds)
EMAIL_COOLDOWN_SECONDS = 60


class EmailManager:
    """Manages autonomous email outreach via ProtonMail Bridge SMTP."""

    def __init__(self):
        self.smtp_host: str = os.getenv("PROTON_SMTP_HOST", "127.0.0.1")
        self.smtp_port: int = int(os.getenv("PROTON_SMTP_PORT", "1025"))
        self.email_user: str = os.getenv("PROTON_EMAIL", "contact@kerne.systems")
        self.email_pass: Optional[str] = os.getenv("PROTON_PASSWORD")
        self.from_name: str = "Kerne Protocol"
        self.outreach_log: Dict = self._load_outreach_log()

    def _load_outreach_log(self) -> Dict:
        """Load the outreach log to track sent emails and prevent duplicates."""
        OUTREACH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        if OUTREACH_LOG_PATH.exists():
            try:
                with open(OUTREACH_LOG_PATH, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                logger.warning("Corrupted outreach log, starting fresh")
                return {"sent": {}, "daily_counts": {}}
        return {"sent": {}, "daily_counts": {}}

    def _save_outreach_log(self) -> None:
        """Persist the outreach log to disk."""
        OUTREACH_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
        with open(OUTREACH_LOG_PATH, "w") as f:
            json.dump(self.outreach_log, f, indent=2, default=str)

    def _get_recipient_hash(self, recipient: str) -> str:
        """Hash recipient for privacy-safe dedup tracking."""
        return hashlib.sha256(recipient.lower().encode()).hexdigest()[:16]

    def _check_daily_limit(self) -> bool:
        """Check if we've hit the daily email send limit."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        daily_count = self.outreach_log.get("daily_counts", {}).get(today, 0)
        if daily_count >= MAX_EMAILS_PER_DAY:
            logger.warning(f"Daily email limit reached ({MAX_EMAILS_PER_DAY}). Skipping.")
            return False
        return True

    def _increment_daily_count(self) -> None:
        """Increment the daily send counter."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        if "daily_counts" not in self.outreach_log:
            self.outreach_log["daily_counts"] = {}
        self.outreach_log["daily_counts"][today] = (
            self.outreach_log["daily_counts"].get(today, 0) + 1
        )

    def _was_already_contacted(self, recipient: str) -> bool:
        """Check if this recipient was already contacted."""
        recipient_hash = self._get_recipient_hash(recipient)
        return recipient_hash in self.outreach_log.get("sent", {})

    def _record_sent(self, recipient: str, subject: str) -> None:
        """Record that an email was sent to this recipient."""
        recipient_hash = self._get_recipient_hash(recipient)
        if "sent" not in self.outreach_log:
            self.outreach_log["sent"] = {}
        self.outreach_log["sent"][recipient_hash] = {
            "timestamp": datetime.utcnow().isoformat(),
            "subject": subject,
        }
        self._increment_daily_count()
        self._save_outreach_log()

    def is_configured(self) -> bool:
        """Check if ProtonMail Bridge credentials are configured."""
        if not self.email_pass:
            logger.error(
                "PROTON_PASSWORD not set. Install ProtonMail Bridge and set the "
                "bridge-generated password in bot/.env"
            )
            return False
        return True

    def send_email(
        self,
        recipient_email: str,
        subject: str,
        body_html: str,
        body_text: Optional[str] = None,
    ) -> bool:
        """
        Send an email via ProtonMail Bridge SMTP.

        Args:
            recipient_email: Target email address
            subject: Email subject line
            body_html: HTML body content
            body_text: Plain text fallback (auto-generated if not provided)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_configured():
            return False

        if self._was_already_contacted(recipient_email):
            logger.info(f"Already contacted {recipient_email[:20]}... Skipping.")
            return False

        if not self._check_daily_limit():
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = f"{self.from_name} <{self.email_user}>"
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg["Reply-To"] = self.email_user

        # Plain text fallback
        if not body_text:
            body_text = body_html.replace("<br>", "\n").replace("<p>", "\n")
            # Strip remaining HTML tags
            import re
            body_text = re.sub(r"<[^>]+>", "", body_text)

        msg.attach(MIMEText(body_text, "plain"))
        msg.attach(MIMEText(body_html, "html"))

        try:
            # ProtonMail Bridge uses STARTTLS on port 1025
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                server.ehlo()
                server.starttls(context=context)
                server.ehlo()
                server.login(self.email_user, self.email_pass)
                server.sendmail(self.email_user, recipient_email, msg.as_string())

            logger.success(f"Email sent to {recipient_email}")
            self._record_sent(recipient_email, subject)
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(
                f"SMTP auth failed. Ensure ProtonMail Bridge is running and "
                f"PROTON_PASSWORD is the bridge-generated password. Error: {e}"
            )
            return False
        except smtplib.SMTPConnectError as e:
            logger.error(
                f"Cannot connect to ProtonMail Bridge at {self.smtp_host}:{self.smtp_port}. "
                f"Ensure Bridge is running. Error: {e}"
            )
            return False
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False

    def generate_institutional_pitch(
        self,
        address: str,
        balance: float,
        asset: str,
    ) -> Dict[str, str]:
        """
        Generate a tailored institutional outreach email for a whale lead.

        Args:
            address: On-chain wallet address
            balance: Token balance (in ETH/token units)
            asset: Asset name (WETH, cbETH, wstETH)

        Returns:
            Dict with 'subject' and 'body_html' keys
        """
        # Tier classification for personalization
        if balance >= 500:
            tier = "Tier 1"
            tier_label = "significant institutional"
        elif balance >= 100:
            tier = "Tier 2"
            tier_label = "substantial"
        else:
            tier = "Tier 3"
            tier_label = "notable"

        # Asset-specific yield messaging
        asset_yields = {
            "WETH": "8-15% APY through delta-neutral basis trading",
            "cbETH": "12-20% APY by combining native staking yield with basis spreads",
            "wstETH": "10-18% APY through Lido staking + hedged basis positions",
        }
        yield_msg = asset_yields.get(asset, "8-20% APY through delta-neutral strategies")

        subject = f"Institutional Yield Infrastructure for {asset} Holdings"

        body_html = f"""
<div style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; color: #1a1a1a;">
    <div style="border-bottom: 2px solid #0a0a0a; padding-bottom: 16px; margin-bottom: 24px;">
        <h2 style="margin: 0; font-size: 20px; font-weight: 600;">Kerne Protocol</h2>
        <p style="margin: 4px 0 0; font-size: 13px; color: #666;">Delta-Neutral Yield Infrastructure</p>
    </div>

    <p>Hello,</p>

    <p>We noticed your {tier_label} {asset} position on Base and wanted to introduce
    <strong>Kerne Protocol</strong> — institutional-grade delta-neutral yield infrastructure
    designed specifically for holders like you.</p>

    <h3 style="font-size: 16px; margin-top: 24px;">What We Offer</h3>
    <ul style="line-height: 1.8;">
        <li><strong>Delta-Neutral Yield:</strong> {yield_msg}</li>
        <li><strong>No Directional Risk:</strong> Fully hedged positions eliminate price exposure</li>
        <li><strong>Institutional Security:</strong> Audited smart contracts, real-time Proof of Reserves</li>
        <li><strong>Non-Custodial:</strong> Your assets remain in on-chain vaults you control</li>
    </ul>

    <h3 style="font-size: 16px; margin-top: 24px;">How It Works</h3>
    <p>Kerne captures the funding rate spread between spot and perpetual futures markets.
    By holding spot {asset} and shorting equivalent perpetuals, we generate consistent yield
    regardless of market direction. This is the same strategy used by top quantitative funds,
    now accessible on-chain.</p>

    <div style="background: #f5f5f5; border-radius: 8px; padding: 16px; margin: 24px 0;">
        <p style="margin: 0; font-size: 14px;">
            <strong>Current Estimated Yield:</strong> {yield_msg}<br>
            <strong>Supported Assets:</strong> WETH, cbETH, wstETH<br>
            <strong>Network:</strong> Base (Coinbase L2)<br>
            <strong>Website:</strong> <a href="https://kerne.systems" style="color: #0066cc;">kerne.systems</a>
        </p>
    </div>

    <p>We'd welcome the opportunity to discuss how Kerne can optimize yield on your {asset} holdings.
    Feel free to reply to this email or reach out on our
    <a href="https://discord.gg/kerne" style="color: #0066cc;">Discord</a>.</p>

    <p style="margin-top: 24px;">Best regards,<br>
    <strong>Kerne Protocol Team</strong><br>
    <a href="https://kerne.systems" style="color: #0066cc;">kerne.systems</a></p>

    <hr style="border: none; border-top: 1px solid #eee; margin-top: 32px;">
    <p style="font-size: 11px; color: #999;">
        You're receiving this because your on-chain activity indicates potential interest
        in yield optimization. If you'd prefer not to hear from us, simply reply with
        "unsubscribe" and we'll remove you from future communications.
    </p>
</div>
"""
        return {"subject": subject, "body_html": body_html}

    def send_lead_outreach(
        self,
        recipient_email: str,
        address: str,
        balance: float,
        asset: str,
    ) -> bool:
        """
        Send an institutional outreach email to a lead.

        Args:
            recipient_email: Target email address
            address: On-chain wallet address
            balance: Token balance
            asset: Asset name

        Returns:
            True if sent successfully
        """
        pitch = self.generate_institutional_pitch(address, balance, asset)
        return self.send_email(
            recipient_email=recipient_email,
            subject=pitch["subject"],
            body_html=pitch["body_html"],
        )

    def send_batch_outreach(self, leads: List[Dict]) -> Dict[str, int]:
        """
        Send outreach emails to a batch of leads with rate limiting.

        Each lead dict should have:
            - email: str (recipient email)
            - address: str (wallet address)
            - balance: float
            - asset: str

        Returns:
            Dict with 'sent', 'skipped', 'failed' counts
        """
        results = {"sent": 0, "skipped": 0, "failed": 0}

        for lead in leads:
            email = lead.get("email")
            if not email:
                results["skipped"] += 1
                continue

            if self._was_already_contacted(email):
                logger.info(f"Already contacted {email[:20]}... Skipping.")
                results["skipped"] += 1
                continue

            if not self._check_daily_limit():
                logger.warning("Daily limit reached. Stopping batch.")
                results["skipped"] += len(leads) - sum(results.values())
                break

            success = self.send_lead_outreach(
                recipient_email=email,
                address=lead.get("address", "unknown"),
                balance=lead.get("balance", 0),
                asset=lead.get("asset", "ETH"),
            )

            if success:
                results["sent"] += 1
            else:
                results["failed"] += 1

            # Rate limiting cooldown between sends
            time.sleep(EMAIL_COOLDOWN_SECONDS)

        logger.info(
            f"Batch outreach complete: {results['sent']} sent, "
            f"{results['skipped']} skipped, {results['failed']} failed"
        )
        return results

    def get_outreach_stats(self) -> Dict:
        """Get statistics about outreach activity."""
        today = datetime.utcnow().strftime("%Y-%m-%d")
        total_sent = len(self.outreach_log.get("sent", {}))
        today_sent = self.outreach_log.get("daily_counts", {}).get(today, 0)
        remaining_today = MAX_EMAILS_PER_DAY - today_sent

        return {
            "total_contacts": total_sent,
            "sent_today": today_sent,
            "remaining_today": max(0, remaining_today),
            "daily_limit": MAX_EMAILS_PER_DAY,
        }


def run_autonomous_outreach():
    """
    Standalone entry point for autonomous outreach.
    Reads leads from docs/institutional_leads.csv and sends outreach.

    Note: This requires leads to have associated email addresses.
    On-chain addresses alone cannot be emailed — this function is designed
    to work with enriched lead data that includes contact info.
    """
    import csv

    mgr = EmailManager()
    if not mgr.is_configured():
        logger.error("Email manager not configured. Set PROTON_PASSWORD in bot/.env")
        return

    stats = mgr.get_outreach_stats()
    logger.info(f"Outreach stats: {stats}")

    # Load leads from CSV
    csv_path = Path("docs/institutional_leads.csv")
    if not csv_path.exists():
        logger.error(f"No leads file found at {csv_path}. Run lead_scanner_v3.py first.")
        return

    leads = []
    with open(csv_path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Only process leads that have an email field
            if row.get("Email"):
                leads.append({
                    "email": row["Email"],
                    "address": row.get("Address", ""),
                    "balance": float(row.get("Balance", 0)),
                    "asset": row.get("Asset", "ETH"),
                })

    if not leads:
        logger.info("No leads with email addresses found. Enrich leads data first.")
        return

    logger.info(f"Found {len(leads)} leads with email addresses. Starting outreach...")
    results = mgr.send_batch_outreach(leads)
    logger.info(f"Outreach results: {results}")


if __name__ == "__main__":
    run_autonomous_outreach()