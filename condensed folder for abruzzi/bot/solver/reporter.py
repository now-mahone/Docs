# Created: 2026-01-13
import asyncio
from loguru import logger
import pandas as pd
import os
from datetime import datetime

class InstitutionalReporter:
    """
    Generates daily performance reports for institutional LPs.
    """
    def __init__(self):
        self.profit_log_path = "bot/solver/profit_log.csv"
        self.report_dir = "docs/reports/solver"
        if not os.path.exists(self.report_dir):
            os.makedirs(self.report_dir)

    def generate_daily_summary(self):
        if not os.path.exists(self.profit_log_path):
            return "No data"

        try:
            df = pd.read_csv(self.profit_log_path)
            # Convert timestamp to date
            df['date'] = df['timestamp'].apply(lambda x: datetime.fromtimestamp(x).strftime('%Y-%m-%d'))
            
            today = datetime.now().strftime('%Y-%m-%d')
            daily_df = df[df['date'] == today]
            
            if daily_df.empty:
                return "No trades today"

            total_trades = len(daily_df)
            wins = len(daily_df[daily_df['status'] == 'HEDGED'])
            total_profit = daily_df[daily_df['status'] == 'HEDGED']['profit_bps'].sum()
            
            report_content = f"""
KERNE SOLVER DAILY PERFORMANCE REPORT
Date: {today}
--------------------------------------
Total Intents Processed: {total_trades}
Successful Extractions: {wins}
Win Rate: {wins/total_trades:.2%}
Total Profit Captured: {total_profit:.2f} bps
Estimated Revenue (100 ETH base): ${total_profit * 0.0001 * 100 * 2500 / 365:.2f}
--------------------------------------
Status: {'TARGET_MET' if total_profit > 50 else 'TARGET_PENDING'}
"""
            report_path = f"{self.report_dir}/report_{today}.txt"
            with open(report_path, "w") as f:
                f.write(report_content)
            
            logger.success(f"Institutional report generated: {report_path}")
            return report_content
        except Exception as e:
            logger.error(f"Report Generation Error: {e}")
            return str(e)

if __name__ == "__main__":
    reporter = InstitutionalReporter()
    print(reporter.generate_daily_summary())
