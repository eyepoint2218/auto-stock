"""환경변수 기반 설정 로더."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv



def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


def parse_int(value: str | None, default: int) -> int:
    if value is None or value == "":
        return default
    return int(value)


def parse_float(value: str | None, default: float) -> float:
    if value is None or value == "":
        return default
    return float(value)


def parse_list(value: str | None, default: list[str] | None = None) -> list[str]:
    if value is None or value.strip() == "":
        return default or []
    return [v.strip() for v in value.split(",") if v.strip()]


@dataclass
class Settings:
    APP_ENV: str
    BROKER_TYPE: str
    ENABLE_LIVE_TRADING: bool
    DRY_RUN: bool
    DB_PATH: str
    LOG_LEVEL: str
    KIS_APP_KEY: str
    KIS_APP_SECRET: str
    KIS_ACCOUNT_NO: str
    KIS_PRODUCT_CODE: str
    KIS_BASE_URL: str
    KIS_IS_PAPER_TRADING: bool
    TRADE_SYMBOLS: list[str]
    LOOP_INTERVAL_SECONDS: int
    SHORT_MA: int
    LONG_MA: int
    MAX_POSITION_PER_SYMBOL: int
    MAX_DAILY_LOSS: float
    MAX_ORDER_AMOUNT: float
    NO_TRADE_MINUTES_AFTER_OPEN: int
    STOP_LOSS_PCT: float
    TAKE_PROFIT_PCT: float

    @classmethod
    def load(cls) -> "Settings":
        load_dotenv()
        settings = cls(
            APP_ENV=os.getenv("APP_ENV", "dev"),
            BROKER_TYPE=os.getenv("BROKER_TYPE", "mock"),
            ENABLE_LIVE_TRADING=parse_bool(os.getenv("ENABLE_LIVE_TRADING"), False),
            DRY_RUN=parse_bool(os.getenv("DRY_RUN"), True),
            DB_PATH=os.getenv("DB_PATH", "autotrader.db"),
            LOG_LEVEL=os.getenv("LOG_LEVEL", "INFO"),
            KIS_APP_KEY=os.getenv("KIS_APP_KEY", ""),
            KIS_APP_SECRET=os.getenv("KIS_APP_SECRET", ""),
            KIS_ACCOUNT_NO=os.getenv("KIS_ACCOUNT_NO", ""),
            KIS_PRODUCT_CODE=os.getenv("KIS_PRODUCT_CODE", "01"),
            KIS_BASE_URL=os.getenv("KIS_BASE_URL", ""),
            KIS_IS_PAPER_TRADING=parse_bool(os.getenv("KIS_IS_PAPER_TRADING"), True),
            TRADE_SYMBOLS=parse_list(os.getenv("TRADE_SYMBOLS"), ["005930", "000660"]),
            LOOP_INTERVAL_SECONDS=parse_int(os.getenv("LOOP_INTERVAL_SECONDS"), 60),
            SHORT_MA=parse_int(os.getenv("SHORT_MA"), 5),
            LONG_MA=parse_int(os.getenv("LONG_MA"), 20),
            MAX_POSITION_PER_SYMBOL=parse_int(os.getenv("MAX_POSITION_PER_SYMBOL"), 10),
            MAX_DAILY_LOSS=parse_float(os.getenv("MAX_DAILY_LOSS"), 100000.0),
            MAX_ORDER_AMOUNT=parse_float(os.getenv("MAX_ORDER_AMOUNT"), 500000.0),
            NO_TRADE_MINUTES_AFTER_OPEN=parse_int(os.getenv("NO_TRADE_MINUTES_AFTER_OPEN"), 5),
            STOP_LOSS_PCT=parse_float(os.getenv("STOP_LOSS_PCT"), 0.03),
            TAKE_PROFIT_PCT=parse_float(os.getenv("TAKE_PROFIT_PCT"), 0.05),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.LONG_MA <= self.SHORT_MA:
            raise ValueError("LONG_MA는 SHORT_MA보다 커야 합니다.")
        if not self.TRADE_SYMBOLS:
            raise ValueError("TRADE_SYMBOLS는 최소 1개 이상이어야 합니다.")
        if self.BROKER_TYPE not in {"mock", "korea_investment"}:
            raise ValueError("BROKER_TYPE은 mock 또는 korea_investment 이어야 합니다.")
