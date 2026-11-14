from risk.rules import RiskRules


def test_reject_insufficient_cash() -> None:
    rules = RiskRules(max_order_amount=1_000_000, no_trade_minutes_after_open=0)
    signal = {"symbol": "005930", "side": "buy", "qty": 10}

    ok, reason = rules.check_order(signal, account={"cash": 1000}, positions=[], current_price=1000)
    assert ok is False
    assert "현금" in reason


def test_reject_order_amount_exceeded() -> None:
    rules = RiskRules(max_order_amount=5_000, no_trade_minutes_after_open=0)
    signal = {"symbol": "005930", "side": "buy", "qty": 10}

    ok, reason = rules.check_order(signal, account={"cash": 1_000_000}, positions=[], current_price=1000)
    assert ok is False
    assert "한도" in reason


def test_allow_normal_order() -> None:
    rules = RiskRules(max_order_amount=1_000_000, no_trade_minutes_after_open=0)
    signal = {"symbol": "005930", "side": "buy", "qty": 1}

    ok, reason = rules.check_order(signal, account={"cash": 1_000_000}, positions=[], current_price=70000)
    assert ok is True
    assert reason == "허용"
