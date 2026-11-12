"""이동평균 크로스 전략."""

from __future__ import annotations

from .base import Strategy


def moving_average(values: list[float], window: int) -> float:
    """단순 이동평균 계산."""
    if window <= 0:
        raise ValueError("window는 1 이상이어야 합니다.")
    if len(values) < window:
        raise ValueError("이동평균 계산에 필요한 데이터가 부족합니다.")
    subset = values[-window:]
    return sum(subset) / window


def detect_cross(closes: list[float], short_window: int, long_window: int) -> str | None:
    """최근 2개 구간의 이동평균으로 골든/데드 크로스를 판정한다."""
    min_len = max(short_window, long_window) + 1
    if len(closes) < min_len:
        return None

    prev_closes = closes[:-1]
    curr_closes = closes

    prev_short = moving_average(prev_closes, short_window)
    prev_long = moving_average(prev_closes, long_window)
    curr_short = moving_average(curr_closes, short_window)
    curr_long = moving_average(curr_closes, long_window)

    if prev_short <= prev_long and curr_short > curr_long:
        return "golden"
    if prev_short >= prev_long and curr_short < curr_long:
        return "dead"
    return None


class MovingAverageCrossStrategy(Strategy):
    """단기/장기 이동평균 크로스 전략."""

    def __init__(self, short_window: int = 5, long_window: int = 20, default_qty: int = 1) -> None:
        if short_window >= long_window:
            raise ValueError("short_window는 long_window보다 작아야 합니다.")
        self.short_window = short_window
        self.long_window = long_window
        self.default_qty = default_qty

    def generate_signal(
        self,
        symbol: str,
        candles: list[dict],
        account: dict,
        positions: list[dict],
    ) -> dict | None:
        _ = account, positions
        closes = [float(c["close"]) for c in candles if "close" in c]
        cross = detect_cross(closes, self.short_window, self.long_window)
        if cross is None:
            return None

        if cross == "golden":
            return {
                "symbol": symbol,
                "side": "buy",
                "qty": self.default_qty,
                "reason": "short_ma crossed above long_ma",
            }
        return {
            "symbol": symbol,
            "side": "sell",
            "qty": self.default_qty,
            "reason": "short_ma crossed below long_ma",
        }
