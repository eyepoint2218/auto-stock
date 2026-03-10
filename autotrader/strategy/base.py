"""전략 인터페이스."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Strategy(ABC):
    """매매 전략 추상 클래스."""

    @abstractmethod
    def generate_signal(
        self,
        symbol: str,
        candles: list[dict],
        account: dict,
        positions: list[dict],
    ) -> dict | None:
        """매매 신호를 생성한다."""
