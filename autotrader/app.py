"""애플리케이션 조립 로직."""

from __future__ import annotations

from broker.koreainvestment import KoreaInvestmentBroker
from broker.mock_broker import MockBroker
from config import Settings
from engine.trader import Trader
from risk.rules import RiskRules
from storage.db import SQLiteStorage
from strategy.moving_average_cross import MovingAverageCrossStrategy
from utils.logger import get_logger


def build_trader(settings: Settings) -> Trader:
    """설정 기반으로 Trader를 생성한다."""
    logger = get_logger(level=settings.LOG_LEVEL)

    db = SQLiteStorage(settings.DB_PATH)
    db.init_db()

    if settings.BROKER_TYPE == "mock":
        broker = MockBroker()
        # 개발 편의를 위한 기본 Mock 데이터
        for symbol in settings.TRADE_SYMBOLS:
            broker.set_price(symbol, 70000)
            candles = [
                {
                    "date": f"202401{i:02d}",
                    "open": 69000 + i,
                    "high": 71000 + i,
                    "low": 68000 + i,
                    "close": 69000 + i,
                    "volume": 100000 + i,
                }
                for i in range(1, 80)
            ]
            broker.set_ohlcv(symbol, candles)
    else:
        broker = KoreaInvestmentBroker(
            app_key=settings.KIS_APP_KEY,
            app_secret=settings.KIS_APP_SECRET,
            account_no=settings.KIS_ACCOUNT_NO,
            product_code=settings.KIS_PRODUCT_CODE,
            base_url=settings.KIS_BASE_URL,
            enable_live_trading=settings.ENABLE_LIVE_TRADING,
            is_paper_trading=settings.KIS_IS_PAPER_TRADING,
        )

    strategy = MovingAverageCrossStrategy(
        short_period=settings.SHORT_MA,
        long_period=settings.LONG_MA,
        order_qty=1,
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
        dry_run=settings.DRY_RUN,
        symbols=settings.TRADE_SYMBOLS,
    )
