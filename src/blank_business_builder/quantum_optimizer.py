"""Quantum-inspired optimizer to rank business ideas."""

from __future__ import annotations

from dataclasses import dataclass
from math import sqrt
from typing import Iterable, List, Sequence

from .business_data import BusinessIdea


@dataclass
class OptimizationResult:
    idea: BusinessIdea
    three_month_profit: float
    monthly_average: float
    success_probability: float
    meets_floor: bool
    meets_target: bool


class QuantumOptimizer:
    """Score business ideas using a quantum-inspired probability model."""

    def __init__(self, monthly_floor: float = 4500.0, quarter_target: float = 20000.0) -> None:
        self.monthly_floor = monthly_floor
        self.quarter_target = quarter_target

    def project_profit(self, idea: BusinessIdea, months: int = 3) -> float:
        """Project cumulative profit over the given number of months.

        We assume revenue ramps linearly over the ramp-up period until full output.
        """

        effective_months = 0.0
        for month in range(1, months + 1):
            if month <= idea.ramp_up_months:
                ramp_ratio = month / max(1, idea.ramp_up_months)
            else:
                ramp_ratio = 1.0
            effective_months += ramp_ratio
        profit_per_full_month = idea.monthly_profit
        return max(0.0, profit_per_full_month * effective_months - idea.startup_cost)

    def _amplitudes(self, profits: Sequence[float]) -> List[float]:
        clipped = [max(0.0, p) for p in profits]
        total = sum(clipped)
        if total == 0:
            # fallback to uniform amplitudes
            return [1.0 / sqrt(len(profits)) for _ in profits]
        amplitudes = [sqrt(p / total) for p in clipped]
        norm = sqrt(sum(a * a for a in amplitudes))
        if norm == 0:
            return [1.0 / sqrt(len(profits)) for _ in profits]
        return [a / norm for a in amplitudes]

    def evaluate(self, ideas: Iterable[BusinessIdea], months: int = 3) -> List[OptimizationResult]:
        ideas_list = list(ideas)
        if not ideas_list:
            return []
        profits = [self.project_profit(idea, months=months) for idea in ideas_list]
        amplitudes = self._amplitudes(profits)
        results: List[OptimizationResult] = []
        for idea, profit, amplitude in zip(ideas_list, profits, amplitudes):
            monthly_average = profit / months if months else 0.0
            success_probability = round(amplitude ** 2, 4)
            meets_floor = monthly_average >= self.monthly_floor
            meets_target = profit >= self.quarter_target
            results.append(
                OptimizationResult(
                    idea=idea,
                    three_month_profit=round(profit, 2),
                    monthly_average=round(monthly_average, 2),
                    success_probability=success_probability,
                    meets_floor=meets_floor,
                    meets_target=meets_target,
                )
            )
        results.sort(key=lambda r: (r.success_probability, r.three_month_profit), reverse=True)
        return results
