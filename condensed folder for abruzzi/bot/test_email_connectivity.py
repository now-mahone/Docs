# Created: 2026-02-07
# Updated: 2026-02-22 — Fixed wrong test domain (was kerne.systems, should be kerne.ai)
#           and bypassed duplicate-contact guard so the test can always re-run.
"""
SMTP connectivity test for the Kerne email system.
Sends a real test email via smtp.resend.com to verify credentials and domain auth.

Usage:
    python bot/test_email_connectivity.py --to your@email.com
    python bot/test_email_connectivity.py  (sends to default test target)
"""
import sys
import os
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
from loguru import logger

load_dotenv(dotenv_path="bot/.env")


def test_connectivity(to_email: str = "team@kerne.ai"):
    """
    Test SMTP connectivity directly (bypasses EmailManager's duplicate guard).
    This is a pure connectivity + auth test, not a tracked outreach send.
    """
    smtp_host = os.getenv("SMTP_HOST", "smtp.resend.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))
    smtp_user = os.getenv("SMTP_USER", "resend")
    smtp_pass = os.getenv("SMTP_PASS") or os.getenv("RESEND_API_KEY")
    from_email = os.getenv("FROM_EMAIL", "team@kerne.ai")

    if not smtp_pass:
        logger.error("SMTP_PASS / RESEND_API_KEY not set in bot/.env")
        return False

    logger.info(f"Starting SMTP connectivity test...")
    logger.info(f"  Server : {smtp_host}:{smtp_port}")
    logger.info(f"  Auth   : {smtp_user}")
    logger.info(f"  From   : {from_email}")
    logger.info(f"  To     : {to_email}")

    msg = MIMEMultipart("alternative")
    msg["From"] = f"Kerne Protocol <{from_email}>"
    msg["To"] = to_email
    msg["Subject"] = "Kerne Protocol — SMTP Connectivity Test"
    html = (
        "<h2>SMTP Connectivity Test</h2>"
        "<p>This confirms that outbound email from <b>@kerne.ai</b> via Resend SMTP is working correctly.</p>"
        "<p>DNS records status: DKIM ✅ | SPF ✅ | Inbound MX ❌ (see audit report)</p>"
    )
    msg.attach(MIMEText("SMTP Connectivity Test — Kerne Protocol", "plain"))
    msg.attach(MIMEText(html, "html"))

    try:
        context = ssl.create_default_context()
        logger.info(f"Connecting via SMTP_SSL to {smtp_host}:{smtp_port}...")
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=30) as server:
            server.login(smtp_user, smtp_pass)
            server.sendmail(from_email, to_email, msg.as_string())

        logger.success(f"SMTP connection and authentication successful!")
        logger.success(f"Test email delivered to {to_email}")
        return True

    except smtplib.SMTPAuthenticationError as e:
        logger.error(f"Authentication failed. Check SMTP_USER / SMTP_PASS in bot/.env. Error: {e}")
        return False
    except smtplib.SMTPConnectError as e:
        logger.error(f"Cannot connect to {smtp_host}:{smtp_port}. Check network/firewall. Error: {e}")
        return False
    except Exception as e:
        logger.error(f"SMTP test failed: {e}")
        return False


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kerne Protocol SMTP connectivity test")
    parser.add_argument(
        "--to",
        default="team@kerne.ai",
        help="Recipient email address for the test (default: team@kerne.ai)"
    )
    args = parser.parse_args()

    success = test_connectivity(args.to)
    sys.exit(0 if success else 1)