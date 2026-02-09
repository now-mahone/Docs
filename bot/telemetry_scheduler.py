# Created: 2026-01-21
# Updated: 2026-02-08 - Switched to DailyPerformanceReporter v2.0
"""
Kerne Protocol - Telemetry Scheduler

Daemon script that runs daily performance reports at a configurable time.
Designed for containerized deployment with proper signal handling.

Reports include:
- Hyperliquid equity, positions, funding rates, P&L
- On-chain wallet balances across Base + Arbitrum
- Solvency ratio, net delta, health status
- Yield metrics from funding rate capture
"""
from __future__ import annotations

import os
import signal
import sys
import time
from datetime import datetime, timezone, timedelta

from loguru import logger

# Configure logging
logger.remove()
logger.add(
    sys.stdout,
    format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>",
    level="INFO",
)

# Graceful shutdown flag
shutdown_requested = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global shutdown_requested
    logger.warning(f"Received signal {signum}, initiating graceful shutdown...")
    shutdown_requested = True


def get_seconds_until_target(target_hour: int = 9, target_minute: int = 0) -> int:
    """
    Calculate seconds until the next occurrence of target time (UTC).

    Default: 9:00 AM UTC (2:00 AM Denver / 4:00 PM London)
    """
    now = datetime.now(tz=timezone.utc)
    target = now.replace(hour=target_hour, minute=target_minute, second=0, microsecond=0)

    # If target time has passed today, schedule for tomorrow
    if now >= target:
        target += timedelta(days=1)

    delta = (target - now).total_seconds()
    return int(delta)


def run_telemetry() -> bool:
    """Execute the daily performance report."""
    try:
        from daily_performance_report import DailyPerformanceReporter

        logger.info("Starting scheduled performance report...")
        reporter = DailyPerformanceReporter()
        report = reporter.run(post_discord=True, save_files=True)

        logger.success(
            f"Report complete: ${report.total_assets_usd:,.2f} total | "
            f"HL: ${report.hyperliquid.account_value_usd:,.2f} | "
            f"On-chain: ${report.onchain.total_onchain_usd:,.2f} | "
            f"Delta: {report.net_delta_eth:+.6f} ETH | "
            f"Funding APY: {report.annualized_funding_apy:.2f}% | "
            f"Health: {report.health_status}"
        )
        return True

    except Exception as e:
        logger.error(f"Performance report failed: {e}")
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
    run_hour = int(os.getenv("TELEMETRY_HOUR_UTC", "9"))  # 9 AM UTC default
    run_minute = int(os.getenv("TELEMETRY_MINUTE_UTC", "0"))
    run_on_startup = os.getenv("TELEMETRY_RUN_ON_STARTUP", "true").lower() == "true"
    interval_override = os.getenv("TELEMETRY_INTERVAL_HOURS", "")  # For testing

    logger.info("=" * 60)
    logger.info("KERNE PERFORMANCE REPORT SCHEDULER v2.0")
    logger.info("=" * 60)
    logger.info(f"Scheduled time: {run_hour:02d}:{run_minute:02d} UTC")
    logger.info(f"Run on startup: {run_on_startup}")
    if interval_override:
        logger.info(f"Interval override: {interval_override} hours")
    logger.info("Data sources: Hyperliquid API + Base RPC + Arbitrum RPC")
    logger.info("Outputs: Discord embed + Markdown + JSON")
    logger.info("=" * 60)

    # Run immediately on startup if configured
    if run_on_startup:
        logger.info("Running initial performance report on startup...")
        run_telemetry()

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
                logger.info(f"Next report at {next_run.strftime('%Y-%m-%d %H:%M:%S')} UTC")
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

            # Run report
            success = run_telemetry()

            if not success:
                # If failed, retry in 5 minutes
                logger.warning("Retrying report in 5 minutes...")
                time.sleep(300)
                run_telemetry()

        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            # Sleep 5 minutes before retrying on error
            time.sleep(300)

    logger.info("Performance report scheduler shutdown complete")


if __name__ == "__main__":
    main()