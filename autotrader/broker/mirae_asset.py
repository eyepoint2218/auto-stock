"""미래에셋증권 연동 스켈레톤.

주의: 본 파일은 실제 API 명세를 임의로 추측하지 않는다.
미확정 부분은 반드시 TODO 주석과 NotImplementedError로 남긴다.
"""

from __future__ import annotations

from dataclasses import dataclass

import requests

from .base import Broker


@dataclass
class MiraeAssetConfig:
    """미래에셋 브로커 설정값."""

    app_key: str
    app_secret: str
    account_no: str
    enable_live_trading: bool = False


class MiraeAssetBroker(Broker):
    """미래에셋증권 브로커 연동 스켈레톤."""

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        enable_live_trading: bool = False,
        session: requests.Session | None = None,
    ) -> None:
        self.config = MiraeAssetConfig(
            app_key=app_key,
            app_secret=app_secret,
            account_no=account_no,
            enable_live_trading=enable_live_trading,
        )
        self.session = session or requests.Session()
        self.access_token: str | None = None

    def authenticate(self) -> None:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 인증 endpoint, header, body 필드, 토큰 규칙 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - authenticate")

    def get_price(self, symbol: str) -> dict:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 현재가 조회 endpoint 및 파라미터 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - get_price")

    def get_ohlcv(self, symbol: str, limit: int = 100) -> list[dict]:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 시세/캔들 조회 endpoint, interval, limit 규칙 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - get_ohlcv")

    def get_balance(self) -> dict:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 잔고 조회 endpoint 및 응답 필드 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - get_balance")

    def get_positions(self) -> list[dict]:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 보유종목 조회 endpoint 및 응답 필드 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - get_positions")

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int | None = None,
        order_type: str = "market",
    ) -> dict:
        if not self.config.enable_live_trading:
            raise RuntimeError(
                "실거래가 비활성화되어 주문이 차단되었습니다. ENABLE_LIVE_TRADING=true 설정 시에만 주문 가능합니다."
            )

        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 주문 endpoint, 주문구분코드, 시장가/지정가 body 스키마 확인 필요
        # TODO: 주문 전송 시 필요한 인증 헤더/해시 규칙 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - place_order")

    def get_order_status(self, order_id: str) -> dict:
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 주문 조회 endpoint 및 order_id 매핑 규칙 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - get_order_status")

    def cancel_order(self, order_id: str) -> dict:
        if not self.config.enable_live_trading:
            raise RuntimeError(
                "실거래가 비활성화되어 주문 취소 API 호출이 차단되었습니다. ENABLE_LIVE_TRADING=true 필요"
            )
        # TODO: 미래에셋 공식 API 문서 확인 필요
        # TODO: 정정/취소 주문 endpoint 및 body 필드 확인 필요
        raise NotImplementedError("TODO: 미래에셋 공식 API 문서 확인 필요 - cancel_order")
