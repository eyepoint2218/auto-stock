"""이동평균 교차 전략."""

from __future__ import annotations

from strategy.base import Strategy


def simple_moving_average(values: list[float], period: int) -> list[float]:
    """단순 이동평균 배열을 반환한다."""
    if period <= 0:
        raise ValueError("period는 1 이상이어야 합니다.")
    if len(values) < period:
        return []

    result: list[float] = []
    window_sum = sum(values[:period])
    result.append(window_sum / period)

    for i in range(period, len(values)):
        window_sum += values[i] - values[i - period]
        result.append(window_sum / period)
    return result


class MovingAverageCrossStrategy(Strategy):
    """단기/장기 이동평균 교차 전략."""

    def __init__(self, short_period: int = 5, long_period: int = 20, order_qty: int = 1) -> None:
        if short_period <= 0 or long_period <= 0:
            raise ValueError("이동평균 기간은 1 이상이어야 합니다.")
        if short_period >= long_period:
            raise ValueError("long_period는 short_period보다 커야 합니다.")
        if order_qty <= 0:
            raise ValueError("order_qty는 1 이상이어야 합니다.")
        self.short_period = short_period
        self.long_period = long_period
        self.order_qty = order_qty

    def generate_signal(
        self,
        symbol: str,
        candles: list[dict],
        account: dict,
        positions: list[dict],
    ) -> dict | None:
        closes = [float(c["close"]) for c in candles if "close" in c]
        required = self.long_period + 1
        if len(closes) < required:
            return None

        short_ma = simple_moving_average(closes, self.short_period)
        long_ma = simple_moving_average(closes, self.long_period)

        if len(short_ma) < 2 or len(long_ma) < 2:
            return None

        prev_short, curr_short = short_ma[-2], short_ma[-1]
        prev_long, curr_long = long_ma[-2], long_ma[-1]

        if prev_short <= prev_long and curr_short > curr_long:
            return {
                "symbol": symbol,
                "side": "buy",
                "qty": self.order_qty,
                "reason": "short_ma crossed above long_ma",
            }

        if prev_short >= prev_long and curr_short < curr_long:
            # 보유 수량이 있으면 해당 수량만큼 매도, 없으면 기본 수량
            current_qty = 0
            for pos in positions:
                if pos.get("symbol") == symbol:
                    current_qty = int(pos.get("qty", 0))
                    break
            qty = current_qty if current_qty > 0 else self.order_qty
            return {
                "symbol": symbol,
                "side": "sell",
                "qty": qty,
                "reason": "short_ma crossed below long_ma",
            }

        return None
