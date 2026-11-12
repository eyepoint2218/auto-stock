from autotrader.strategy.moving_average_cross import (
    MovingAverageCrossStrategy,
    detect_cross,
    moving_average,
)


def _candles_from_closes(closes: list[int]) -> list[dict]:
    return [
        {
            "open": c,
            "high": c,
            "low": c,
            "close": c,
            "volume": 100,
            "timestamp": str(i),
        }
        for i, c in enumerate(closes)
    ]


def test_moving_average():
    assert moving_average([1, 2, 3, 4, 5], 3) == 4


def test_golden_cross_buy_signal():
    closes = [13, 16, 12, 9, 12, 17]
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=5, default_qty=1)
    signal = strategy.generate_signal("005930", _candles_from_closes(closes), {"cash": 1000000}, [])
    assert signal is not None
    assert signal["side"] == "buy"


def test_dead_cross_sell_signal():
    closes = [6, 10, 3, 13, 2, 1]
    strategy = MovingAverageCrossStrategy(short_window=2, long_window=5, default_qty=1)
    signal = strategy.generate_signal(
        "005930", _candles_from_closes(closes), {"cash": 1000000}, [{"symbol": "005930", "qty": 1}]
    )
    assert signal is not None
    assert signal["side"] == "sell"


def test_not_enough_data_returns_none():
    assert detect_cross([1, 2, 3], short_window=2, long_window=5) is None
