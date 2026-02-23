# Created: 2026-01-21
"""
Kerne Protocol - Proof of Reserve Scheduler

Daemon script that runs PoR attestations at configurable intervals.
Designed for containerized deployment with proper signal handling.

Default: Daily at 00:00 UTC (The "Glass House Standard" attestation)
"""
from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta
from typing import Optional

from loguru import logger
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO"
)

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def get_seconds_until_target(target_hour: int = 0, target_minute: int = 0) -> int:
    """
    Calculate seconds until the next occurrence of target time (UTC).
    
    Default: 00:00 UTC (Midnight - clean daily boundary)
    """
    now = datetime.now(tz=timezone.utc)
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)
    
    # If target time has passed today, schedule for tomorrow
    if now >= target:
        target += timedelta(days=1)
    
    delta = (target - now).total_seconds()
    return int(delta)


def send_discord_alert(webhook_url: str, por_status: str, solvency_ratio: float, message: str = ""):
    """Send PoR result to Discord."""
    try:
        import requests
        
        if por_status == "SOLVENT":
            color = 0x00FF00  # Green
            emoji = "✅"
        elif "WARNING" in por_status:
            color = 0xFFFF00  # Yellow
            emoji = "⚠️"
        else:
            color = 0xFF0000  # Red
            emoji = "🚨"
        
        embed = {
            "title": f"{emoji} Kerne Proof of Reserve",
            "description": f"Daily solvency attestation complete",
            "color": color,
            "fields": [
                {"name": "Status", "value": por_status, "inline": True},
                {"name": "Solvency Ratio", "value": f"{solvency_ratio:.2%}", "inline": True},
            ],
            "footer": {"text": "Kerne PoR Bot - Glass House Standard"},
            "timestamp": datetime.now(tz=timezone.utc).isoformat()
        }
        
        if message:
            embed["fields"].append({"name": "Note", "value": message, "inline": False})
        
        response = requests.post(
            webhook_url,
            json={"embeds": [embed]},
            timeout=10
        )
        response.raise_for_status()
        logger.info("Discord PoR alert sent successfully")
        
    except Exception as e:
        logger.warning(f"Failed to send Discord alert: {e}")


def run_por_attestation(post_discord: bool = True) -> bool:
    """Execute the Proof of Reserve attestation cycle."""
    try:
        from por_automated import AutomatedPoRBot, AggregatedPoR
        
        logger.info("Starting scheduled PoR attestation...")
        bot = AutomatedPoRBot()
        
        # Run with full validation
        por = bot.run(save_json=True, save_markdown=True, validate=True)
        
        logger.success(
            f"PoR attestation complete: {por.status} | "
            f"Solvency: {por.aggregate_solvency_ratio:.2%} | "
            f"Assets: {por.total_assets_eth:.4f} ETH"
        )
        
        # Send Discord notification
        if post_discord:
            webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
            if webhook_url:
                send_discord_alert(
                    webhook_url,
                    por.status,
                    por.aggregate_solvency_ratio,
                    f"Hash: {por.attestation_hash[:16]}..."
                )
        
        return True
        
    except ValueError as e:
        # Invariant violation - critical error
        logger.critical(f"SOLVENCY INVARIANT VIOLATION: {e}")
        
        # Send critical alert
        webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
        if webhook_url:
            send_discord_alert(
                webhook_url,
                "CRITICAL",
                0.0,
                f"INVARIANT VIOLATED: {str(e)}"
            )
        
        return False
        
    except Exception as e:
        logger.error(f"PoR attestation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False


def main():
    """Main scheduler loop."""
    global shutdown_requested
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Configuration from environment
    run_hour = int(os.getenv("POR_HOUR_UTC", "0"))  # Midnight UTC default
    run_minute = int(os.getenv("POR_MINUTE_UTC", "0"))
    run_on_startup = os.getenv("POR_RUN_ON_STARTUP", "true").lower() == "true"
    interval_override = os.getenv("POR_INTERVAL_HOURS", "")  # For testing
    post_discord = os.getenv("POR_POST_DISCORD", "true").lower() == "true"
    
    logger.info("=" * 60)
    logger.info("KERNE PROOF OF RESERVE SCHEDULER STARTING")
    logger.info("The Glass House Standard - Daily Solvency Attestation")
    logger.info("=" * 60)
    logger.info(f"Scheduled time: {run_hour:02d}:{run_minute:02d} UTC")
    logger.info(f"Run on startup: {run_on_startup}")
    logger.info(f"Post to Discord: {post_discord}")
    if interval_override:
        logger.info(f"Interval override: {interval_override} hours")
    logger.info("=" * 60)
    
    # Run immediately on startup if configured
    if run_on_startup:
        logger.info("Running initial PoR attestation on startup...")
        run_por_attestation(post_discord=post_discord)
    
    # Main scheduling loop
    while not shutdown_requested:
        try:
            if interval_override:
                # Fixed interval mode (for testing)
                sleep_seconds = int(float(interval_override) * 3600)
                logger.info(f"Sleeping for {interval_override} hours ({sleep_seconds}s)...")
            else:
                # Time-based scheduling
                sleep_seconds = get_seconds_until_target(run_hour, run_minute)
                next_run = datetime.now(tz=timezone.utc) + timedelta(seconds=sleep_seconds)
                logger.info(f"Next PoR attestation at {next_run.strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logger.info(f"Sleeping for {sleep_seconds // 3600}h {(sleep_seconds % 3600) // 60}m...")
            
            # Sleep in small increments to check for shutdown
            sleep_chunk = 60  # Check every minute
            time_slept = 0
            
            while time_slept < sleep_seconds and not shutdown_requested:
                remaining = min(sleep_chunk, sleep_seconds - time_slept)
                time.sleep(remaining)
                time_slept += remaining
            
            if shutdown_requested:
                break
            
            # Run PoR attestation
            success = run_por_attestation(post_discord=post_discord)
            
            if not success:
                # If failed, retry in 15 minutes
                logger.warning("Retrying PoR attestation in 15 minutes...")
                time.sleep(900)
                run_por_attestation(post_discord=post_discord)
                
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            # Sleep 5 minutes before retrying on error
            time.sleep(300)
    
    logger.info("PoR scheduler shutdown complete")


if __name__ == "__main__":
    main()
