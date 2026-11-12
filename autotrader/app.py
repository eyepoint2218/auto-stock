"""애플리케이션 조립 모듈."""

from __future__ import annotations

from autotrader.broker.mirae_asset import MiraeAssetBroker
from autotrader.broker.mock_broker import MockBroker
from autotrader.config import Settings
from autotrader.engine.trader import Trader
from autotrader.risk.rules import RiskRules
from autotrader.storage.db import Database
from autotrader.strategy.moving_average_cross import MovingAverageCrossStrategy
from autotrader.utils.logger import init_logger


def create_app(settings: Settings) -> Trader:
    """설정 기반으로 트레이딩 엔진을 생성한다."""
    logger = init_logger()
    db = Database("data/autotrader.db")

    if settings.BROKER_TYPE == "mock":
        broker = MockBroker()
        for symbol in settings.TRADE_SYMBOLS:
            broker.set_price(symbol, 70000)
            # 단순 예시 캔들 주입
            candles = [
                {
                    "open": 70000,
                    "high": 70500,
                    "low": 69500,
                    "close": 70000 + i,
                    "volume": 10000 + i,
                    "timestamp": f"t{i}",
                }
                for i in range(60)
            ]
            broker.set_ohlcv(symbol, candles)
    else:
        broker = MiraeAssetBroker(
            app_key=settings.MIRAE_APP_KEY,
            app_secret=settings.MIRAE_APP_SECRET,
            account_no=settings.MIRAE_ACCOUNT_NO,
            enable_live_trading=settings.ENABLE_LIVE_TRADING,
        )

    strategy = MovingAverageCrossStrategy(
        short_window=settings.SHORT_MA,
        long_window=settings.LONG_MA,
        default_qty=1,
    )
    risk_rules = RiskRules(
        max_position_per_symbol=settings.MAX_POSITION_PER_SYMBOL,
        max_daily_loss=settings.MAX_DAILY_LOSS,
        max_order_amount=settings.MAX_ORDER_AMOUNT,
        no_trade_minutes_after_open=settings.NO_TRADE_MINUTES_AFTER_OPEN,
        stop_loss_pct=settings.STOP_LOSS_PCT,
        take_profit_pct=settings.TAKE_PROFIT_PCT,
    )

    return Trader(
        broker=broker,
        strategy=strategy,
        risk_rules=risk_rules,
        db=db,
        logger=logger,
        symbols=settings.TRADE_SYMBOLS,
        dry_run=settings.DRY_RUN,
    )
