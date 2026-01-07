import os
import requests
from dotenv import load_dotenv
from loguru import logger

# Created: 2025-12-28

def send_discord_alert(message: str, level: str = "INFO"):
    """
    Sends a notification to a Discord channel via Webhook.
    """
    load_dotenv()
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    
    if not webhook_url or "your_discord_webhook_url" in webhook_url:
        logger.warning("Discord Webhook URL not configured. Skipping alert.")
        return

    try:
        # Prepend @everyone for critical alerts
        if level.upper() == "CRITICAL":
            content = f"🚨 **CRITICAL ALERT** @everyone\n{message}"
        else:
            content = f"ℹ️ **{level}**: {message}"

        payload = {
            "content": content,
            "username": "Kerne Bot"
        }

        response = requests.post(webhook_url, json=payload)
        response.raise_for_status()
        
    except Exception as e:
        logger.error(f"Failed to send Discord alert: {e}")
