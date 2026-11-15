from autotrader.risk.rules import RiskRules


def _base_rules() -> RiskRules:
    return RiskRules(
        max_position_per_symbol=10,
        max_daily_loss=100000,
        max_order_amount=500000,
        no_trade_minutes_after_open=0,
    )


def test_insufficient_cash():
    rules = _base_rules()
    ok, reason = rules.check_order(
        signal={"symbol": "005930", "side": "buy", "qty": 10},
        account={"cash": 1000},
        positions=[],
        current_price=1000,
    )
    assert not ok
    assert "현금" in reason


def test_order_amount_exceeded():
    rules = _base_rules()
    ok, reason = rules.check_order(
        signal={"symbol": "005930", "side": "buy", "qty": 100},
        account={"cash": 100000000},
        positions=[],
        current_price=10000,
    )
    assert not ok
    assert "max_order_amount" in reason


def test_normal_order_allowed():
    rules = _base_rules()
    ok, reason = rules.check_order(
        signal={"symbol": "005930", "side": "buy", "qty": 1},
        account={"cash": 1000000},
        positions=[],
        current_price=70000,
    )
    assert ok
    assert reason == "OK"
