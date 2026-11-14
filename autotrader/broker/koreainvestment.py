"""한국투자증권 Open API 브로커 구현 골격.

주의:
- 본 구현은 공식 문서 기반으로 확정 가능한 범위까지만 구조화했다.
- 거래 ID(tr_id), 엔드포인트 상세 경로, 요청/응답 필드는 계좌유형/상품/환경에 따라 달라질 수 있다.
- 반드시 한국투자증권 공식 문서 최신값을 확인한 뒤 운영에 사용해야 한다.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import requests

from broker.base import Broker


class LiveTradingDisabledError(RuntimeError):
    """실거래 비활성화 상태에서 주문 시도 시 발생."""


@dataclass
class TokenInfo:
    """액세스 토큰 정보."""

    access_token: str
    token_type: str = "Bearer"


class KoreaInvestmentBroker(Broker):
    """한국투자증권 Open API 브로커."""

    def __init__(
        self,
        app_key: str,
        app_secret: str,
        account_no: str,
        product_code: str,
        base_url: str,
        enable_live_trading: bool,
        is_paper_trading: bool,
    ) -> None:
        self.app_key = app_key
        self.app_secret = app_secret
        self.account_no = account_no
        self.product_code = product_code
        self.base_url = base_url.rstrip("/")
        self.enable_live_trading = enable_live_trading
        self.is_paper_trading = is_paper_trading

        self.session = requests.Session()
        self.session.headers.update({"content-type": "application/json; charset=utf-8"})
        self.token: TokenInfo | None = None

    def authenticate(self) -> None:
        """액세스 토큰 발급.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 정확한 토큰 발급 endpoint path
        - 요청 body 필드명 및 scope
        - 응답 필드(access_token 외) 세부
        """
        endpoint = "/oauth2/tokenP"  # TODO: 한국투자증권 공식 API 문서 확인 필요
        payload = {
            "grant_type": "client_credentials",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
        }
        response = self._request("POST", endpoint, json=payload, include_auth=False)
        access_token = response.get("access_token")
        if not access_token:
            raise RuntimeError("인증 실패: access_token이 응답에 없습니다.")
        self.token = TokenInfo(access_token=access_token)

    def get_price(self, symbol: str) -> dict:
        """현재가 조회.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 시세 조회 endpoint
        - tr_id 값
        - params 항목 (시장구분/종목코드 필드)
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-price"  # TODO 확인
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # TODO 확인
            "FID_INPUT_ISCD": symbol,
        }
        headers = self._build_headers(tr_id="TODO_TR_ID_PRICE")
        data = self._request("GET", endpoint, headers=headers, params=params)
        output = data.get("output", {})
        return {
            "symbol": symbol,
            "price": int(output.get("stck_prpr", 0)),  # TODO 필드명 확인
            "raw": data,
        }

    def get_ohlcv(self, symbol: str, limit: int = 100) -> list[dict]:
        """OHLCV 조회.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 일봉/분봉 endpoint
        - tr_id
        - 응답 output 리스트 필드
        """
        endpoint = "/uapi/domestic-stock/v1/quotations/inquire-daily-price"  # TODO 확인
        params = {
            "FID_COND_MRKT_DIV_CODE": "J",  # TODO 확인
            "FID_INPUT_ISCD": symbol,
        }
        headers = self._build_headers(tr_id="TODO_TR_ID_OHLCV")
        data = self._request("GET", endpoint, headers=headers, params=params)
        raw_rows = data.get("output", [])
        candles: list[dict] = []
        for row in raw_rows[:limit]:
            candles.append(
                {
                    "date": row.get("stck_bsop_date"),  # TODO 필드 확인
                    "open": int(row.get("stck_oprc", 0)),
                    "high": int(row.get("stck_hgpr", 0)),
                    "low": int(row.get("stck_lwpr", 0)),
                    "close": int(row.get("stck_clpr", 0)),
                    "volume": int(row.get("acml_vol", 0)),
                }
            )
        return list(reversed(candles))

    def get_balance(self) -> dict:
        """잔고 조회.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 잔고 조회 endpoint/tr_id
        - output 필드 매핑
        """
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-balance"  # TODO 확인
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
        }
        headers = self._build_headers(tr_id="TODO_TR_ID_BALANCE")
        data = self._request("GET", endpoint, headers=headers, params=params)
        return {"raw": data}

    def get_positions(self) -> list[dict]:
        """보유 포지션 조회.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 잔고/보유종목 응답 배열 위치 확인
        """
        balance = self.get_balance()
        raw = balance.get("raw", {})
        rows = raw.get("output1", [])  # TODO 필드 확인
        positions: list[dict] = []
        for row in rows:
            positions.append(
                {
                    "symbol": row.get("pdno"),
                    "qty": int(row.get("hldg_qty", 0)),
                    "avg_price": int(row.get("pchs_avg_pric", 0)),
                    "current_price": int(row.get("prpr", 0)),
                }
            )
        return positions

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: int,
        price: int | None = None,
        order_type: str = "market",
    ) -> dict:
        """주문 실행.

        안전장치:
        - enable_live_trading=False 이면 예외 발생
        """
        if not self.enable_live_trading:
            raise LiveTradingDisabledError(
                "실거래가 비활성화되어 주문이 차단되었습니다. ENABLE_LIVE_TRADING=true 설정 필요"
            )

        if side not in {"buy", "sell"}:
            raise ValueError("side는 buy 또는 sell 이어야 합니다.")
        if qty <= 0:
            raise ValueError("qty는 1 이상이어야 합니다.")
        if order_type not in {"market", "limit"}:
            raise ValueError("order_type은 market 또는 limit 이어야 합니다.")
        if order_type == "limit" and (price is None or price <= 0):
            raise ValueError("지정가 주문 시 유효한 price가 필요합니다.")

        endpoint = "/uapi/domestic-stock/v1/trading/order-cash"  # TODO 확인

        # TODO: 한국투자증권 공식 API 문서 확인 필요
        # - 매수/매도별 tr_id
        # - 시장가/지정가 구분 코드(ORD_DVSN)
        # - 계좌번호 분리 규칙(CANO/ACNT_PRDT_CD)
        tr_id = "TODO_TR_ID_ORDER_BUY" if side == "buy" else "TODO_TR_ID_ORDER_SELL"
        ord_dvsn = "01" if order_type == "market" else "00"  # TODO 코드값 확인

        payload = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "PDNO": symbol,
            "ORD_DVSN": ord_dvsn,
            "ORD_QTY": str(qty),
            "ORD_UNPR": str(price or 0),
        }
        headers = self._build_headers(tr_id=tr_id)
        data = self._request("POST", endpoint, headers=headers, json=payload)
        return {"raw": data}

    def get_order_status(self, order_id: str) -> dict:
        """주문 상태 조회.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 주문조회 endpoint/tr_id
        - 조회 키(원주문번호/주문일자 등)
        """
        endpoint = "/uapi/domestic-stock/v1/trading/inquire-daily-ccld"  # TODO 확인
        params = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "ODNO": order_id,
        }
        headers = self._build_headers(tr_id="TODO_TR_ID_ORDER_STATUS")
        data = self._request("GET", endpoint, headers=headers, params=params)
        return {"raw": data}

    def cancel_order(self, order_id: str) -> dict:
        """주문 취소.

        TODO: 한국투자증권 공식 API 문서 확인 필요
        - 정정/취소 endpoint/tr_id
        - 필수 주문원본정보 필드
        """
        if not self.enable_live_trading:
            raise LiveTradingDisabledError(
                "실거래가 비활성화되어 주문취소 요청이 차단되었습니다. ENABLE_LIVE_TRADING=true 설정 필요"
            )

        endpoint = "/uapi/domestic-stock/v1/trading/order-rvsecncl"  # TODO 확인
        payload = {
            "CANO": self.account_no,
            "ACNT_PRDT_CD": self.product_code,
            "ORGN_ODNO": order_id,
        }
        headers = self._build_headers(tr_id="TODO_TR_ID_CANCEL")
        data = self._request("POST", endpoint, headers=headers, json=payload)
        return {"raw": data}

    def _build_headers(self, tr_id: str) -> dict[str, str]:
        """요청 공통 헤더 생성."""
        self._ensure_token()
        assert self.token is not None
        return {
            "authorization": f"{self.token.token_type} {self.token.access_token}",
            "appkey": self.app_key,
            "appsecret": self.app_secret,
            "tr_id": tr_id,
            "custtype": "P",
        }

    def _ensure_token(self) -> None:
        """토큰 없으면 인증 수행."""
        if self.token is None:
            self.authenticate()

    def _request(
        self,
        method: str,
        endpoint: str,
        headers: dict[str, str] | None = None,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        include_auth: bool = True,
    ) -> dict:
        """공통 HTTP 요청/응답 검증."""
        url = f"{self.base_url}{endpoint}"

        req_headers: dict[str, str] = {}
        if headers:
            req_headers.update(headers)
        elif include_auth:
            # tr_id가 필요한 API는 호출부에서 명시해야 한다.
            # TODO: 한국투자증권 공식 API 문서 확인 필요
            self._ensure_token()
            assert self.token is not None
            req_headers.update(
                {
                    "authorization": f"{self.token.token_type} {self.token.access_token}",
                    "appkey": self.app_key,
                    "appsecret": self.app_secret,
                }
            )

        resp = self.session.request(method=method, url=url, headers=req_headers, params=params, json=json, timeout=15)
        if resp.status_code >= 400:
            raise RuntimeError(f"KIS API 요청 실패: status={resp.status_code}, body={resp.text}")

        try:
            data = resp.json()
        except ValueError as exc:
            raise RuntimeError(f"KIS API 응답 JSON 파싱 실패: {resp.text}") from exc

        # TODO: 공식 문서 기준 응답 코드(rt_cd, msg_cd, msg1 등) 검사 강화 필요
        if isinstance(data, dict) and data.get("rt_cd") not in (None, "0"):
            raise RuntimeError(f"KIS API 비정상 응답: {data}")

        return data
