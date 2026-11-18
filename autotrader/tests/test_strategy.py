from strategy.moving_average_cross import MovingAverageCrossStrategy, simple_moving_average


def test_simple_moving_average_basic() -> None:
    values = [1, 2, 3, 4, 5]
    assert simple_moving_average(values, 3) == [2.0, 3.0, 4.0]


def test_golden_cross_signal() -> None:
    strategy = MovingAverageCrossStrategy(short_period=3, long_period=5, order_qty=1)
    closes = [10, 10, 10, 10, 10, 9, 8, 12, 13]
    candles = [{"close": c} for c in closes]

    signal = strategy.generate_signal("005930", candles, account={"cash": 1_000_000}, positions=[])
    assert signal is not None
    assert signal["side"] == "buy"


def test_dead_cross_signal() -> None:
    strategy = MovingAverageCrossStrategy(short_period=3, long_period=5, order_qty=1)
    closes = [10, 10, 10, 10, 10, 11, 12, 9, 8]
    candles = [{"close": c} for c in closes]
    positions = [{"symbol": "005930", "qty": 2}]

    signal = strategy.generate_signal("005930", candles, account={"cash": 1_000_000}, positions=positions)
    assert signal is not None
    assert signal["side"] == "sell"
    assert signal["qty"] == 2


def test_not_enough_data_returns_none() -> None:
    strategy = MovingAverageCrossStrategy(short_period=5, long_period=20, order_qty=1)
    candles = [{"close": 100}] * 10

    signal = strategy.generate_signal("005930", candles, account={"cash": 1_000_000}, positions=[])
    assert signal is None
