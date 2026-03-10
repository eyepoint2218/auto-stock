from broker.mock_broker import MockBroker


def test_buy_order_updates_balance_and_position() -> None:
    broker = MockBroker(initial_cash=1_000_000)
    broker.set_price("005930", 10000)

    order = broker.place_order(symbol="005930", side="buy", qty=10)
    assert order["status"] == "filled"

    balance = broker.get_balance()
    assert balance["cash"] == 900000

    positions = broker.get_positions()
    assert positions[0]["symbol"] == "005930"
    assert positions[0]["qty"] == 10


def test_sell_order_updates_balance_and_position() -> None:
    broker = MockBroker(initial_cash=1_000_000)
    broker.set_price("005930", 10000)
    broker.place_order(symbol="005930", side="buy", qty=10)
    broker.set_price("005930", 11000)

    order = broker.place_order(symbol="005930", side="sell", qty=4)
    assert order["status"] == "filled"

    balance = broker.get_balance()
    assert balance["cash"] == 944000

    positions = broker.get_positions()
    assert positions[0]["qty"] == 6


def test_get_order_status() -> None:
    broker = MockBroker(initial_cash=1_000_000)
    broker.set_price("005930", 10000)
    order = broker.place_order(symbol="005930", side="buy", qty=1)

    status = broker.get_order_status(order["order_id"])
    assert status["order_id"] == order["order_id"]
    assert status["status"] == "filled"
