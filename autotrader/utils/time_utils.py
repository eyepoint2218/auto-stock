"""시간 관련 유틸 (Asia/Seoul 기준)."""

from __future__ import annotations

from datetime import datetime, time
from zoneinfo import ZoneInfo

SEOUL_TZ = ZoneInfo("Asia/Seoul")


def seoul_now() -> datetime:
    """서울 현재 시각을 반환한다."""
    return datetime.now(tz=SEOUL_TZ)


def market_open_time() -> time:
    """한국 주식시장 정규장 시작 시각."""
    return time(hour=9, minute=0)


def market_close_time() -> time:
    """한국 주식시장 정규장 종료 시각."""
    return time(hour=15, minute=30)


def is_market_open(now: datetime | None = None) -> bool:
    """정규장 시간 여부를 반환한다."""
    current = now.astimezone(SEOUL_TZ) if now else seoul_now()
    t = current.time()
    return market_open_time() <= t <= market_close_time()


def is_within_minutes_after_market_open(minutes: int, now: datetime | None = None) -> bool:
    """장 시작 후 N분 이내인지 판별한다."""
    if minutes <= 0:
        return False
    current = now.astimezone(SEOUL_TZ) if now else seoul_now()
    opened = current.replace(
        hour=market_open_time().hour,
        minute=market_open_time().minute,
        second=0,
        microsecond=0,
    )
    delta = (current - opened).total_seconds()
    return 0 <= delta <= minutes * 60
