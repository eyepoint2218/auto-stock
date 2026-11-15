"""전략 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Strategy(ABC):
    """신호 생성 전략 추상 클래스."""

    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        candles: list[dict],
        account: dict,
        positions: list[dict],
    ) -> dict | None:
        """매수/매도 신호를 생성한다."""
