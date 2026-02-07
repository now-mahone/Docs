# Created: 2026-02-07
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from bot.email_manager import EmailManager
from loguru import logger

def test_connectivity():
    logger.info("Starting SMTP connectivity test for Resend.com...")
    mgr = EmailManager()
    
    if not mgr.is_configured():
        logger.error("EmailManager is not correctly configured. Check bot/.env")
        return

    # We use a dummy recipient for the connection test
    # Note: This will actually attempt to send if credentials are valid
    # but Resend will likely reject it if the domain isn't verified yet.
    test_recipient = "test-verify@kerne.systems"
    subject = "Kerne Protocol - SMTP Connectivity Test"
    body_html = "<h1>Connectivity Test</h1><p>This is a test of the autonomous outreach SMTP configuration.</p>"
    
    logger.info(f"Attempting to connect to {mgr.smtp_host}:{mgr.smtp_port}...")
    success = mgr.send_email(
        recipient_email=test_recipient,
        subject=subject,
        body_html=body_html
    )
    
    if success:
        logger.success("SMTP Connection and Authentication Successful!")
    else:
        logger.error("SMTP Test Failed. This is expected if the domain 'kerne.systems' is not yet verified in the Resend dashboard.")
        logger.info("ACTION REQUIRED: Please ensure you have added the DNS records provided by Resend to your domain provider for kerne.systems.")

if __name__ == "__main__":
    test_connectivity()