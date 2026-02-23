import os
import asyncio
import time
from loguru import logger
from typing import Dict, Any
from bot.alerts import send_discord_alert

class AlertManager:
    """
    Centralized Alert Manager for Kerne Protocol Bots.
    Handles heartbeats, status reports, and deduplication of alerts.
    """
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.last_heartbeat = 0
        self.alert_history: Dict[str, float] = {}
        self.MIN_ALERT_INTERVAL = 300 # 5 minutes for same alert

    async def send_heartbeat(self):
        """Sends a heartbeat to Discord to signal the bot is alive."""
        now = time.time()
        if now - self.last_heartbeat > 3600: # Hourly heartbeat
            msg = f"💚 **Heartbeat**: {self.service_name} is operational."
            send_discord_alert(msg, level="INFO")
            self.last_heartbeat = now
            logger.info(f"Heartbeat sent for {self.service_name}")

    def notify(self, message: str, level: str = "INFO", dedupe_key: str = ""):
        """Sends a notification with optional deduplication."""
        now = time.time()
        key = dedupe_key or message
        
        if key in self.alert_history:
            if now - self.alert_history[key] < self.MIN_ALERT_INTERVAL:
                logger.debug(f"Deduplicating alert: {message}")
                return

        send_discord_alert(f"[{self.service_name}] {message}", level=level)
        self.alert_history[key] = now
        logger.info(f"Notification sent: {message}")

    async def start_heartbeat_loop(self):
        """Starts an infinite loop for heartbeats."""
        logger.info(f"Starting heartbeat loop for {self.service_name}")
        while True:
            await self.send_heartbeat()
            await asyncio.sleep(60) # Check every minute

if __name__ == "__main__":
    # Test
    am = AlertManager("TestService")
    am.notify("Test message", level="INFO")
    asyncio.run(am.send_heartbeat())
