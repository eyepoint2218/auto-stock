"""전략 패키지."""

from strategy.base import Strategy
from strategy.moving_average_cross import MovingAverageCrossStrategy

__all__ = ["Strategy", "MovingAverageCrossStrategy"]
