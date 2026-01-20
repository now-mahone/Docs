# Created: 2026-01-19
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from loguru import logger


@dataclass
class ProfitRecord:
    timestamp: float
    venue: str
    order_id: str
    token_in: str
    token_out: str
    amount_out: float
    profit_bps: float
    gas_used: float
    tx_hash: str
    status: str


@dataclass
class DailySummary:
    date: str
    total_trades: int
    successful_trades: int
    win_rate: float
    total_profit_bps: float
    total_gas_used: float
    venues: Dict[str, int]


class DailyProfitReporter:
    def __init__(
        self,
        solver_log_path: str = "bot/solver/profit_log.csv",
        zin_log_path: str = "bot/solver/zin_profit_log.csv",
        output_dir: str = "docs/reports/solver",
    ) -> None:
        self.solver_log_path = Path(solver_log_path)
        self.zin_log_path = Path(zin_log_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _load_csv_rows(self, path: Path) -> List[Dict[str, str]]:
        if not path.exists():
            return []
        with path.open("r", newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)
            return list(reader)

    def _normalize_records(self) -> List[ProfitRecord]:
        records: List[ProfitRecord] = []

        for row in self._load_csv_rows(self.solver_log_path):
            records.append(
                ProfitRecord(
                    timestamp=float(row.get("timestamp", 0.0)),
                    venue=row.get("venue", "unknown"),
                    order_id=row.get("order_id", "unknown"),
                    token_in=row.get("coin", "unknown"),
                    token_out=row.get("coin", "unknown"),
                    amount_out=float(row.get("amount", 0.0)),
                    profit_bps=float(row.get("profit_bps", 0.0)),
                    gas_used=0.0,
                    tx_hash="",
                    status=row.get("status", "unknown"),
                )
            )

        for row in self._load_csv_rows(self.zin_log_path):
            records.append(
                ProfitRecord(
                    timestamp=float(row.get("timestamp", 0.0)),
                    venue=row.get("venue", "zin"),
                    order_id=row.get("order_id", "unknown"),
                    token_in=row.get("token_in", "unknown"),
                    token_out=row.get("token_out", "unknown"),
                    amount_out=float(row.get("amount_out", 0.0)),
                    profit_bps=float(row.get("profit_bps", 0.0)),
                    gas_used=float(row.get("gas_used", 0.0)),
                    tx_hash=row.get("tx_hash", ""),
                    status=row.get("status", "unknown"),
                )
            )

        return records

    def _filter_by_date(self, records: List[ProfitRecord], date_str: str) -> List[ProfitRecord]:
        filtered: List[ProfitRecord] = []
        for record in records:
            record_date = datetime.fromtimestamp(record.timestamp, tz=timezone.utc).strftime("%Y-%m-%d")
            if record_date == date_str:
                filtered.append(record)
        return filtered

    def _aggregate(self, records: List[ProfitRecord], date_str: str) -> Optional[DailySummary]:
        if not records:
            return None

        total_trades = len(records)
        successful_trades = len([record for record in records if record.status.upper() in {"HEDGED", "FILLED", "SUCCESS"}])
        win_rate = successful_trades / total_trades if total_trades else 0.0
        total_profit_bps = sum(record.profit_bps for record in records if record.status.upper() in {"HEDGED", "FILLED", "SUCCESS"})
        total_gas_used = sum(record.gas_used for record in records)

        venues: Dict[str, int] = {}
        for record in records:
            venues[record.venue] = venues.get(record.venue, 0) + 1

        return DailySummary(
            date=date_str,
            total_trades=total_trades,
            successful_trades=successful_trades,
            win_rate=win_rate,
            total_profit_bps=total_profit_bps,
            total_gas_used=total_gas_used,
            venues=venues,
        )

    def generate_daily_report(self, date_str: Optional[str] = None) -> Optional[DailySummary]:
        target_date = date_str or datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
        records = self._normalize_records()
        daily_records = self._filter_by_date(records, target_date)
        summary = self._aggregate(daily_records, target_date)

        if summary is None:
            logger.warning("No profit records found for {date}", date=target_date)
            return None

        output_path = self.output_dir / f"daily_profit_{target_date}.json"
        with output_path.open("w", encoding="utf-8") as file:
            json.dump(summary.__dict__, file, indent=2)

        logger.success("Daily profit report generated: {path}", path=output_path)
        return summary


if __name__ == "__main__":
    reporter = DailyProfitReporter()
    reporter.generate_daily_report()
