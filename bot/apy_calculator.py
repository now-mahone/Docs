# Created: 2026-01-19
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List


@dataclass
class PeriodReturn:
    timestamp: float
    delta_t_days: float
    r_k: float


class APYCalculator:
    @staticmethod
    def calculate_period_return(
        funding_pnl: float,
        staking_pnl: float,
        spread_pnl: float,
        total_costs: float,
        prior_nav: float,
    ) -> float:
        if prior_nav <= 0:
            return 0.0
        return (funding_pnl + staking_pnl + spread_pnl - total_costs) / prior_nav

    @staticmethod
    def calculate_realized_apy(periods: List[PeriodReturn]) -> float:
        if not periods:
            return 0.0

        total_time_days = sum(period.delta_t_days for period in periods)
        if total_time_days <= 0:
            return 0.0

        log_return_sum = 0.0
        for period in periods:
            if period.r_k <= -1:
                continue
            log_return_sum += math.log(1 + period.r_k)

        annualized_log_return = (365 / total_time_days) * log_return_sum
        return math.exp(annualized_log_return) - 1

    @staticmethod
    def calculate_expected_apy(
        leverage: float,
        funding_rate: float,
        staking_yield: float,
        spread_edge: float,
        turnover_rate: float,
        cost_rate: float,
    ) -> float:
        annual_funding = funding_rate * 3 * 365
        expected_log_return = (
            leverage * annual_funding
            + leverage * staking_yield
            + turnover_rate * spread_edge
            - cost_rate
        )
        return math.exp(expected_log_return) - 1
