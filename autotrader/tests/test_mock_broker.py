from autotrader.broker.mock_broker import MockBroker


def test_buy_order_updates_balance_and_position():
    broker = MockBroker(initial_cash=100000)
    broker.set_price("005930", 10000)
    result = broker.place_order("005930", "buy", 2)

    assert result["status"] == "filled"
    assert broker.get_balance()["cash"] == 80000
    positions = broker.get_positions()
    assert positions[0]["symbol"] == "005930"
    assert positions[0]["qty"] == 2


def test_sell_order_updates_balance_and_position():
    broker = MockBroker(initial_cash=100000)
    broker.set_price("005930", 10000)
    broker.place_order("005930", "buy", 2)
    broker.place_order("005930", "sell", 1)

    assert broker.get_balance()["cash"] == 90000
    positions = broker.get_positions()
    assert positions[0]["qty"] == 1


def test_get_order_status():
    broker = MockBroker(initial_cash=100000)
    broker.set_price("005930", 10000)
    order = broker.place_order("005930", "buy", 1)
    status = broker.get_order_status(order["order_id"])
    assert status["order_id"] == order["order_id"]
