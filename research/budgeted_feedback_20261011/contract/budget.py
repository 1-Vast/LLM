"""Common resource cap for measurements, round trips and declared other costs."""
from dataclasses import dataclass
from math import isfinite


def _nonnegative(value: float) -> bool:
    return (not isinstance(value, bool) and isinstance(value, (int, float))
            and isfinite(value) and value >= 0)


@dataclass(frozen=True)
class CampaignBudget:
    """Resource units are separate from terminal-utility prices.

    Use one instance for every compared arm. Other costs include declared API,
    compute or assay overhead in the same resource unit; zero must be justified
    by the experiment. This arithmetic does not authenticate laboratory prices.
    """

    total: float
    measurement_cost: float
    turnaround_cost: float
    unit: str

    def __post_init__(self) -> None:
        if not all(_nonnegative(v) for v in (self.total, self.measurement_cost, self.turnaround_cost)):
            raise ValueError("resource budget and costs must be finite and nonnegative")
        if not isinstance(self.unit, str) or not self.unit.strip():
            raise ValueError("resource unit must be named")

    def cost(self, measurements: int, turnarounds: int, *, other_cost: float = 0.0) -> float:
        if any(type(v) is not int or v < 0 for v in (measurements, turnarounds)):
            raise ValueError("resource counts must be nonnegative integers")
        if not _nonnegative(other_cost):
            raise ValueError("other resource cost must be finite and nonnegative")
        value = measurements * self.measurement_cost + turnarounds * self.turnaround_cost + other_cost
        if not isfinite(value):
            raise ValueError("total resource cost must be finite")
        return value

    def require_feasible(self, measurements: int, turnarounds: int, *, other_cost: float = 0.0) -> float:
        """Check cumulative expenditure, including a proposed purchase, before execution."""
        value = self.cost(measurements, turnarounds, other_cost=other_cost)
        if value > self.total and not abs(value - self.total) <= 1e-12 * max(1.0, self.total):
            raise ValueError("campaign exceeds total resource budget")
        return value
