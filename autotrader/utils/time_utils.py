"""시간 유틸 (Asia/Seoul 기준)."""

from __future__ import annotations

from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

KST = ZoneInfo("Asia/Seoul")
MARKET_OPEN = time(hour=9, minute=0)
MARKET_CLOSE = time(hour=15, minute=30)


def now_kst() -> datetime:
    """현재 KST 시각 반환."""
    return datetime.now(tz=KST)


def is_market_open(now: datetime | None = None) -> bool:
    """한국 장 운영 시간 여부."""
    now = now or now_kst()
    t = now.timetz().replace(tzinfo=None)
    return MARKET_OPEN <= t <= MARKET_CLOSE


def minutes_after_market_open(now: datetime | None = None) -> int:
    """장 시작 후 경과 분 (음수 가능)."""
    now = now or now_kst()
    market_open_dt = datetime.combine(now.date(), MARKET_OPEN, tzinfo=KST)
    delta: timedelta = now - market_open_dt
    return int(delta.total_seconds() // 60)


def is_within_no_trade_window(minutes: int, now: datetime | None = None) -> bool:
    """장 시작 후 N분 이내 매매 금지 여부."""
    if minutes <= 0:
        return False
    if not is_market_open(now):
        return False
    return minutes_after_market_open(now) < minutes
