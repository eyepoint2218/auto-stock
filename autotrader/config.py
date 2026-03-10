"""환경설정 로더."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


def _parse_bool(v: str, default: bool = False) -> bool:
    if v is None:
        return default
    return v.strip().lower() in {"1", "true", "yes", "y", "on"}


def _parse_int(v: str, default: int) -> int:
    return int(v) if v is not None and v != "" else default


def _parse_float(v: str, default: float) -> float:
    return float(v) if v is not None and v != "" else default


def _parse_list(v: str, default: list[str] | None = None) -> list[str]:
    if not v:
        return default or []
    return [x.strip() for x in v.split(",") if x.strip()]


@dataclass
class Settings:
    APP_ENV: str
    BROKER_TYPE: str
    ENABLE_LIVE_TRADING: bool
    DRY_RUN: bool
    MIRAE_ACCOUNT_NO: str
    MIRAE_APP_KEY: str
    MIRAE_APP_SECRET: str
    TRADE_SYMBOLS: list[str]
    LOOP_INTERVAL_SECONDS: int
    SHORT_MA: int
    LONG_MA: int
    MAX_POSITION_PER_SYMBOL: int
    MAX_DAILY_LOSS: int
    MAX_ORDER_AMOUNT: int
    NO_TRADE_MINUTES_AFTER_OPEN: int
    STOP_LOSS_PCT: float
    TAKE_PROFIT_PCT: float

    def validate(self) -> None:
        if self.BROKER_TYPE not in {"mock", "mirae"}:
            raise ValueError("BROKER_TYPE은 mock 또는 mirae만 가능합니다.")
        if self.SHORT_MA <= 0 or self.LONG_MA <= 0:
            raise ValueError("SHORT_MA, LONG_MA는 1 이상이어야 합니다.")
        if self.SHORT_MA >= self.LONG_MA:
            raise ValueError("SHORT_MA는 LONG_MA보다 작아야 합니다.")
        if not self.TRADE_SYMBOLS:
            raise ValueError("TRADE_SYMBOLS는 최소 1개 이상 필요합니다.")
        if self.BROKER_TYPE == "mirae":
            if not self.MIRAE_ACCOUNT_NO:
                raise ValueError("MIRAE_ACCOUNT_NO가 비어 있습니다.")
            if not self.MIRAE_APP_KEY:
                raise ValueError("MIRAE_APP_KEY가 비어 있습니다.")
            if not self.MIRAE_APP_SECRET:
                raise ValueError("MIRAE_APP_SECRET가 비어 있습니다.")


def load_settings() -> Settings:
    """.env에서 설정 로드 후 검증."""
    load_dotenv()
    settings = Settings(
        APP_ENV=os.getenv("APP_ENV", "dev"),
        BROKER_TYPE=os.getenv("BROKER_TYPE", "mock"),
        ENABLE_LIVE_TRADING=_parse_bool(os.getenv("ENABLE_LIVE_TRADING", "false"), False),
        DRY_RUN=_parse_bool(os.getenv("DRY_RUN", "true"), True),
        MIRAE_ACCOUNT_NO=os.getenv("MIRAE_ACCOUNT_NO", ""),
        MIRAE_APP_KEY=os.getenv("MIRAE_APP_KEY", ""),
        MIRAE_APP_SECRET=os.getenv("MIRAE_APP_SECRET", ""),
        TRADE_SYMBOLS=_parse_list(os.getenv("TRADE_SYMBOLS", "005930,000660")),
        LOOP_INTERVAL_SECONDS=_parse_int(os.getenv("LOOP_INTERVAL_SECONDS"), 60),
        SHORT_MA=_parse_int(os.getenv("SHORT_MA"), 5),
        LONG_MA=_parse_int(os.getenv("LONG_MA"), 20),
        MAX_POSITION_PER_SYMBOL=_parse_int(os.getenv("MAX_POSITION_PER_SYMBOL"), 10),
        MAX_DAILY_LOSS=_parse_int(os.getenv("MAX_DAILY_LOSS"), 100000),
        MAX_ORDER_AMOUNT=_parse_int(os.getenv("MAX_ORDER_AMOUNT"), 500000),
        NO_TRADE_MINUTES_AFTER_OPEN=_parse_int(os.getenv("NO_TRADE_MINUTES_AFTER_OPEN"), 5),
        STOP_LOSS_PCT=_parse_float(os.getenv("STOP_LOSS_PCT"), 0.03),
        TAKE_PROFIT_PCT=_parse_float(os.getenv("TAKE_PROFIT_PCT"), 0.05),
    )
    settings.validate()
    return settings
