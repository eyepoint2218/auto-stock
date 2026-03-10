"""브로커 인터페이스 정의."""

from __future__ import annotations

from abc import ABC, abstractmethod


class Broker(ABC):
    """브로커 추상 클래스.

    실제 브로커 구현체는 아래 메서드를 모두 제공해야 한다.
    """

    @abstractmethod
    def authenticate(self) -> None:
        """인증/세션 초기화를 수행한다."""

    @abstractmethod
    def get_price(self, symbol: str) -> dict:
        """현재가를 조회한다."""

    @abstractmethod
    def get_ohlcv(self, symbol: str, limit: int = 100) -> list[dict]:
        """OHLCV 캔들 데이터를 조회한다."""

    @abstractmethod
    def get_balance(self) -> dict:
        """계좌 잔고 정보를 반환한다."""

    @abstractmethod
    def get_positions(self) -> list[dict]:
        """보유 포지션 목록을 반환한다."""

    @abstractmethod
    def place_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int | None = None,
        order_type: str = "market",
    ) -> dict:
        """주문을 생성한다."""

    @abstractmethod
    def get_order_status(self, order_id: str) -> dict:
        """주문 상태를 조회한다."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> dict:
        """주문 취소를 요청한다."""
